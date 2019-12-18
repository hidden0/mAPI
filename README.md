# mAPI
Meraki API monitor

The intent of this tool is to quickly and easily produce a visualization for at-scale Cisco Meraki deployments.
With thousands of devices to monitor, mAPI achieves a fast and reliable overview of your entire deployment.

# Usage

```
git clone https://github.com/hidden0/mAPI.git
cd mAPI && ./setup.sh
```


The above will install grafana, postgresql, and python. Finally a cronjob will run every minute to continually update the grafana visualization.

Once the installation is complete, navigate to ```localhost``` in your browser to see the results.

# Optional
Slack integration is entirely optional but available. The requirements are as follows:
1. Create a slack workspace - https://slack.com/create
2. Create a slack app to generate a webhook and oauth token - https://api.slack.com/apps?new_app=1
3. Type "yes" when prompted to enable slack integration, and provide the aforementioned details from your new app.


# Requirements
You will need some experience with linux, bash, and python to comfortably navigate any errors you may encounter during setup.
Further, a computer is required to run the graphing server (grafana). Some examples:
- A raspberri pi
- Ubuntu server
- CentOS 7

This tool can be run on any hardware or as a VM that has a connection to the internet.

# How it works

The general flow of this tool is as follows:

1. Run ./setup.sh to install necessary dependencies as well as grafana, postgresql, and python.
	- Detects package manager (yum or apt)
	- Installs iptables-persistent python python-pip adduser libfontconfig1 postgresql postgresql-contrib libpq-dev python-psycopg2
	- Starts ./install.py
2. The setup script will then transition to the ./install.py code knowing python has been successfully installed.
	- Install will ask for the API key to use to query device status
	- A password will be requested to configure the grafana and postgres service accounts.
	- The data sources and dashboards are provisioned for grafana.
	- Postgres gives the "grafana" postgres user access to the necessary database for grafana to read.
	- Install the ./check.py file in the sudo crontab to execute every minute
3. The ./check.py file is regularly ran to update the database, and hence Grafana output.
	- The API key is used to pull for known organizations, and inserts/updates the mnode_org table with any pertinent changes.
	- For each organization found with the API key, the API device status endpoint is queried.
	- Each device reported in the query has a new entry in mnode_stats to track device status over time.
	- A change in device count or organization name will trigger the check.py script to rebuild and provision an updated grafana dashboard to reflect changes.
