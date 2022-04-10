worker_processes 1;
events {
#  worker_connections 1024;
}
daemon on;
error_log /dev/stdout;

http {
    include    /conf/mime.types;
    server {
        client_max_body_size ${NGINX_MAX_BODY_SIZE};
        access_log /dev/stdout;
        listen 80;
         location /favicon.ico {
            alias ${STATIC_ROOT}/favicon/favicon.ico;
            etag off;
            if_modified_since off;
            add_header Cache-Control "public, no-transform, immutable";
            expires 1d;
         }
         location /static/ {
            root /var;
            autoindex off;
            etag off;
            if_modified_since off;
            add_header Cache-Control "public, no-transform, immutable";
            expires 1y;
            gzip on;
            gzip_disable "MSIE [1-6]\.";
            gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml;
         }

        location / {
            http2_push https://browser.sentry-cdn.com/5.30.0/bundle.min.js;
            http2_push https://unpkg.com/tailwindcss@1.9.6/dist/tailwind.min.css;

            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Scheme $scheme;
        }
    }
}