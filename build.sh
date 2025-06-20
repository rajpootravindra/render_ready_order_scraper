#!/usr/bin/env bash
apt-get update
apt-get install -y unzip xvfb libxi6 libgconf-2-4 libnss3 libxss1 libappindicator1 libindicator7 wget curl
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome*.deb
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
wget -N https://chromedriver.storage.googleapis.com/$(echo $CHROME_VERSION | cut -d '.' -f 1)/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver