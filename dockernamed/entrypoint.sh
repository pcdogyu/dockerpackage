#!/bin/bash
set -e
set -x

# Set our default values
hidden_master=${hidden_master:-false}
bind_mode=${bind_mode:-"slave"}
BIND_DATA_DIR=${DATA_DIR}/bind

handle_hidden_master() {

  # Check if we need a special configuration for our master
  if [[ "$hidden_master" == true ]]
  then
    if [[ "$bind_mode" == "master" ]]
    then
      pythonCMD="/scripts/dns_proxy.py"
      mv /etc/named-hidden-master.conf ${BIND_DATA_DIR}/etc/named.conf
      if [[ ! -f  ${mySlaveKey} ]]
      then
          /usr/sbin/rndc-confgen -a -b 512 -c ${mySlaveKey}
      fi
    elif [[ "$bind_mode" == "slave" ]]
    then
      pythonCMD="/scripts/dns_cleanup.py"
      mv /etc/named-hidden-master-slave.conf ${BIND_DATA_DIR}/etc/named.conf
      # Check if a slave already created a slave key
      if [[ -f  ${mySlaveKey} ]]
      then
        cp  ${mySlaveKey} ${BIND_DATA_DIR}/etc/rndc.key
      else
        echo "No slave key found under ${mySlaveKey}"
        exit 1
      fi
    else
        echo "No valid value for bind_mode specified. master or slave required"
        exit 1
    fi
  fi
}

create_bind_data_dir() {

  # populate default bind configuration if it does not exist
  if [ ! -d ${BIND_DATA_DIR}/etc ]; then
    /usr/sbin/rndc-confgen -a -b 512
    mkdir -p ${BIND_DATA_DIR}/etc
    mv /etc/named.conf ${BIND_DATA_DIR}/etc/
    mv /etc/named.d ${BIND_DATA_DIR}/etc/
    mv /etc/rndc.key ${BIND_DATA_DIR}/etc/
  fi
  rm -rf /etc/named.conf
  rm -rf /etc/named.d
  rm -rf /etc/rndc.key

  ln -sf ${BIND_DATA_DIR}/etc/named.d /etc/named.d
  ln -sf ${BIND_DATA_DIR}/etc/named.conf /etc/named.conf
  ln -sf ${BIND_DATA_DIR}/etc/rndc.key /etc/rndc.key

  chmod -R 0775 ${BIND_DATA_DIR}
  chown -R ${BIND_USER}:${BIND_USER} ${BIND_DATA_DIR}

  if [ ! -d ${BIND_DATA_DIR}/lib ]; then
    mkdir -p ${BIND_DATA_DIR}/lib
    mv /var/lib/named ${BIND_DATA_DIR}/lib/
  fi

  rm -rf /var/lib/named
  ln -sf ${BIND_DATA_DIR}/lib/named /var/lib/named
  chown -R ${BIND_USER}:${BIND_USER} ${BIND_DATA_DIR}/lib/named/
}

create_pid_dir() {
  mkdir -m 0775 -p /var/run/named
  chown root:${BIND_USER} /var/run/named
}

add_include() {
  include_path=$1

  if [[ -f $include_path ]] && ! grep -q "$include_path" /etc/named.conf; then
    sed -i --follow-symlinks "/\".\"/ i include \"$include_path\";" /etc/named.conf
  fi
}

edit_named_conf() {

  # SAP DNS zones are written to /dns-config/forwarders.conf by cloud-init after terraform ran.
  # This file does not exist when gitlab runs the tests, so only include when
  # file exists and not yet included
  add_include /dns-config/forwarders.conf

  # Support region specific includes. If there are files under /dns-config/my-region/*.conf,
  # we include them. Cloud-init will set the symlink to the correct region
  if compgen -G "/dns-config/my-region/*.conf" > /dev/null; then
    for file in $(compgen -G "/dns-config/my-region/*.conf"); do
      add_include $file
    done
  fi

  sed -i --follow-symlinks -e "s/@DNS_FORWARDER@/${DNS_FORWARDER}/" /etc/named.conf
} # sed without --follow-symlinks options breaks the link (named.conf -> /data/bind/etc/named.conf)

#create_bind_cache_dir() {
#  mkdir -m 0775 -p /var/cache/bind
#  chown root:${BIND_USER} /var/cache/bind
#}

create_pid_dir
create_bind_data_dir

# Do the needfull to get the hidden master stuff working
handle_hidden_master
#create_bind_cache_dir

#If we have a custom acl.conf, use this instead of the default one from the container
if [ -f /dns-config/acl.conf ]; then
    cp /dns-config/acl.conf ${BIND_DATA_DIR}/etc/named.d/
fi

edit_named_conf

# allow arguments to be passed to named
if [[ ${1:0:1} = '-' ]]; then
  EXTRA_ARGS="$@"
  set --
elif [[ ${1} == named || ${1} == $(which named) ]]; then
  EXTRA_ARGS="${@:2}"
  set --
fi

# default behaviour is to launch named
if [[ -z ${1} ]]; then
  if [[ "$hidden_master" = true ]]
  then
    echo "Starting named..."
    echo $(which named)
    exec $(which named) -u ${BIND_USER} -g ${EXTRA_ARGS} &
    echo "Starting python helper scripts..."
    $pythonCMD
  else
    exec $(which named) -u ${BIND_USER} -g ${EXTRA_ARGS}
  fi
else
  exec "$@" &
fi

