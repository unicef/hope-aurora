FROM python:3.12-slim-bookworm AS base
ARG BUILD_DATE
ARG VERSION
ARG GIT_SHA

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                gdal-bin \
                gettext \
                git-core \
                libmagic1 \
                libxml2 \
                locales \
                locales-all \
                nginx \
                postgresql-client \
                postgresql-client-15 \
                python3-gdal \
                python3-psycopg2 \
    && locale-gen --no-purge uk_UA.UTF-8 \
    && apt-get clean


RUN groupadd --gid 1024 unicef \
    && adduser --disabled-login --disabled-password --no-create-home --ingroup unicef -q hope

FROM base AS builder
RUN set -x \
    && buildDeps="build-essential \
cmake \
curl \
gcc \
git \
libfontconfig1 \
libgconf-2-4 \
libglib2.0-0 \
libnss3 \
libssl-dev \
libjpeg-dev \
libpq-dev \
libxml2-dev  \
python3-dev \
zlib1g-dev  \
" \
    && apt-get update \
    && apt-get install -y --no-install-recommends $buildDeps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv uwsgi

# ------- tests -------
FROM builder AS tests
ARG BUILD_DATE
ARG VERSION
ARG GIT_SHA

LABEL distro="tests"
LABEL org.opencontainers.image.created="$BUILD_DATE"
LABEL org.opencontainers.image.version="$VERSION"
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
               ./google-chrome-stable_current_amd64.deb

ENV PATH=/venv/bin:/usr/local/bin/:/usr/bin:/bin \
    DJANGO_SETTINGS_MODULE=aurora.config.settings \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=""\
    UV_PROJECT_ENVIRONMENT=/venv \
    VIRTUAL_ENV=/venv \
    UWSGI_PROCESSES=4

WORKDIR /app
ADD uv.lock README.md MANIFEST.in pyproject.toml /app/
ADD src /app/src/

RUN --mount=type=cache,target=/root/.uv-cache \
      uv sync --cache-dir=/root/.uv-cache \
        --python=/usr/local/bin/python \
        --python-preference=system \
        --frozen

# ------- production only deps-------
FROM builder AS production

WORKDIR /app
COPY uv.lock README.md MANIFEST.in pyproject.toml /app/
COPY src /app/src/
ENV PATH=/venv/bin:/usr/local/bin/:/usr/bin:/bin \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=""\
    UV_PROJECT_ENVIRONMENT=/venv \
    VIRTUAL_ENV=/venv

RUN --mount=type=cache,target=/root/.uv-cache \
    uv sync --cache-dir=/root/.uv-cache \
        --python=/usr/local/bin/python \
        --python-preference=system \
        --no-dev --no-editable --frozen


FROM base AS dist
ARG BUILD_DATE
ARG VERSION
ARG GIT_SHA

ENV PATH=/venv/bin:/usr/local/bin/:/usr/bin:/bin:/usr/sbin/:/usr/local/sbin/ \
    BUILD_DATE="${BUILD_DATE}" \
    DJANGO_SETTINGS_MODULE=aurora.config.settings \
    GIT_SHA="${GIT_SHA}" \
    MEDIA_ROOT=/var/aurora/media \
    PGSSLCERT="/tmp/postgresql.crt" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=""\
    PYTHONUNBUFFERED=1 \
    STATIC_ROOT=/var/aurora/static/ \
    STATIC_URL="/static/" \
    UWSGI_PROCESSES=4 \
    UV_PROJECT_ENVIRONMENT=/venv \
    VIRTUAL_ENV=/venv \
    VERSION="${VERSION}"


WORKDIR /app
ADD docker/conf /conf/
ADD docker/bin/* /usr/local/bin/

ADD uv.lock README.md MANIFEST.in pyproject.toml /app/
ADD src /app/src/

COPY --from=production /venv /venv
COPY --from=builder /usr/local/bin/uwsgi /usr/local/bin/uv /usr/local/bin/

RUN --mount=type=cache,target=/root/.uv-cache \
    uv --cache-dir=/root/.uv-cache pip install --no-deps . \
    && rm -fr /app/*


EXPOSE 8000
ENTRYPOINT exec entrypoint.sh "$0" "$@"
CMD ["run"]

LABEL distro="final"
LABEL maintainer="hope@unicef.org"
LABEL cheksum="$CHECKSUM"

LABEL org.opencontainers.image.authors="hope@unicef.org"
LABEL org.opencontainers.image.created="$BUILD_DATE"
LABEL org.opencontainers.image.description="Bitcaster"
LABEL org.opencontainers.image.documentation="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}"
LABEL org.opencontainers.image.licenses="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/blob/${GIT_SHA:-master}/LICENSE.md"
LABEL org.opencontainers.image.revision=$GIT_SHA
LABEL org.opencontainers.image.source="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/tree/${GIT_SHA:-master}/"
LABEL org.opencontainers.image.title="Aurora"
LABEL org.opencontainers.image.version="$VERSION"
LABEL org.opencontainers.image.url="https://register.unicef.org/"
LABEL org.opencontainers.image.vendor="UNICEF"
