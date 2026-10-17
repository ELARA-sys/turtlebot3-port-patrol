# Test results (step 7)

Setup for both tests: Gazebo `turtlebot3_world`, TurtleBot3 burger, Nav2 on the
saved SLAM map (`~/maps/my_map.yaml`) with `config/nav2_burger.yaml`, AMCL
initial pose at the spawn point (map origin). Patrol node
`port_patrol/patrol_node.py` with waypoints from `src/port_patrol/config/waypoint.yaml`:

| Waypoint | x (map) | y (map) |
|----------|---------|---------|
| A        | 0.22    | 1.21    |
| B        | 1.23    | 2.33    |
| C        | 2.71    | 2.41    |

Goal timeout: 120 s (default `goal_timeout_sec`).

## Test 1: clear path (2026-10-17)

No extra obstacles.

| Waypoint | Result    |
|----------|-----------|
| A        | SUCCEEDED |
| B        | SUCCEEDED |
| C        | SUCCEEDED |

Summary from the node: `Reached 3/3, failed or skipped 0, time 128.7 s`.

Observation: the robot reached each point, then turned in place for
10-20 s to match the goal heading (yaw = 0) before Nav2 reported success.

## Test 2: obstacle on the route B -> C (2026-10-17)

Obstacle: static box 0.3 x 0.3 x 0.4 m (`sim/obstacle_box.sdf`), spawned
before the patrol started, at the midpoint of B -> C: map (1.97, 2.37),
Gazebo (-0.03, 1.87). The box is not in the saved map.

| Waypoint | Result    |
|----------|-----------|
| A        | SUCCEEDED |
| B        | SUCCEEDED |
| C        | SUCCEEDED |

Summary from the node: `Reached 3/3, failed or skipped 0, time 92.8 s`.
(Confirmed afterwards with `gz model --list` that `obstacle_box` was in the world.)

Recoveries (Navigation 2 panel in RViz): not checked

Evidence from the logs:
- At the start of B -> C, Nav2 reported 1.71 m remaining. In Test 1 the same
  leg started at 1.46 m. The straight-line distance B -> C is about 1.48 m.
  So the planned path was about 0.25 m longer, which fits a detour around the box.
- The remaining distance went down steadily on B -> C with no long stall
  until 0.16 m. That last stall was the turn in place to the goal heading,
  as in Test 1.
- The box appeared in the Nav2 costmap from live LiDAR data (visible in RViz
  between the pillar row and the wall). The box is not in the saved map.

What I saw: The robot slowed down near the box and drove around its left side.

Outcome: **rerouted**. The robot planned around the box and reached C
without the node skipping anything.

An earlier attempt with the box (same day, not logged) also got past it:
`/amcl_pose` afterwards was (2.49, 2.47), about 0.23 m from C.

## Limits of these tests

- Each test has one logged run (plus one unlogged obstacle run), so there is
  no real data on how repeatable they are.
- Only one obstacle size and position was tested. A route that is completely
  blocked (where the skip and timeout logic would run) was not tested.
- Simulation only, with Gazebo running at about 75 % real time.
