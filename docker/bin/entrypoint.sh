#!/bin/bash
set -e
export NGINX_MAX_BODY_SIZE="${NGINX_MAX_BODY_SIZE:-30M}"
export NGINX_CACHE_DIR="${NGINX_CACHE_DIR:-/data/nginx/cache}"
export NGINX_APP_ROOT="/"
export REDIS_LOGLEVEL="${REDIS_LOGLEVEL:-warning}"
export REDIS_MAXMEMORY="${REDIS_MAXMEMORY:-100Mb}"
export REDIS_MAXMEMORY_POLICY="${REDIS_MAXMEMORY_POLICY:-volatile-ttl}"

export DOLLAR='$'

mkdir -p /var/run /var/nginx ${NGINX_CACHE_DIR} ${MEDIA_ROOT} ${STATIC_ROOT}
echo "created support dirs /var/run ${MEDIA_ROOT} ${STATIC_ROOT}"


if [ $# -eq 0 ]; then
    if [ "${MAINTENANCE_MODE}" = "on" ]; then
      cp /var/nginx/maintainance.html /var/nginx/system/maintainance.html
    else
      rm -f /var/nginx/system/maintainance.html
      envsubst < /conf/nginx.conf.tpl > /conf/nginx.conf && nginx -tc /conf/nginx.conf
      envsubst < /conf/redis.conf.tpl > /conf/redis.conf
      redis-server /conf/redis.conf
      django-admin upgrade --no-input
      exec uwsgi --ini /conf/uwsgi.ini
    fi
    nginx -c /conf/nginx.conf
else
    case "$1" in
        "dev")
        until pg_isready -h db -p 5432;
          do echo "waiting for database"; sleep 2; done;
        django-admin collectstatic --no-input
        django-admin migrate
        django-admin runserver 0.0.0.0:8000
        ;;
    *)
    exec "$@"
    ;;
    esac
fi
