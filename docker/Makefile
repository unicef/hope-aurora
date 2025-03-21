# envs to set before use this script
.ONESHELL:
VERSION := $(shell grep -m 1 version ../pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
BUILD_DATE:="$(shell date +"%Y-%m-%d %H:%M")"
SOURCE_COMMIT=$(shell git rev-parse --short HEAD)
STAGE?=dist
TAG?=${VERSION}

help:
	@echo "Docke"

.build:
	DOCKER_BUILDKIT=1 cd .. && docker build \
			--build-arg BUILDKIT_INLINE_CACHE=1 \
			--build-arg VERSION=${VERSION} \
			--build-arg BUILD_DATE=${BUILD_DATE} \
			--build-arg GIT_SHA=${SOURCE_COMMIT} \
			--cache-from ${DOCKER_IMAGE_NAME}:${VERSION}-base \
			--cache-from ${DOCKER_IMAGE_NAME}:${VERSION}-builder \
			--cache-from ${DOCKER_IMAGE_NAME}:${VERSION}-production \
			--cache-to type=inline,mode=max \
			--target ${STAGE} \
			${BUILD_OPTIONS} \
			-t ${DOCKER_IMAGE} \
			-f docker/Dockerfile .
	docker images | grep "${DOCKER_IMAGE_NAME}" | grep ${VERSION}
	docker inspect ${DOCKER_IMAGE} | jq -r '.[0].Config.Labels'


build:
	DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:${VERSION} \
	$(MAKE) .build ## build image

.build-stage:
	DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:${VERSION}-${STAGE} \
	$(MAKE) .build

base:
	STAGE=base $(MAKE) .build-stage

builder:
	STAGE=builder $(MAKE) .build-stage


tests:
	STAGE=tests $(MAKE) .build-stage

production:
	STAGE=production $(MAKE) .build-stage

dist:
	STAGE=dist $(MAKE) .build-stage


step1: base
step2: builder
step3: tests
step4: production
step5: dist

.run:
	cd .. && docker run \
	 		--rm \
			-p 8000:8000 \
			-e ADMIN_EMAIL="${ADMIN_EMAIL}" \
			-e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
			-e ALLOWED_HOSTS="*" \
			-e CACHE_DEFAULT="redis://host.docker.internal:6379/0" \
			-e CELERY_BROKER_URL=redis://host.docker.internal:6379/0 \
			-e CSRF_COOKIE_SECURE=False \
			-e CSRF_TRUSTED_ORIGINS=http://localhost \
			-e DATABASE_URL="postgres://postgres:@host.docker.internal:5432/aurora" \
			-e DEBUG="1" \
			-e DJANGO_ADMIN_URL=admin/ \
			-e DJANGO_SETTINGS_MODULE=aurora.config.settings \
			-e LOGGING_LEVEL="DEBUG" \
			-e SECRET_KEY="super-secret-key-just-for-testing" \
			-e SENTRY_DSN="${SENTRY_DSN}" \
			-e SOCIAL_AUTH_REDIRECT_IS_HTTPS="False" \
			-e SUPERUSERS="sax," \
			-v ./docker/conf/:/conf \
			${RUN_OPTIONS} \
			-t ${DOCKER_IMAGE} \
			${CMD}

run:
	DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:${TAG} \
 	CMD='run' \
	$(MAKE) .run


shell:
	DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:${TAG} \
	RUN_OPTIONS="-it" \
 	CMD='/bin/bash' \
	$(MAKE) .run


run-tests:
	CMD='pytest tests/ -x -n auto -v --maxfail=5 --migrations' \
	RUN_OPTIONS="-it -v ./output/:/app/output \
              -v ./src/:/app/src \
              -v ./tests:/app/tests \
              -v ./pytest.ini:/app/pytest.ini" \
	TAG="tests" \
	DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:${VERSION}-tests \
	$(MAKE) .run
