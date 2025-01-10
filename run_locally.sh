#!/bin/bash

TAG=$(date +'%Y%m%d%H%M%S')
IMAGE="imagenode"

echo "Deleting imagenode container"
docker-compose stop node 
docker-compose rm -f node 


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
