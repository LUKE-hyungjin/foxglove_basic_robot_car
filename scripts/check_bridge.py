"""Connect to foxglove_bridge the way Foxglove does and list what it offers.

    python3 scripts/check_bridge.py [ws://localhost:8765]

Prints the server's capabilities and every advertised topic, then fetches the
arena mesh the way Foxglove's 3D panel does. Exits non-zero if a topic the
layout needs is missing. Standard library only: no pip install needed.
"""
import base64
import json
import os
import socket
import struct
import sys
import time
from urllib.parse import urlparse

NEEDED_TOPICS = [
    "/scan", "/odom", "/ground_truth/odom", "/joint_states", "/wheel_debug/expected",
    "/wheel_debug/error", "/tf", "/tf_static", "/map", "/robot_description",
]
# The map marker's mesh and one of the robot's Fusion meshes from /robot_description.
ASSET_URIS = [
    "package://robot_car_sim/models/arena/meshes/arena.stl",
    "package://robot_car_sim/meshes/base_link.stl",
]
# foxglove_bridge 3.x (built on the Foxglove SDK) only accepts foxglove.sdk.v1;
# older bridges only accept foxglove.websocket.v1. Offer both, like Foxglove does.
SUBPROTOCOLS = ["foxglove.sdk.v1", "foxglove.websocket.v1"]


def connect(url):
    parsed = urlparse(url)
    sock = socket.create_connection((parsed.hostname, parsed.port or 80), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    sock.sendall((
        f"GET / HTTP/1.1\r\nHost: {parsed.hostname}:{parsed.port}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
        f"Sec-WebSocket-Protocol: {', '.join(SUBPROTOCOLS)}\r\n\r\n"
    ).encode())
    response = b""
    while b"\r\n\r\n" not in response:
        response += sock.recv(1)
    if b" 101 " not in response.split(b"\r\n")[0]:
        sys.exit(f"websocket upgrade refused:\n{response.decode()}")
    headers = dict(
        line.split(": ", 1) for line in response.decode().lower().split("\r\n")[1:] if ": " in line
    )
    return sock, headers.get("sec-websocket-protocol")


def read_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("bridge closed the connection")
        data += chunk
    return data


def read_message(sock):
    """One websocket message: (is_text, payload). Joins fragmented frames."""
    payload, first_opcode = b"", None
    while True:
        b0, b1 = read_exact(sock, 2)
        opcode, length = b0 & 0x0F, b1 & 0x7F
        if length == 126:
            length = struct.unpack(">H", read_exact(sock, 2))[0]
        elif length == 127:
            length = struct.unpack(">Q", read_exact(sock, 8))[0]
        data = read_exact(sock, length)
        if opcode in (0x9, 0xA):  # ping / pong
            continue
        first_opcode = first_opcode or opcode
        payload += data
        if b0 & 0x80:
            return first_opcode == 0x1, payload


def send_text(sock, text):
    data, mask = text.encode(), os.urandom(4)
    header = bytes([0x81]) + (
        bytes([0x80 | len(data)]) if len(data) < 126 else bytes([0x80 | 126]) + struct.pack(">H", len(data))
    )
    sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def fetched(sock, uri):
    """Wait for the fetchAsset reply (binary opcode 4) and print what came back."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        is_text, payload = read_message(sock)
        if not is_text and payload[0] == 0x04:
            status = payload[5]
            error_length = struct.unpack_from("<I", payload, 6)[0]
            error = payload[10:10 + error_length].decode()
            size = len(payload) - 10 - error_length
            print(f"fetchAsset {uri}: " + (f"{size} bytes" if status == 0 else f"failed: {error}"))
            return status == 0
    print(f"fetchAsset {uri}: no reply")
    return False


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    sock, subprotocol = connect(url)
    print(f"connected to {url} (subprotocol {subprotocol})")

    # The bridge advertises everything right after connecting. It also streams the
    # sim clock nonstop, so listen for a fixed time instead of waiting for quiet.
    channels, server_info = {}, None
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        is_text, payload = read_message(sock)
        if not is_text:
            continue
        message = json.loads(payload)
        if message["op"] == "serverInfo":
            server_info = message
        elif message["op"] == "advertise":
            for channel in message["channels"]:
                channels[channel["topic"]] = channel["schemaName"]

    print(f"server: {server_info['name']}  capabilities: {', '.join(server_info['capabilities'])}")
    print(f"{len(channels)} advertised topics:")
    for topic in sorted(channels):
        print(f"  {topic:28} {channels[topic]}")

    assets_ok = "assets" in server_info["capabilities"]
    for request_id, uri in enumerate(ASSET_URIS if assets_ok else []):
        send_text(sock, json.dumps({"op": "fetchAsset", "uri": uri, "requestId": request_id}))
        assets_ok = assets_ok and fetched(sock, uri)
    sock.close()

    missing = [t for t in NEEDED_TOPICS if t not in channels]
    if missing:
        print(f"MISSING: {', '.join(missing)}")
    print("PASS" if not missing and assets_ok else "FAIL")
    sys.exit(0 if not missing and assets_ok else 1)


if __name__ == "__main__":
    main()
