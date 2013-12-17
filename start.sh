#!/bin/bash

# Kill if started
export PID=`ps aux | grep 'escapistvideobot.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$PID" ]; then
  echo "Killing old process "$PID"."
  kill $PID
fi

# Update from git
echo "Pulling latest git version"
git pull

# Start
echo "Starting"
cd src
nohup python3 escapistvideobot.py >../nohup.out 2>&1 &
disown
sleep 1
export PID=`ps aux | grep '__init__.py' | grep -v grep | awk '{print($2)}'`
if [ -n "$PID" ]; then
  echo "Running correctly."
else
  echo "ERROR: Script stopped."
fi

