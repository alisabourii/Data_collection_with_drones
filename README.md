## Raspberry Pi5(Ubuntu Server) Remote Bağlanmak:
Raspberry Pi5 Terminalinda:(Server)

	sudo nano /etc/ssh/sshd_config.d/50-cloud-init.conf
	açılan dosyada : "PasswordAuthentication no" yerine "PasswordAuthentication yes" yazacağız.
	 sudo systemctl restart ssh
	 
Client bilgisayarda:
	
	ssh ubuntu@192.168.x.xx(x.xx-> serverde=> hostname -I)



## Kurulum rehberi:

1.Sistem hazırlığı

Sistem paketlerini güncelle

	sudo apt update && sudo apt upgrade -y

	# Locale ayarlarını yap
	sudo apt install -y locales
	sudo locale-gen en_US en_US.UTF-8
	sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
	export LANG=en_US.UTF-8

	# Universe deposunu ekle ve temel araçları yükle
	sudo apt install -y software-properties-common curl gnupg lsb-release
	sudo add-apt-repository universe -y

2.ROS2 GPG Anahtarını Depoyu ekleme:

	sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
	
3.ROS2 Jazzy Kurulumu:

	sudo apt update
	sudo apt install -y ros-jazzy-desktop

4.Geliştirme Araçları ve Bağımlılık Yöneticileri:

	sudo apt install -y \
	  python3-colcon-common-extensions \
	  python3-rosdep \
	  python3-pip \
	  ros-jazzy-cv-bridge \
	  ros-jazzy-image-transport

	# rosdep veritabanını başlat
	sudo rosdep init
	rosdep update
5.Ortam Değişkenlerini Tanımlama:

	echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
	source ~/.bashrc

6.Intel RealSense SDK ve ROS 2 Wrapper Kurulumu:

	sudo apt install -y \
	  ros-jazzy-librealsense2* \
	  ros-jazzy-realsense2-camera \
	  ros-jazzy-realsense2-description
    
7. Adım: USB Yetkilerini tanımlama:
   
   		sudo curl -sSL https://raw.githubusercontent.com/IntelRealSense/librealsense/master/config/99-realsense-libusb.rules -o /etc/udev/rules.d/99-realsense-libusb.rules
        sudo udevadm control --reload-rules && sudo udevadm trigger


## Test Başlatması için: 

kameranın hazırolması için:(Serverde çalışacak)
		
	ros2 launch realsense2_camera rs_launch.py

butonun tetikte beklemesi için:(Serverde çalışacak)

	source ~/ros2_ws/install/setup.bash
	ros2 run camera_capture button_bag_recorder
			
Belirli bir kaydın getirlilmesi için :

	scp -r ubuntu@192.168.1.197:~/realsense_bag_20260728_154950 ~/Masaüstü/

.Bag kayıtlarımızı indirmek için:

	scp -r ubuntu@192.168.1.197:~/realsense_bag_* ~/Masaüstü/

.Bag kayıtlarımıza silmek için(Server):

	rm -rf ~/realsense_bag_*

## PUSHUP buton Bağlantısı

Dosya: nano ~/ros2_ws/src/camera_capture/camera_capture/button_bag_recorder.py

#### Katot(-) -> GND

#### Anot(+)  -> GPIO18

## GPS Entegrasyonu:

## 🛠️ Donanım Bağlantıları

### GPS Modülü Bağlantı Şeması

U-blox NEO-M8N modülünün dahili LDO voltaj regülatöründen dolayı kararlı çalışması için 5V besleme kullanılmıştır.

| NEO-M8N Pin | Raspberry Pi 5 Fiziksel Pin | Açıklama |
| :--- | :--- | :--- |
| VCC | Pin 2 / Pin 4 | 5V Güç Beslemesi |
| GND | Pin 6 (veya herhangi bir GND) | Toprak |
| TX | Pin 10 (GPIO 15 / RXD0) | Pi RX (Alıcı) |
| RX | Pin 8 (GPIO 14 / TXD0) | Pi TX (Verici) |

---

## ⚙️ Sistem & Çekirdek (Kernel) Yapılandırması

Raspberry Pi 5'in yeni RP1 I/O entegresinde UART DMA kilitlenmelerini (dmachan2 is non-idle!) ve kernel terminal çakışmalarını önlemek için yapılan ayarlar:

1. /boot/firmware/config.txt içine eklenecek satırlar:

		enable_uart=1
		dtoverlay=uart0-pi5,dma=off

2. /boot/firmware/cmdline.txt düzenlemesi:

   		console=ttyAMA0,115200
   ifadesini dosyadan silin ve satır sonına şu parametreyi ekleyin:

   		8250.nr_uarts=1

(Önemli: /boot/firmware/cmdline.txt dosyası tek bir uzun satırdan oluşmalıdır. Değişikliklerin uygulanması için cihazı yeniden başlatın: sudo reboot)

---

## 📦 Kurulum ve Bağımlılıklar

ROS 2 Jazzy için gerekli NMEA GPS sürücüsünü yükleyin ve seri porta kullanıcı erişim izinlerini tanımlayın:

	sudo apt update
	sudo apt install ros-jazzy-nmea-navsat-driver python3-serial

	sudo usermod -aG dialout,tty ubuntu
	sudo chmod 666 /dev/ttyAMA0

---

## 🧪 Donanım Doğrulama Komutları

ROS 2 düğümlerini başlatmadan önce ham NMEA verilerinin aktığını doğrulamak için:

	sudo stty -F /dev/ttyAMA0 9600 raw -echo
	sudo cat /dev/ttyAMA0

(Beklenen Çıktı: Akıcı $GNRMC..., $GNGGA... NMEA cümleçikleri.)

---

## 🚀 ROS 2 Launch Dosyası

Ana launch dosyası (auto_record.launch.py), kamera, GPS ve buton kayıt düğümlerini eşzamanlı başlatır:

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

---

## 🔄 Derleme ve Servis Yönetimi

ROS 2 çalışma alanını derleyin ve arka plan servisini yönetin:

	cd ~/ros2_ws
	colcon build --symlink-install

	sudo systemctl restart realsense_recorder.service
	sudo systemctl status realsense_recorder.service
	
	sudo journalctl -u realsense_recorder.service -n 50 --no-pager

---

## 📡 Çalışma Kontrolü ve Başlıklar (Topics)

Sistem aktifken yayınlanan başlıkları kontrol etmek için:
	
	source /opt/ros/jazzy/setup.bash
	source ~/ros2_ws/install/setup.bash

	ros2 topic list
	ros2 topic echo /fix

Kaydedilen Başlıklar:
* /camera/camera/color/image_raw
* /camera/camera/depth/image_rect_raw
* /camera/camera/color/camera_info
* /camera/camera/depth/camera_info
* /fix (GPS Konum Bilgisi)

---
