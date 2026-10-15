# PROGRESS

Fast-track plan (see CLAUDE.md). Patrol node: written by me with hints (option a).

## Done
- [x] Environment verified: WSL2, Ubuntu 24.04.5, x86_64, VS Code connected to WSL
- [x] ROS 2 Jazzy installed (ros-jazzy-desktop + ros-dev-tools), sourced in ~/.bashrc
- [x] talker/listener demo running
- [x] Solved: forgot WSL sudo password, reset via `wsl -d Ubuntu-24.04 -u root passwd zhang`
- [x] .gitignore, PLAN.md, PROGRESS.md, LEARNING_LOG.md created

## Steps
- [ ] 0. First Git commit and push (own message)
- [x] 1. Installed TurtleBot3 sim, Gazebo Harmonic, SLAM Toolbox, Nav2 (apt)
- [x] 1. Launched turtlebot3_world in Gazebo; GPU via GALLIUM_DRIVER=d3d12, ~75% real-time factor
- [ ] 2. Drive with teleop while SLAM builds a map; save map to ~/maps/my_map
- [ ] 3. Nav2 on saved map; send a goal from RViz
- [ ] 4. Patrol node (goToPose, one goal at a time, result handling, timeout, skip, summary)
- [ ] 5. Two test runs (clear / obstacle), README, demo GIF
- [ ] 6. OPTIONAL: container-yard world

## Notes
- Gazebo reset button (↻) removes the spawned robot. Restart the launch file instead.
- LEARNING_LOG: password problem entry written (Day 1, section 二)

- [x] Relaunched Gazebo after reset problem; burger visible, teleop drives the robot (2026-10-15)

## Next
- Step 0 commit + push, then step 2 (SLAM mapping)
