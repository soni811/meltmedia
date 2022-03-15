#!/bin/bash

# if executed using the xprofile, output will be sent to $HOME/emu-startup.log

# check for running emu's
hippo_pids=$(ps uwx | grep '/vagrant/main.py' | grep -v grep)

if [ "$?" -eq 0 ]; then
  # kill running hippo instances
  echo "Killing $hippo_pids"
  ps uwx | grep '/vagrant/main.py' | grep -v grep | awk '{print($2)}' | xargs kill
fi

attempts=0

while [ ! -e "/vagrant/main.py" ]
do
  if [ "$attempts" -gt 30 ];
  then
    echo "got tired of waiting for /vagrant, aborting."
    exit 1
  fi
  echo "delaying startup waiting on /vagrant"
  let attempts=attempts+1
  sleep 2
done

if [ "$attempts" -eq 0 ]; then
  echo "vagrant ready with no delay"
fi

echo "starting hippo in the background"

cd "/vagrant"

# export the display to use
export DISPLAY=':0.0'

# check for the setenv file
if [ -e "/vagrant/bin/setenv.sh" ]; then
  . /vagrant/bin/setenv.sh
fi

echo "running hippo with the following environment"
env

if [ -z "$HIPPO_ARGS" ]; then
  export HIPPO_ARGS="-e develop"
fi

echo "running: /usr/bin/python3 /vagrant/main.py $HIPPO_ARGS"
/usr/bin/python3 /vagrant/main.py $HIPPO_ARGS &> "$HOME/hippo.log" &
