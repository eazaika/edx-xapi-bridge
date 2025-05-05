#!/bin/sh
set -e

export DOCKER_TAG=dev
docker build -t xapi_bridge:$DOCKER_TAG .
