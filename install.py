#!/usr/bin/env python
import sys
import os
import time
import platform
import subprocess
import getpass
pathname = os.path.dirname(sys.argv[0])
print(os.path.abspath(os.path.abspath(pathname)+'/lib'))
sys.path.append(os.path.abspath(os.path.abspath(pathname)+'/lib'))
import mnode

packman=sys.argv[1]
header = "\
                         ___                       \n\
                        (   )                      \n\
 ___ .-.     .--.     .-.| |    .--.       .--.    \n\
(   )   \   /    \   /   \ |   /    \    /  _  \   \n\
 |  .-. .  |  .-. ; |  .-. |  |  .-. ;  . .' `. ;  \n\
 | |  | |  | |  | | | |  | |  |  | | |  | '   | |  \n\
 | |  | |  | |  | | | |  | |  |  |/  |  _\_`.(___) \n\
 | |  | |  | |  | | | |  | |  |  ' _.' (   ). '.   \n\
 | |  | |  | '  | | | '  | |  |  .'.-.  | |  `\ |  \n\
 | |  | |  '  `-' / ' `-'  /  '  `-' /  ; '._,' '  \n\
(___)(___)  `.__.'   `.__,'    `.__.'    '.___.'   \n\
                                                   \n\
                                                   \n"
colors = {
	'blue': '\033[94m',
	'pink': '\033[95m',
	'green': '\033[92m',
	'yellow': '\033[93m',
	'white': '\033[37m'
	}

# Defining functions before menus (menus make reference to function calls)

# Allow colors array to emphasize instructions in terminal
def colorize(string, color):
	if not color in colors: return string
	return colors[color] + string + '\033[0m'

# Install setup for yum
def yumSetup():
	# Configure Grafana
	os.system('sudo firewall-cmd --permanent --add-port=80/tcp >/dev/null 2>&1')
	os.system('sudo firewall-cmd --permanent --add-port=3000/tcp >/dev/null 2>&1')
	os.system('sudo firewall-cmd --reload >/dev/null 2>&1')
	os.system('sudo yum install wget -y >/dev/null 2>&1')
	os.system('wget https://dl.grafana.com/oss/release/grafana-6.5.1-1.x86_64.rpm >/dev/null 2>&1')
	os.system('sudo yum localinstall grafana-6.5.1-1.x86_64.rpm -y >/dev/null 2>&1')

	# Grafana config file setup

	os.system('sudo grafana-cli admin reset-admin-password '+newPw)

	# Create the datasource yaml file
	"""
	apiVersion: 1

	datasources:
	  - name: Postgres
	    type: postgres
	    url: localhost:5432
	    database: grafana
	    user: grafana
	    secureJsonData:
	      password: ""
	    jsonData:
	      sslmode: "disable" # disable/require/verify-ca/verify-full
	      maxOpenConns: 0         # Grafana v5.4+
	      maxIdleConns: 2         # Grafana v5.4+
	      connMaxLifetime: 14400  # Grafana v5.4+
	      postgresVersion: 903 # 903=9.3, 904=9.4, 905=9.5, 906=9.6, 1000=10
	      timescaledb: false
	"""
	# Put the yaml files in /etc/grafana/provisioning as necessesary
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/dashboard.yaml /etc/grafana/provisioning/dashboards/')
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/datasources.yaml /etc/grafana/provisioning/datasources/')

	# Put the json files in /var/lib
	os.system('sudo mkdir -p /var/lib/grafana/dashboards')
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/dashboard.json /var/lib/grafana/dashboards/')
	os.system('sudo chown -hR grafana:grafana /var/lib/grafana/')
	# Final Grafana restart
	os.system('sudo /bin/systemctl daemon-reload')
	os.system('sudo /bin/systemctl enable grafana-server.service')
	os.system('sudo systemctl reset-failed grafana-server.service')
	os.system('sudo systemctl stop grafana-server.service')
	os.system('sleep 1')
	os.system('sudo systemctl start grafana-server.service')
	os.system('sudo /bin/systemctl restart grafana-server.service')
	os.system('sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3000')
	print("\nIP TABLES UPDATED\n")

	# Configure postgres
	os.system('sudo postgresql-setup initdb >/dev/null 2>&1')
	os.system('sudo systemctl enable postgresql >/dev/null 2>&1')
	print "\nPostgreSQL Setup:\n"

	os.system('echo '+newPw+' | sudo passwd -f --stdin postgres')
	print("Line 187")
	os.system('sudo -u postgres psql -d template1 -c "ALTER USER postgres WITH PASSWORD \''+newPw+'\';"')
	os.system('sudo -u postgres createdb mnodes')
	os.system('sudo -u postgres createuser grafana')
	os.system('sudo -u postgres psql -c "ALTER USER grafana WITH PASSWORD \''+newPw+'\';"')
	os.system('sudo -u postgres psql -d mnodes -c "grant all privileges on database mnodes to grafana"')
	os.system('mkdir '+os.path.abspath(pathname)+'/conf >/dev/null 2>&1')
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/pg_hba.conf /var/lib/pgsql/data/')
	os.system('sudo chown -hR postgres:postgres /var/lib/pgsql/data/')
	os.system('sudo systemctl restart postgresql >/dev/null 2>&1')

	# Create a cronjob to execute ./check.py every 5 minutes.

	cron="*/5 * * * * "+os.getcwd()+"/check.py >> /var/log/cron.log 2>&1\n"
	with open(''+os.path.abspath(pathname)+'/mycron', 'w') as the_file:
		the_file.write(cron)
		the_file.close()
	os.system('sudo crontab '+os.path.abspath(pathname)+'/mycron')
	os.system('sudo rm -f '+os.path.abspath(pathname)+'/mycron')

