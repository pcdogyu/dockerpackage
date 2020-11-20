FROM opensuse/leap
MAINTAINER hao.yu01@sap.com
RUN zypper --gpg-auto-import-keys ref
RUN zypper up
RUN zypper install -y bind bind-utils bind-doc
RUN zypper install -y vim which iputils telnet net-tools-deprecated
EXPOSE 53
CMD ["/usr/sbin/named"]

