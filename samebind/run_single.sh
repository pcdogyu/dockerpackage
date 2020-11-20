#!/bin/bash
docker pull sameersbn/bind:latest
docker run --name dns_single -d --restart=always \
  --publish 53:53/tcp --publish 53:53/udp --publish 10000:10000/tcp \
  --volume /opt/bind:/data --env='WEBMIN_INIT_SSL_ENABLED=false' \
 --env='ROOT_PASSWORD=root@123'  sameersbn/bind:latest
