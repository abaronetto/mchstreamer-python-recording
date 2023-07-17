#!/bin/bash

# install python 3.6 
sudo apt-get python3.6

# install portaudio modules
sudo apt-get install libasound-dev

# install pyaudio and wave libraries for recording
sudo apt-get install python3-pyaudio
sudo pip3 install wave

# install jack
sudo apt-get install multimedia-jack

# enable the package, select 'yes' in the window
dpkg-reconfigure -p high jackd2 

# add the user to the audio group
sudo adduser $(whoami) audio

# reboot to make changes effective
reboot
