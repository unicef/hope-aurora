#!/bin/bash

aurora --version
uwsgi --version

django-admin check --deploy
