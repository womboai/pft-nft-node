#!/bin/bash

TAG=$(date +'%Y%m%d%H%M%S')
IMAGE="imagenode"

export DOCKER_BUILDKIT=1

. ./.env

echo "Building imagenode image..."
docker build -t ${IMAGE}:${TAG} .

# Run the Docker container
docker run -d \
  --name node-container \
  --env-file .env \
  -t \
  ${IMAGE}:${TAG}
