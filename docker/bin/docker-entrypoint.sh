#!/bin/bash
set -e
export NGINX_MAX_BODY_SIZE="${NGINX_MAX_BODY_SIZE:-30M}"
export NGINX_CACHE_DIR="${NGINX_CACHE_DIR:-/data/nginx/cache}"
export MEDIA_ROOT="${MEDIA_ROOT:-/var/media}"
export STATIC_ROOT="${STATIC_ROOT:-/var/static}"

export REDIS_LOGLEVEL="${REDIS_LOGLEVEL:-warning}"
export REDIS_MAXMEMORY="${REDIS_MAXMEMORY:-100Mb}"
export REDIS_MAXMEMORY_POLICY="${REDIS_MAXMEMORY_POLICY:-volatile-ttl}"
export AURORA_VERSION=${VERSION}
export AURORA_BUILD=${BUILD_DATE}

export DOLLAR='$'

mkdir -p /var/run /var/nginx ${NGINX_CACHE_DIR} ${MEDIA_ROOT} ${STATIC_ROOT}
echo "created support dirs /var/run '${MEDIA_ROOT}' '${STATIC_ROOT}' "
echo "Startup command is: '$1'"
echo "Startup configuration:"
echo "   START_PROXY:         '$START_PROXY'"
echo "   START_APP:           '$START_APP'"
echo "   START_WORKER:        '$START_WORKER'"
echo "   START_CRON:          '$START_CRON'"
echo "   START_CELERY_WORKER: '$START_CELERY_WORKER'"

/etc/init.d/nginx stop

case "$1" in
    "run")
        envsubst < /conf/nginx.conf.tpl > /conf/nginx.conf && /usr/sbin/nginx -tc /conf/nginx.conf
        django-admin upgrade --no-input
        circusd /conf/circus.ini
    ;;
    "dev")
        until pg_isready -h db -p 5432;
          do echo "waiting for database"; sleep 2; done;
        django-admin collectstatic --no-input
        django-admin migrate
        django-admin runserver 0.0.0.0:8000
    ;;
    "setup")
        until pg_isready -h db -p 5432;
          do echo "waiting for database"; sleep 2; done;
        django-admin upgrade --no-input
    ;;
    *)
      exec "$@"
    ;;
esac
