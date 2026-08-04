from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # 1. RealSense Kamera Düğümü
    realsense_launch_dir = get_package_share_directory('realsense2_camera')
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(realsense_launch_dir, 'launch', 'rs_launch.py')
        )
    )

    # 2. U-blox NEO-M8N GPS Düğümü (/dev/ttyAMA0)
    gps_node = Node(
        package='nmea_navsat_driver',
        executable='nmea_serial_driver',
        name='gps_node',
        parameters=[{
            'port': '/dev/ttyAMA0',
            'baud': 9600
        }],
        output='screen'
    )

    # 3. GPIO Buton Kayıt Düğümü
    button_recorder_node = Node(
        package='camera_capture',
        executable='button_bag_recorder',
        name='button_bag_recorder_node',
        output='screen'
    )

    return LaunchDescription([
        realsense_launch,
        gps_node,
        button_recorder_node
    ])