FROM opensuse/leap

MAINTAINER Hao.yu01@sap.com - lastupdate 2020.11.18

VOLUME /data

ENV BIND_USER=named \
    DATA_DIR=/data

RUN zypper --gpg-auto-import-keys ref \
  && zypper in -y --no-recommends bind bind-doc bind-utils htop which \
  && zypper in -y --no-recommends net-tools-deprecated iputils telnet vim \
  && zypper in -y --no-recommends python3 python3-pip \
  && zypper clean -a 

COPY entrypoint.sh /usr/sbin/entrypoint.sh

RUN chmod 755 /usr/sbin/entrypoint.sh

EXPOSE 53/udp 53/tcp

#ENTRYPOINT ["/usr/sbin/entrypoint.sh"]

CMD ["/usr/sbin/named"]