# Install setup for apt
def aptSetup():
	# Grafana d/l url
	grafana = "https://dl.grafana.com/oss/release/grafana_6.5.1_amd64.deb"
	# Is this arm?
	p = platform.platform()
	if "arm" in str(p).lower():
		fullUname = subprocess.check_output(["arch"]).strip()
		if fullUname == "armv7l":
			grafana = "https://dl.grafana.com/oss/release/grafana-rpi_6.5.1_armhf.deb"
		else:
			grafana = "https://dl.grafana.com/oss/release/grafana_6.5.1_arm64.deb"
	# Configure Grafana
	os.system('sudo apt-get install software-properties-common -y >/dev/null 2>&1')
	os.system('sudo apt-get install wget ca-certificates -y >/dev/null 2>&1')
	os.system('sudo wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -')
	os.system('sudo wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -')
	os.system('wget '+grafana+' >/dev/null 2>&1')
	os.system('sudo dpkg -i ./grafana*')

	# Grafana config file setup

	os.system('sudo grafana-cli admin reset-admin-password '+newPw)

	# Create the datasource yaml file
	"""
	apiVersion: 1
	datasources:
	  - name: Postgres
	    type: postgres
	    url: localhost:5432
	    database: grafana
	    user: grafana
	    secureJsonData:
	      password: ""
	    jsonData:
	      sslmode: "disable" # disable/require/verify-ca/verify-full
	      maxOpenConns: 0         # Grafana v5.4+
	      maxIdleConns: 2         # Grafana v5.4+
	      connMaxLifetime: 14400  # Grafana v5.4+
	      postgresVersion: 903 # 903=9.3, 904=9.4, 905=9.5, 906=9.6, 1000=10
	      timescaledb: false
	"""

	# Put the yaml files in /etc/grafana/provisioning as necessesary
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/dashboard.yaml /etc/grafana/provisioning/dashboards/')
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/datasources.yaml /etc/grafana/provisioning/datasources/')

	# Put the json files in /var/lib
	os.system('sudo mkdir -p /var/lib/grafana/dashboards')
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/dashboard.json /var/lib/grafana/dashboards/')
	os.system('sudo chown -hR grafana:grafana /var/lib/grafana/')
	os.system('sudo rm -f /var/lib/grafana/dashboard.json')
	# Final Grafana restart
	os.system('sudo systemctl enable grafana-server')
	os.system('sudo systemctl restart grafana-server')

	os.system('sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3000')
	os.system('sudo sh -c "iptables-save > /etc/iptables.rules"')
	print("\nIP TABLES UPDATED\n")

	# Configure postgres
	os.system('sudo sh -c \'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list\'')
	os.system('sudo apt-get update')
	os.system('sudo postgresql-setup initdb >/dev/null 2>&1')
	os.system('sudo systemctl enable postgresql >/dev/null 2>&1')
	print "\nPostgreSQL Setup:\n"


	os.system('echo "postgres:'+newPw+'" | sudo chpasswd')
	print("Line 187")
	os.system('sudo -u postgres psql -d template1 -c "ALTER USER postgres WITH PASSWORD \''+newPw+'\';"')
	os.system('sudo -u postgres createdb mnodes')
	os.system('sudo -u postgres createuser grafana')
	os.system('sudo -u postgres psql -c "ALTER USER grafana WITH PASSWORD \''+newPw+'\';"')
	os.system('sudo -u postgres psql -d mnodes -c "grant all privileges on database mnodes to grafana"')
	os.system('sudo mkdir -p '+os.path.abspath(pathname)+'/conf >/dev/null 2>&1')
	# Find postgres version

	os.system('sudo mkdir -p /etc/postgresql/10/main/')
	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/pg_hba.conf /etc/postgresql/10/main/ >/dev/null 2>&1')
	os.system('sudo chown -hR postgres:postgres /var/lib/pgsql/data/ >/dev/null 2>&1')
	os.system('sudo systemctl restart postgresql >/dev/null 2>&1')

	# Create a cronjob to execute ./check.py every 5 minutes.

	cron="*/5 * * * * "+os.getcwd()+"/check.py >> /var/log/cron.log 2>&1\n"
	with open(''+os.path.abspath(pathname)+'/mycron', 'w') as the_file:
		the_file.write(cron)
		the_file.close()
	os.system('sudo crontab '+os.path.abspath(pathname)+'/mycron')
	os.system('sudo rm -f '+os.path.abspath(pathname)+'/mycron')

