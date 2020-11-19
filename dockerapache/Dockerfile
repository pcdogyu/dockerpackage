FROM opensuse/leap

MAINTAINER Hao.yu01@sap.com - lastupdate 2020.11.19

RUN RUN zypper --gpg-auto-import-keys ref

RUN zypper addrepo -f http://packman.inode.at/suse/openSUSE_Leap_15.2/ packman

RUN zypper install httpd

CMD apachectl -DFOREGROUND

