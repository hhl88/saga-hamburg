#!/bin/bash

PID_FILE="./app.pid"

killApp() {
  APP_PID="`cat $PID_FILE || echo ""`"

  if [ "$APP_PID" != "" ] && [ $(ps -p"$APP_PID" -o pid=) ];
  then
  	APP_RUNNING="true"

  	echo "PID $APP_PID found in pid file"

  	COUNTER=1
  	while [  $COUNTER -lt 4 ] && [ "$APP_RUNNING" == "true" ];
  	do
  		echo "  $COUNTER. attempt to kill"

  		if [ $COUNTER -gt 2 ];
  		then
  			kill -9 $APP_PID || echo "  Warning: Could not kill $APP_PID"
  		else
  			kill $APP_PID || echo "  Warning: Could not kill $APP_PID"
  		fi

  		sleep 10

  		if kill -0 &>1 > /dev/null $APP_PID;
  		then
  			APP_RUNNING="true"
  		else
  			APP_RUNNING="false"
  		fi

  		let COUNTER=COUNTER+1
  	done

  	if [ "$APP_RUNNING" == "true" ];
  	then
  		echo "  Warning: Could not kill stale app process. Ignoring."
  	fi
  fi
}

# kill running app
killApp
echo "Running app killed"

nohup python3 main.py > /dev/null 2>&1 &
APP_PID=$!
echo "$APP_PID" > $PID_FILE