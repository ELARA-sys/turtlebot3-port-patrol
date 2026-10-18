"""Record the overhead demo camera, then turn the frames into a GIF.

Step 1, record: saves every frame from /demo_camera/image (bridged from
Gazebo) as a JPEG in <frames_dir> as soon as it arrives. Stop with Ctrl+C;
nothing is lost because frames are already on disk.
  python3 record_demo.py record <frames_dir>

Step 2, make the GIF from the saved frames:
  python3 record_demo.py gif <frames_dir> <output.gif> [speedup vs real time]
"""
import glob
import os
import sys

from PIL import Image as PILImage
from PIL import ImageDraw

SOURCE_HZ = 5      # <update_rate> in demo_camera.sdf (for progress logging only)
OUT_SIZE = 480     # GIF width and height in pixels


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
    label = f'x{speedup:g} real time'
    frames = []
    for p in paths:
        f = PILImage.open(p).convert('RGB').resize((OUT_SIZE, OUT_SIZE))
        ImageDraw.Draw(f).text((10, 10), label, fill=(0, 0, 0))
        frames.append(f.quantize(colors=64))
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
