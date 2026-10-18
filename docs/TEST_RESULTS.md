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

Repeat runs with the same box (2026-10-18, while recording the demo GIF):

| Run | Start point | Route | Result | Time |
|-----|-------------|-------|--------|------|
| 2   | spawn point | A -> B -> C | 3/3 SUCCEEDED | 119.6 s |
| 3   | C (left there by run 2) | C -> A -> B -> C | 3/3 SUCCEEDED | 213.4 s |

Run 3 is the one in `docs/demo.gif`. Only the summary lines of these runs
were kept, not the full logs.

## Test 3: waypoint B unreachable (2026-10-18)

Purpose: run the node's failure handling (timeout, skip, summary), which
Tests 1 and 2 never triggered.

Obstacle: the same box (`sim/obstacle_box.sdf`) placed directly on waypoint B:
map (1.23, 2.33), Gazebo (-0.77, 1.83). Goal timeout lowered to 60 s with
`-p goal_timeout_sec:=60.0`.

| Waypoint | Result    |
|----------|-----------|
| A        | SUCCEEDED |
| B        | TIMEOUT   |
| C        | SUCCEEDED |

Summary from the node: `Reached 2/3, failed or skipped 1, time 105.6 s`.

Key log lines:

```
[WARN] [patrol_node]: B: no result after 60 s, canceling
[INFO] [patrol_node]: Canceling current task.
[WARN] [patrol_node]: B: TIMEOUT, skipping to next waypoint
[INFO] [patrol_node]: Going to C (2.71, 2.41)
```

Evidence from the logs:
- On the way to B the remaining distance jumped from 1.99 m to 2.85 m and
  then varied, which fits Nav2 replanning once the box appeared in the costmap.
- It then stayed at 0.91 m for about 25 s (no progress), then dropped to
  0.29 m just before the timeout. The planner may plan to a point up to 0.5 m
  from the goal (`tolerance: 0.5`), but the robot cannot get within the
  0.25 m goal tolerance because the box sits on B.
- Nav2 did not return FAILED within 60 s, so the node's own timeout decided
  the outcome. Whether Nav2 would have given up later was not tested.

What I saw: the robot reached A, then drove towards B and kept trying until
it timed out, then skipped B and went straight to C and finished.

Outcome: **skipped**. The timeout canceled the goal, the node moved on to C,
and the summary reported 2/3.

## Limits of these tests

- Test 2 (box on the route) has three runs that all reached 3/3; Tests 1
  and 3 have one run each. That is still too few to say how repeatable they are.
- Only one obstacle size was tested, in two positions (on the route, and on a
  waypoint). Moving obstacles were not tested.
- The FAILED path (Nav2 itself giving up) was not seen; in Test 3 the node's
  timeout fired first.
- Simulation only, with Gazebo running at about 75 % real time.
