#!/bin/sh

git pull
docker-compose up --build -d
docker system prune -f
docker-compose logs -f