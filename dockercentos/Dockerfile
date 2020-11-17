FROM scratch
MAINTAINER Hao.yu01@sap.com - lastupdate 2020.11.17
ADD centos-8-x86_64.tar.xz /
COPY entrypoint.sh /sbin/entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/sbin/entrypoint.sh"]
