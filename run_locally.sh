#!/bin/bash

TAG=$(date +'%Y%m%d%H%M%S')
IMAGE="imagenode"

echo "Deleting imagenode container"
docker-compose stop node 
docker-compose rm -f node 


export DOCKER_BUILDKIT=1

. ./.env

echo "Building imagenode image..."
docker build -t $IMAGE:$TAG  .

echo "Runing imagenode container..."
TAG=$TAG IMAGE=$IMAGE docker-compose up -d node 

echo "Here are the running containers"
docker ps -a
