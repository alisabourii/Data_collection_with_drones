# Data_collection_with_drones
Data collection with drones, use ıntel realense, ROS2 and raspberry pi5

### Raspberry Pi5(Ubuntu Server) Remote Bağlanmak:
Raspberry Pi5 Terminalinda:(Server)

	sudo nano /etc/ssh/sshd_config.d/50-cloud-init.conf
	açılan dosyada : "PasswordAuthentication no" bulup "PasswordAuthentication yes" şeklinde değiştireceğiz.
	 sudo systemctl restart ssh
	 
Client bilgisayarda:
	
	ssh ubuntu@192.168.x.xx(x.xx-> serverde=> hostname -I)



### Kurulum rehberi:

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


### Test Başlatması için: 

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

#### Katot(-) -> GND

#### Anot(+)  -> GPIO18
