FROM python:3.12-slim-bookworm AS base_os
ARG VERSION
ARG GIT_SHA
ARG BUILD_DATE

RUN set -x \
  && runtimeDeps=" \
    nginx \
    gettext \
    libmagic1 \
    libxml2 \
    libldap-2.5-0 \
  " \
  && buildDeps=" \
wget \
" \
  && apt-get update \
    && echo "exit 101" > /usr/sbin/policy-rc.d \
    && chmod +x /usr/sbin/policy-rc.d \
    && apt-get install -y --no-install-recommends ${buildDeps} ${runtimeDeps} \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm /usr/sbin/policy-rc.d

RUN groupadd --gid 1024 unicef \
    && adduser --disabled-login --disabled-password --no-create-home --ingroup unicef -q hope

# ------- deps -------
FROM base_os AS deps
RUN set -x \
    && buildDeps="build-essential \
cmake \
curl \
gcc \
git \
libfontconfig1 \
libgconf-2-4 \
libglib2.0-0 \
libldap2-dev \
libnss3 \
libsasl2-dev \
libssl-dev \
libxml2-dev  \
libzbar-dev \
python3-dev \
zlib1g-dev  \
" \
    && apt-get install -y --no-install-recommends $buildDeps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uwsgi uv

# ------- builder -------
FROM deps AS builder
ENV VIRTUAL_ENV=/venv \
    UV_PROJECT_ENVIRONMENT=/venv

RUN <<EOF cat> /RELEASE
{"version": "$VERSION",
  "commit": "$GIT_SHA"
  "date": "$BUILD_DATE"
}
EOF
WORKDIR /code
COPY . /code

RUN uv venv $VIRTUAL_ENV \
    && uv sync --frozen --no-editable

RUN ls /venv/lib/python3.12/site-packages/aurora/

# ------- distro -------
FROM base_os AS dist
ADD docker/conf /conf/
ADD docker/bin/* /usr/local/bin/
RUN pip install circus

COPY --from=deps /usr/local/bin/uwsgi /usr/local/bin/
COPY --from=builder /venv /venv

ENV PATH=/venv/bin:/usr/local/bin/:/usr/bin:/bin:/usr/sbin \
    VERSION=$VERSION \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE="aurora.config.settings" \
    STATIC_URL="/static/" \
    PYTHONPATH=""\
    GIT_SHA=$GIT_SHA \
    PGSSLCERT="/tmp/postgresql.crt" \
    UWSGI_PROCESSES=4\
    START_PROXY="true" \
    START_APP="true" \
    START_WORKER="false" \
    START_CRON="false"


EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["run"]


LABEL org.opencontainers.image.authors="hope@unicef.org"
LABEL org.opencontainers.image.created="$BUILD_DATE"
LABEL org.opencontainers.image.description="Aurora"
LABEL org.opencontainers.image.documentation="https://unicef.github.io/hope-aurora/"
LABEL org.opencontainers.image.licenses="https://github.com/unicef/hope-aurora/blob/${GIT_SHA:-develop}/LICENSE.md"
LABEL org.opencontainers.image.revision=$GIT_SHA
LABEL org.opencontainers.image.source="https://github.com/unicef/hope-aurora/tree/${GIT_SHA:-develop}/"
LABEL org.opencontainers.image.title="Aurora"
LABEL org.opencontainers.image.version="$VERSION"
LABEL org.opencontainers.image.url="https://register.unicef.org/"
LABEL org.opencontainers.image.vendor="UNICEF"
