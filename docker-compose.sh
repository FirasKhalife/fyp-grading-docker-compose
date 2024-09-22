#!/bin/bash

docker-compose \
  -f docker-compose/docker-compose.yml \
  -f docker-compose/docker-compose.spring-boot.yml \
  -f docker-compose/docker-compose.spring-cloud.yml \
  -f docker-compose/docker-compose.messaging.yml \
  -f docker-compose/docker-compose.database.yml \
  -f docker-compose/docker-compose.redis.yml \
  -f docker-compose/docker-compose.grafana.yml \
  -f docker-compose/docker-compose.frontend.yml \
  up
