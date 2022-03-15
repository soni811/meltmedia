#!/bin/bash

sudo apt-get update --fix-missing -y
sudo apt-get upgrade -y
sudo apt-get install -y xubuntu-desktop git build-essential python3-pip python3-dev python3-setuptools libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk python3-numpy

INSTALL_CODE="$?"

# make the vagrant user auto login
cat <<EOF | sudo tee /etc/lightdm/lightdm.conf.d/20-vagrant-login.conf > /dev/null
[SeatDefaults]
autologin-user=vagrant
autologin-user-timeout=0
EOF

sudo cp /vagrant/bin/hippo-run.sh /usr/local/bin/hippo-run.sh
sudo chmod +x /usr/local/bin/hippo-run.sh

sudo cp /vagrant/bin/xprofile /home/vagrant/.xprofile
sudo chown vagrant.vagrant /home/vagrant/.xprofile

# make sure the python requirements are met
sudo /usr/bin/pip install -r /vagrant/requirements.txt

# download and unpack Firefox 4.6.01
mkdir -p /home/vagrant/firefox/97.0 && cd /home/vagrant/firefox/97.0 && curl -sL "https://ftp.mozilla.org/pub/firefox/releases/97.0/linux-x86_64/en-US/firefox-97.0.tar.bz2" | tar jx --strip-components 1
cd ~
sudo chmod +x /home/vagrant/firefox/97.0

if [ "$INSTALL_CODE" -ne 0 ]; then
    echo "There were errors installing the packages."
    echo "Run 'vagrant ssh -c \"sudo apt-get install -f\"'"
    echo "  then run 'vagrant reload'"
else
    echo "Run vagrant reload!"
fi
