#!/bin/bash

set -eou pipefail

production() {
    uwsgi \
        --http :8000 \
        --master \
        --module=src.app.config.wsgi \
        --processes=2 \
        --buffer-size=8192
}

if [ $# -eq 0 ]; then
    production
fi

case "$1" in
    "dev")
        ./wait-for-it.sh db:5432
        python3 manage.py upgrade
        python3 manage.py runserver 0.0.0.0:8000 
    ;;
    "prd")
        production
    ;;
    *)
        exec "$@"
    ;;
esac