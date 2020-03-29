#!/bin/bash

# if [ -n "$DJANGOPID" ]; then
#   kill $DJANGOPID
# fi

ps -aux | grep 'runserver 8080' | awk '{print $2}' | xargs kill -9

git pull

nohup python manage.py runserver 8080 > api.log 2>&1 &

# export DJANGOPID=$(echo $!)

