#!/bin/bash

source /opt/ros/humble/setup.bash
cd ros_msgs
if colcon build; then
  source install/setup.bash
  cd ../../react-app
  if yarn build; then
      cd ../server
      if python3 -m flask run --no-reload --host=0.0.0.0; then
          echo "Goodbye!"
      else
          echo "The server did not build correctly."
      fi
  else
      echo "The react app did not build properly."
      cd ../server
  fi
else
  echo "The message files did not build properly."
fi