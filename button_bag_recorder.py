import rclpy
from rclpy.node import Node
import subprocess
import signal
import os
from datetime import datetime
from gpiozero import Button

class ButtonBagRecorderNode(Node):
    def __init__(self):
        super().__init__('button_bag_recorder_node')
        self.process = None

        # GPIO18 pinine bağlı buton (Dahili Pull-Up aktif)
        # bounce_time=0.2 mekanik buton sıçramalarını önler
        self.button = Button(18, pull_up=True, bounce_time=0.2)

        # Butona basıldığında toggle_recording metodunu çağır
        self.button.when_pressed = self.toggle_recording

        self.get_logger().info("GPIO18 Butonlu ROS2 Bag Recorder Hazır. Butona basılmayı bekliyor...")

    def toggle_recording(self):
        if self.process is None:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        # Zaman damgalı klasör ismi
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bag_name = f"realsense_bag_{timestamp}"

        # Kaydedilecek RealSense veri başlıkları
        topics = [
            '/camera/camera/color/image_raw',
            '/camera/camera/depth/image_rect_raw',
            '/camera/camera/color/camera_info',
            '/camera/camera/depth/camera_info'
        ]

        cmd = ['ros2', 'bag', 'record', '-o', bag_name] + topics
        home_dir = os.path.expanduser('~')

        self.process = subprocess.Popen(cmd, cwd=home_dir)
        self.get_logger().info(f"🟢 BUTON TETİKLENDİ: Kayıt BAŞLADI -> ~/{bag_name}")

    def stop_recording(self):      
        if self.process is not None:
            self.process.send_signal(signal.SIGINT)
            self.process.wait()
            self.process = None
            self.get_logger().info("🔴 BUTON TETİKLENDİ: Kayıt DURDURULDU ve .bag kapatıldı.")
    def main(args=None):
        rclpy.init(args=args)
        node = ButtonBagRecorderNode()

        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            if node.process is not None:
                node.stop_recording()
        finally:
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
