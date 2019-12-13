#!/bin/bash
clear
echo ""
echo "Getting things ready... "
echo ""
chmod +x ./reset.sh
./reset.sh

PACKMAN="yum"

# Section: Architecture detection
if [ -f /etc/os-release ]; then
    # freedesktop.org and systemd
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    # linuxbase.org
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
elif [ -f /etc/lsb-release ]; then
    # For some versions of Debian/Ubuntu without lsb_release command
    . /etc/lsb-release
    OS=$DISTRIB_ID
    VER=$DISTRIB_RELEASE
elif [ -f /etc/debian_version ]; then
    # Older Debian/Ubuntu/etc.
    OS=Debian
    VER=$(cat /etc/debian_version)
elif [ -f /etc/SuSe-release ]; then
    # Older SuSE/etc.
    ...
elif [ -f /etc/redhat-release ]; then
    # Older Red Hat, CentOS, etc.
    ...
else
    # Fall back to uname, e.g. "Linux <version>", also works for BSD, etc.
    OS=$(uname -s)
    VER=$(uname -r)
fi

if [[ $OS == *"Cent"* ]]; then
	PACKMAN="yum"
else
	PACKMAN="apt"
fi

if [[ $PACKMAN == "yum" ]]; then
	sudo yum install epel-release -y >/dev/null 2>&1
	sudo yum update -y >/dev/null 2>&1
	sudo yum install python python-pip -y >/dev/null 2>&1
	sudo yum install postgresql-server postgresql-contrib -y >/dev/null 2>&1
else
	#sudo add-apt-repository ppa:jonathonf/python-3.6
	sudo apt-get update -y
	sudo apt-get install iptables-persistent python python-pip adduser libfontconfig1 postgresql postgresql-contrib libpq-dev python-psycopg2 -y
	sudo apt-get -f install
fi
chmod +x ./install.py
chmod +x ./check.py

./install.py $PACKMAN
