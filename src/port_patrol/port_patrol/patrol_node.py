"""Waypoint patrol node: visit A -> B -> C one goal at a time with Nav2."""

import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.parameter import Parameter


def make_pose(nav, x, y):
    """Build a goal pose in the map frame, facing yaw = 0."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0
    pose.pose.orientation.w = 1.0
    return pose


def go_to_waypoint(nav, name, x, y, timeout_sec):
    """Send one goal, wait for it, return 'SUCCEEDED', 'FAILED', 'CANCELED' or 'TIMEOUT'."""
    nav.get_logger().info(f'Going to {name} ({x:.2f}, {y:.2f})')
    nav.goToPose(make_pose(nav, x, y))

    start = time.monotonic()
    last_print = 0.0
    while not nav.isTaskComplete():
        elapsed = time.monotonic() - start

        if elapsed > timeout_sec:
            nav.get_logger().warn(f'{name}: no result after {timeout_sec:.0f} s, canceling')
            nav.cancelTask()
            return 'TIMEOUT'

        feedback = nav.getFeedback()
        if feedback is not None and elapsed - last_print > 2.0:
            nav.get_logger().info(
                f'{name}: {feedback.distance_remaining:.2f} m remaining')
            last_print = elapsed

    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        return 'SUCCEEDED'
    if result == TaskResult.CANCELED:
        return 'CANCELED'
    return 'FAILED'


def main():
    rclpy.init()
    nav = BasicNavigator(node_name='patrol_node')

    # Waypoints come from config/waypoint.yaml (passed with --params-file).
    nav.declare_parameter('waypoint_names', Parameter.Type.STRING_ARRAY)
    nav.declare_parameter('waypoints_x', Parameter.Type.DOUBLE_ARRAY)
    nav.declare_parameter('waypoints_y', Parameter.Type.DOUBLE_ARRAY)
    nav.declare_parameter('goal_timeout_sec', 120.0)

    try:
        names = list(nav.get_parameter('waypoint_names').value)
        xs = list(nav.get_parameter('waypoints_x').value)
        ys = list(nav.get_parameter('waypoints_y').value)
    except Exception:
        nav.get_logger().error('Waypoints not set. Run with --params-file waypoint.yaml')
        nav.destroy_node()
        rclpy.shutdown()
        return
    timeout_sec = nav.get_parameter('goal_timeout_sec').value

    if not (len(names) == len(xs) == len(ys)):
        nav.get_logger().error('waypoint_names, waypoints_x and waypoints_y differ in length')
        nav.destroy_node()
        rclpy.shutdown()
        return

    results = []
    patrol_start = time.monotonic()
    try:
        for name, x, y in zip(names, xs, ys):
            outcome = go_to_waypoint(nav, name, x, y, timeout_sec)
            results.append((name, outcome))
            if outcome == 'SUCCEEDED':
                nav.get_logger().info(f'{name}: reached')
            else:
                nav.get_logger().warn(f'{name}: {outcome}, skipping to next waypoint')
    except KeyboardInterrupt:
        # Ctrl+C: stop the robot instead of leaving the goal running.
        nav.cancelTask()

    total = time.monotonic() - patrol_start
    reached = sum(1 for _, outcome in results if outcome == 'SUCCEEDED')
    nav.get_logger().info('===== Patrol summary =====')
    for name, outcome in results:
        nav.get_logger().info(f'  {name}: {outcome}')
    nav.get_logger().info(
        f'  Reached {reached}/{len(names)}, failed or skipped {len(results) - reached}, '
        f'time {total:.1f} s')

    nav.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
