#!/bin/bash

TAG=$(date +'%Y%m%d%H%M%S')
IMAGE="imagenode"

export DOCKER_BUILDKIT=1

. ./.env

cleanup_previous_container() {
  # Check if the container exists
  if docker ps -a --filter "name=node-container" --format '{{.Names}}' | grep -q '^node-container$'; then
    echo "Stopping and removing the existing 'node-container'..."
    docker stop node-container
    docker rm node-container
  else
    echo "No existing 'node-container' found. Proceeding with build..."
  fi
}

cleanup_previous_container

echo "Building imagenode image..."
docker build -t ${IMAGE}:${TAG} .

# Run the Docker container
docker run -d \
  --name node-container \
  --env-file .env \
  -t \
  ${IMAGE}:${TAG}
