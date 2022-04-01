## Spojazdnenie sondy
### Skúšané na:
- OS: 2021-05-07-raspios-buster-arm
- Python: 3.7.3
### Úprava užívateľa
- Vytvorenie skupiny __sonda__
```bash
sudo addgroup sonda
```
- Pridanie užívateľa do skupiny
```bash
sudo usermod -a -G sonda <uzivatel>
reboot
```
### Inštalácia balíkov
- Update a upgrade 
```bash
sudo apt-get -y update
sudo apt-get -y upgrade
```
- Potrebné balíky
```bash
sudo apt-get -y install wget build-essential cmake pkg-config python3-dev python3-pip libjpeg-dev libtiff5-dev libjasper-dev libpng-dev libhdf5-dev libhdf5-serial-dev libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5 libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran protobuf-compiler libprotoc-dev libilmbase-dev libopenexr-dev libgstreamer1.0-dev libpcap0.8 libopenblas-dev redis-server tcpdump git
```
- Virtuálne prostredie pre python
```bash
sudo pip3 install virtualenvwrapper
echo 'export WORKON_HOME=$HOME/.virtualenvs' >> ~/.profile
echo 'export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3' >> ~/.profile
echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.profile
```
- Inštalácia cicflometer __!ako root v zložke cicflowmeter!__
```bash
cd ./ciflowmeter
sudo pip3 install -r requirements.txt
sudo python3 setup.py install
```
- Inštalácia OPENVINO Toolkit
```bash
wget https://download.01.org/opencv/2021/openvinotoolkit/2021.2/l_openvino_toolkit_runtime_raspbian_p_2021.2.185.tgz
sudo mkdir -p /opt/intel/openvino
sudo tar -xf l_openvino_toolkit_runtime_raspbian_p_2021.2.185.tgz --strip 1 -C /opt/intel/openvino
rm -f l_openvino_toolkit_runtime_raspbian_p_2021.2.185.tgz
source /opt/intel/openvino/bin/setupvars.sh
echo 'source /opt/intel/openvino/bin/setupvars.sh' >> ~/.profile
sudo usermod -a -G users "$(whoami)"
sh /opt/intel/openvino/install_dependencies/install_NCS_udev_rules.sh
```
- Inštalácia sondy
```bash
mkvirtualenv app
workon app
pip3 install -r ./sonda/requirements.txt
deactivate app
```
- Spustenie __v zložke sonda!__
```bash
sudo ifconfig eth0 promisc
sudo cicflowmeter -i eth0 -c flows.csv &
workon app
export FLASK_APP=app.py
flask run --port=5001
```
- Zálohovanie: SSH overovanie pomocou certifikátov medzi serverom
```bash
ssh-keygen -b 2048 -t rsa
ssh-copy-id -i <cesta_k_suboru_.pub> <uzivatel>@<adresa_servera>
```
- Zálohovanie: šifrovaná výmena súborov
```bash 
rsync -ae ssh ./sonda/checked/ <uzivatel>@<adresa_servera>:~/backup/
```
- Kontrola priestoru na disku
	- 1. parameter: cesta k kontrolovanej zložke
	- 2. parameter: nutné percentuálne obsadenie disku pre začatie čistenie
	- 3. parameter: počet odstránených súborov v cykle ak je prekročené obsadenie disku  
```bash
chmod 744 ./sonda/spaceRelease.sh
./sonda/spaceRelease.sh ./sonda/checked/ 60 10
```