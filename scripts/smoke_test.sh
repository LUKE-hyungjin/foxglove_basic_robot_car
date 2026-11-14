#!/usr/bin/env bash
# Restart the simulation from scratch and rerun every check.
#   ./scripts/smoke_test.sh
# Stops a running `docker compose up` first. The full output is also saved to
# docs/_captures/smoke_<time>.txt.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p docs/_captures
capture="docs/_captures/smoke_$(date +%Y%m%d_%H%M%S).txt"
exec > >(tee "$capture") 2>&1

failures=0
in_sim() {  # run a command inside the simulation container, showing it first
  echo
  echo "\$ $1"
  docker compose exec -T sim bash -c "source /ws/install/setup.bash && $1" || failures=$((failures + 1))
}
reset_robot() {
  in_sim 'gz service -s /world/arena/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 --req "name: \"robot_car\", position: {x: 0, y: 0, z: 0.01}, orientation: {w: 1}"'
}

echo "\$ docker compose down && docker compose build --quiet && docker compose up -d"
docker compose down 2>/dev/null
docker compose build --quiet || exit 1
docker compose up -d 2>/dev/null || exit 1

echo
echo "waiting for the first /scan ..."
for _ in $(seq 60); do
  docker compose exec -T sim bash -c "source /ws/install/setup.bash && timeout 3 ros2 topic echo --once /scan --field header.frame_id" \
    >/dev/null 2>&1 && break
  sleep 2
done

in_sim "python3 -m pytest -q /ws/src/robot_car_sim/test"
in_sim "ros2 topic list"
in_sim "timeout 8 ros2 topic hz /scan | tail -2; true"
in_sim "timeout 5 ros2 topic hz /joint_states | tail -2; true"

reset_robot
in_sim "python3 /ws/scripts/check_sim.py scan"
reset_robot
in_sim "python3 /ws/scripts/check_sim.py drive 0.2 0.5 4"
reset_robot
in_sim "python3 /ws/scripts/check_sim.py drive 0.2 0 5"
reset_robot

echo
echo "\$ python3 scripts/check_bridge.py   # on the host, like Foxglove"
python3 scripts/check_bridge.py || failures=$((failures + 1))

echo
if [ "$failures" -eq 0 ]; then echo "SMOKE TEST PASSED"; else echo "SMOKE TEST FAILED ($failures failing steps)"; fi
echo "saved to $capture"
exit "$failures"
