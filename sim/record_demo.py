"""Record the overhead demo camera, then turn the frames into a GIF.

Step 1, record: saves every frame from /demo_camera/image (bridged from
Gazebo) as a JPEG in <frames_dir> as soon as it arrives. Stop with Ctrl+C;
nothing is lost because frames are already on disk.
  python3 record_demo.py record <frames_dir>

Step 2, make the GIF from the saved frames:
  python3 record_demo.py gif <frames_dir> <output.gif> [speedup vs real time]
"""
import glob
import math
import os
import sys

from PIL import Image as PILImage
from PIL import ImageDraw
from PIL import ImageFont
import yaml

SOURCE_HZ = 5      # <update_rate> in demo_camera.sdf (for progress logging only)
OUT_SIZE = 480     # GIF width and height in pixels
BANNER_H = 72      # white strip above the camera image for the title

# Camera geometry, must match demo_camera.sdf: straight down from (0, 0, 4.6).
CAM_HEIGHT = 4.6
CAM_HFOV = 1.047
# Gazebo position = map position + robot spawn point (the map origin).
SPAWN_IN_GAZEBO = (-2.0, -0.5)
# Nav2 counts a goal as reached within this distance (xy_goal_tolerance in
# config/nav2_burger.yaml), so each ring is drawn with this radius.
GOAL_TOLERANCE_M = 0.25
WAYPOINTS_YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src',
                              'port_patrol', 'config', 'waypoint.yaml')
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
PX_PER_M = (OUT_SIZE / 2) / (CAM_HEIGHT * math.tan(CAM_HFOV / 2))   # at floor level


def map_to_pixel(x_map, y_map):
    """Where a point on the floor (map frame) appears in the GIF image.

    The camera looks straight down with image-up = Gazebo +x and
    image-left = Gazebo +y.
    """
    xg = x_map + SPAWN_IN_GAZEBO[0]
    yg = y_map + SPAWN_IN_GAZEBO[1]
    return OUT_SIZE / 2 - yg * PX_PER_M, OUT_SIZE / 2 - xg * PX_PER_M


def load_waypoints():
    with open(WAYPOINTS_YAML) as f:
        p = yaml.safe_load(f)['patrol_node']['ros__parameters']
    return list(zip(p['waypoint_names'], p['waypoints_x'], p['waypoints_y']))


def make_overlay(speedup):
    """Draw the title banner and the waypoint markers once, on a transparent layer."""
    big = ImageFont.truetype(FONT_BOLD, 18)
    small = ImageFont.truetype(FONT, 12)
    marker = ImageFont.truetype(FONT_BOLD, 15)
    layer = PILImage.new('RGBA', (OUT_SIZE, OUT_SIZE + BANNER_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, 0, OUT_SIZE, BANNER_H], fill=(255, 255, 255, 255))
    d.text((10, 6), 'Autonomous waypoint patrol (ROS 2 Nav2)', font=big, fill=(20, 20, 20, 255))
    d.text((10, 32), f'Goals A, B, C sent one at a time  |  x{speedup:g} real time',
           font=small, fill=(80, 80, 80, 255))
    d.text((10, 50), 'Rings: goal reached within 0.25 m  |  orange box: obstacle not in the map',
           font=small, fill=(80, 80, 80, 255))
    for name, x, y in load_waypoints():
        u, v = map_to_pixel(x, y)
        v += BANNER_H
        # Hollow ring = the area where Nav2 counts the goal as reached, so the
        # robot stays visible when it arrives. Letter in a badge beside it.
        r = GOAL_TOLERANCE_M * PX_PER_M
        d.ellipse([u - r, v - r, u + r, v + r], outline=(200, 30, 30, 255), width=2)
        bu, bv, br = u + r * 0.8 + 8, v - r * 0.8 - 8, 10
        d.ellipse([bu - br, bv - br, bu + br, bv + br], fill=(200, 30, 30, 255),
                  outline=(255, 255, 255, 255), width=2)
        d.text((bu, bv), name, font=marker, fill=(255, 255, 255, 255), anchor='mm')
    return layer


def record(frames_dir):
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from sensor_msgs.msg import Image

    os.makedirs(frames_dir, exist_ok=True)

    class Recorder(Node):
        def __init__(self):
            super().__init__('demo_recorder')
            self.count = 0
            self.create_subscription(Image, '/demo_camera/image', self.on_image, 10)

        def on_image(self, msg):
            img = PILImage.frombytes('RGB', (msg.width, msg.height), bytes(msg.data))
            img.save(os.path.join(frames_dir, f'{self.count:05d}.jpg'), quality=90)
            self.count += 1
            if self.count % (SOURCE_HZ * 10) == 0:
                self.get_logger().info(f'{self.count // SOURCE_HZ} s recorded')

    rclpy.init()
    node = Recorder()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    print(f'{node.count} frames saved in {frames_dir}')
    node.destroy_node()
    rclpy.try_shutdown()


def make_gif(frames_dir, out, speedup):
    paths = sorted(glob.glob(os.path.join(frames_dir, '*.jpg')))
    if not paths:
        print(f'No frames in {frames_dir}')
        return
    # Gazebo renders slower than SOURCE_HZ when the machine is busy, so take
    # the real recording time from the file timestamps, not the frame count.
    real_sec = os.path.getmtime(paths[-1]) - os.path.getmtime(paths[0])
    duration_ms = max(20, int(real_sec * 1000 / len(paths) / speedup))
    overlay = make_overlay(speedup)
    frames = []
    for p in paths:
        f = PILImage.new('RGBA', overlay.size, (255, 255, 255, 255))
        f.paste(PILImage.open(p).convert('RGB').resize((OUT_SIZE, OUT_SIZE)), (0, BANNER_H))
        f.alpha_composite(overlay)
        frames.append(f.convert('RGB').quantize(colors=64))
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=duration_ms, loop=0, optimize=True)
    print(f'Saved {len(frames)} frames to {out}')


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == 'record':
        record(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == 'gif':
        speedup = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
        make_gif(sys.argv[2], sys.argv[3], speedup)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