# Ask slack API questions:
def getSlack():
	print(colorize("Slack Integration Setup","yellow"))
	print("\nTo configure a slack notification channel, this script will ask a few questions.\n")

	print("To set up slack you need to configure an incoming webhook url at slack on your own workspace. You can follow their guide on how to do that here:\n")
	print(colorize("https://api.slack.com/apps?new_app=1","green"))

	print("What is your "+colorize("incoming slack webhook URL","yellow")+"?")
	webhookURL=raw_input(">> ")

	print("Under your slack app -> OAuth & Permissions page, what is your "+colorize("OAuth Access Token","yellow")+"?")
	oauthToken=raw_input(">> ")

	# Update notifier.yaml in conf directory
	notifyYAML="""
notifiers:
  - name: Slack Bot
    type: slack
    uid: notifier1
    # either
    org_id: 1
    # or
    org_name: default
    is_default: true
    send_reminder: true
    frequency: 1h
    disable_resolve_message: false
    # See `Supported Settings` section for settings supporter for each
    # alert notification type.
    settings:
      recipient: "#alerts"
      token: \""""+oauthToken+"""\"
      uploadImage: true
      url: """+webhookURL+"""
"""
	with open(os.path.abspath(pathname)+'/conf/notifier.yaml', 'w') as the_file:
		the_file.write(notifyYAML)

	os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/notifier.yaml /etc/grafana/provisioning/notifiers/')
	os.system('sudo systemctl restart grafana-server')
	os.system('touch ./slack_setup_true')

import psycopg2
from configparser import ConfigParser

# Code starts here
os.system('clear')
print(colorize(header,'green'))
print("Setting up the monitor. What we need to do is:\n\
\tInstall Grafana\n\
\tInstall Postgres\n\
\tObtain your API Key\n")

print("What is your "+colorize("dashboard API key","yellow")+"?")
apiKey=raw_input(">> ")
print("Do you wish to configure "+colorize("slack integration for alerts","yellow")+"?")
slackAns=raw_input("(yes/no)>> ")
if(slackAns=="yes"):
	slackConfig = getSlack()


with open(os.path.abspath(pathname)+'/api.key', 'w') as the_file:
	the_file.write(apiKey)
os.system('sudo chmod 0640 '+os.path.abspath(pathname)+'/api.key')
print("Please set a password to use for "+colorize("Grafana admin user and PostgreSQL user","yellow")+":")
newPw=getpass.getpass()

if(packman=="yum"):
	yumSetup()
else:
	aptSetup()

# Configure database.ini file
with open(os.path.abspath(pathname)+'/conf/database.ini', 'w') as the_file:
	the_file.write('[local]\nhost=localhost\ndatabase=mnodes\nuser=grafana\npassword='+newPw)

sqlStats="""
CREATE TABLE mnode_stats (
id SERIAL PRIMARY KEY,
dateCreated integer,
org_id varchar(64),
mnode_row_id integer REFERENCES mnode(id),
organization_name varchar(128),
numOnline integer,
numAlerting integer,
numOffline integer,
percDiff decimal
);
"""
sqlNode="""
CREATE TABLE mnode (
id SERIAL PRIMARY KEY,
dateCreated integer,
org_id varchar(64),
macAddr varchar(32),
deviceName varchar(64),
deviceModel varchar(32),
deviceSerial varchar(16),
deviceNetwork varchar(128),
deviceUrl varchar,
devStatus varchar(32)
);
"""
sqlOrg="""
CREATE TABLE mnode_org (
id SERIAL PRIMARY KEY,
dateCreated integer,
organization_id varchar(64),
organization_name varchar(128),
organization_url varchar(512),
totalDevices integer
);
"""
dbObj = mnode.mNodeStorage(os.path.abspath(pathname)+"/conf/database.ini","local")
if(dbObj.checkTable("mnode_org")==False):
	dbObj.execSQL(sqlOrg)
if(dbObj.checkTable("mnode")==False):
	dbObj.execSQL(sqlNode)
if(dbObj.checkTable("mnode_stats")==False):
	dbObj.execSQL(sqlStats)

# At this point in the code, everything should be setup and we can start a while loop to monitor node status in the background
