# PROGRESS

Fast-track plan (see CLAUDE.md). Patrol node: written by me with hints (option a).

## Done
- [x] Environment verified: WSL2, Ubuntu 24.04.5, x86_64, VS Code connected to WSL
- [x] ROS 2 Jazzy installed (ros-jazzy-desktop + ros-dev-tools), sourced in ~/.bashrc
- [x] talker/listener demo running
- [x] Solved: forgot WSL sudo password, reset via `wsl -d Ubuntu-24.04 -u root passwd zhang`
- [x] .gitignore, PLAN.md, PROGRESS.md, LEARNING_LOG.md created

## Steps
- [x] 0. First Git commit and push (9594df2, in sync with origin/main)
- [x] 1. Installed TurtleBot3 sim, Gazebo Harmonic, SLAM Toolbox, Nav2 (apt)
- [x] 1. Launched turtlebot3_world in Gazebo; GPU via GALLIUM_DRIVER=d3d12, ~75% real-time factor
- [x] 2. SLAM map built and saved to ~/maps/my_map (.pgm + .yaml), 2026-10-17
  (first try failed: robot hit a pillar, wheel slip broke the map; second run driven by Claude with slow scripted /cmd_vel commands because teleop was hard to control)
- [x] 3. Nav2 running on saved map, localized (2026-10-17). Launch with
  params_file:=config/nav2_burger.yaml (scan.source_timeout 0.2 -> 2.0: slow Gazebo made
  collision_monitor treat every scan as stale and block all motion)
- [x] 4. Nav2 Goal from RViz reached (2026-10-17, short goal ~0.5 m)
- [ ] 5. OPTIONAL: patrol node (goToPose, one goal at a time, result handling, timeout, skip, summary)
- [ ] 6. OPTIONAL: container-yard world
- [ ] 7. MUST: final test (clear path / obstacle)
- [ ] 8. README, demo GIF

## Notes
- Gazebo reset button (↻) removes the spawned robot. Restart the launch file instead.
- LEARNING_LOG: password problem entry written (Day 1, section 二)

- [x] Relaunched Gazebo after reset problem; burger visible, teleop drives the robot (2026-10-15)

## Next
- Try one long goal across the arena; commit; then decide on optional step 5 (patrol node) vs step 7 (final test)
