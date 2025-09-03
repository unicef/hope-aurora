#!/bin/bash

echo "Aurora", $(aurora --version)
echo "uwsgi", $(uwsgi --version)

echo "nginx", $(nginx --version)
/usr/sbin/nginx -tc /conf/nginx.conf

echo "circusd", $(circusd --version)

django-admin check --deploy
