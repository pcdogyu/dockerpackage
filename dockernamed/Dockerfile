FROM opensuse/leap
MAINTAINER Hao.yu01@sap.com - lastupdate 2020.11.18

#COPY repos/*.repo /etc/zypp/repos.d/

RUN zypper --gpg-auto-import-keys ref \
  && zypper in -y --no-recommends bind bind-utils which \
  && zypper in -y --no-recommends net-tools-deprecated iputils telnet vim \
  && zypper in -y --no-recommends python3 python3-pip \
  && zypper clean -a \
  && pip install dnspython dnslib \
  && pip install --upgrade pip

# in real system, this is a bind mount...
# RUN rm -rfv /var/run; ln -s /run /var/

VOLUME /data

ENV BIND_USER=named \
    DATA_DIR=/data

#COPY named.conf /etc/named.conf
#COPY named-hidden-master.conf /etc/named-hidden-master.conf
#COPY named-hidden-master-slave.conf /etc/named-hidden-master-slave.conf
#COPY files/acl.conf /etc/named.d/acl.conf

# Needed for proxy and cleanup scripts
#COPY files/proxy/dns_proxy.py /scripts/
#COPY files/proxy/dns_cleanup.py /scripts/
#COPY files/proxy/lib/*  /scripts/lib/

#RUN sed -i -e "s/instance_network_ip/$LISTEN_IP/g" /etc/named.conf

COPY entrypoint.sh /sbin/entrypoint.sh

RUN chmod 755 /sbin/entrypoint.sh 
#RUN chmod 755 /sbin/entrypoint.sh /scripts/dns_cleanup.py /scripts/dns_proxy.py

EXPOSE 53/udp 53/tcp

ENTRYPOINT ["/sbin/entrypoint.sh"]

CMD ["/usr/sbin/named"]



