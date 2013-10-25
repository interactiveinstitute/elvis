#!/bin/sh

# install dependencies
sudo apt-get install python-serial python-pyudev

# install node
node_version=0.8.22 # 0.10 and 0.11 don't work
node_folder=node-v${node_version}-linux-arm-pi
node_url=http://nodejs.org/dist/v${node_version}/${node_folder}.tar.gz
wget $node_url
tar xvzf ${node_folder}.tar.gz
rm -rf ${node_folder}.tar.gz
mkdir ~/node
mv ${node_folder} ~/node
cd ~/node && ln -s ${node_folder} 0

# install node-openvg-canvas (takes a while)
sudo apt-get install libfreetype6 libfreetype6-dev libfreeimage3 libfreeimage-dev
~/node/0/bin/npm install --global openvg-canvas

# make sure we can load node modules
echo "export NODE_PATH=$HOME/node/0/lib/node_modules:./node_modules:$NODE_PATH" >> ~/.profile
