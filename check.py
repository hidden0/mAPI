#!/usr/bin/env python
import sys
import os
import time
import json
import requests
pathname = os.path.dirname(sys.argv[0])
debug = None
try:
	val = sys.argv[1]
	if val == "debug":
		debug = True
except:
	debug = None

if debug == True:
	print ("DEBUG MODE TRUE")
	exit()
sys.path.append(os.path.abspath(os.path.abspath(pathname)+'/lib'))
import mnode


# API key read:
f=open(os.path.abspath(pathname)+"/api.key", "r")
apikey=f.read().strip()
apiAction="organizations"
numOnline = 0
numOffline = 0
numAlerting = 0
totalDevices = 0
dbObj = mnode.mNodeStorage(os.path.abspath(pathname)+"/conf/database.ini","local")
apiObj = mnode.mAPI(apikey)

def buildDashboards(orgName, orgId, totalDev):
	print("Building " + orgName + " dashboard")
	# Read in the template
	with open(os.path.abspath(pathname)+"/conf/dashtemplate.json") as json_template:
		dashboard = json.load(json_template)
	print("Dashboard ID: " + str(dashboard['id']))
	print("Dashboard Title: " + dashboard['title'])
	dashboard['editable']='true'
	dashboard['id']=str(orgId)
	dashboard['title'] = orgName + " Device Monitoring"
	dashboard['uid'] = str(orgId)
	dashboard['time']['from']="now-1h"

	targetTmpA = {
	"refId": "A",
	"format": "time_series",
	"timeColumn": "time",
	"metricColumn": "none",
	"h": 14,
	"w": 15,
	"x": 0,
	"y": 6,
	"group": [],
	"where": [
		{
			"type": "macro",
			"name": "$__timeFilter",
			"params": []
		}
	],
	"select": [
		[
			{
			"type": "column",
			"params": [
				"value"
				]
			}
		]
	],
	"rawQuery": "true",
	"rawSql": "SELECT\n  datecreated AS \"time\",\n  CONCAT(organization_name, ' Online') AS metric,\n  numonline as \"Devices Online\"\nFROM mnode_stats\nWHERE organization_name = '"+orgName.strip()+"'\nORDER BY 1,2"
	}
	targetTmpB = {
	"refId": "B",
	"format": "time_series",
	"timeColumn": "time",
	"metricColumn": "none",
	"group": [],
	"where": [
		{
			"type": "macro",
			"name": "$__timeFilter",
			"params": []
		}
	],
	"select": [
		[
			{
			"type": "column",
			"params": [
				"value"
				]
			}
		]
	],
	"rawQuery": "true",
	"rawSql": "SELECT\n  datecreated AS \"time\",\n  CONCAT(organization_name, ' Alerting') AS metric,\n  numalerting as \"Devices Alerting\"\nFROM mnode_stats\nWHERE organization_name = '"+orgName.strip()+"'\nORDER BY 1,2"
	}
	targetTmpC = {
	"refId": "C",
	"format": "time_series",
	"timeColumn": "time",
	"metricColumn": "none",
	"group": [],
	"where": [
		{
			"type": "macro",
			"name": "$__timeFilter",
			"params": []
		}
	],
	"select": [
		[
			{
			"type": "column",
			"params": [
				"value"
				]
			}
		]
	],
	"rawQuery": "true",
	"rawSql": "SELECT\n  datecreated AS \"time\",\n  CONCAT(organization_name, ' Offline') AS metric,\n  numoffline as \"Devices Offline\"\nFROM mnode_stats\nWHERE organization_name = '"+orgName.strip()+"'\nORDER BY 1,2"
	}
	dashboard['panels'][0]['targets'][0]=targetTmpA
	dashboard['panels'][0]['targets'].append(targetTmpB)
	dashboard['panels'][0]['targets'].append(targetTmpC)
	slackInt = False

	# Check for a file existing
	try:
		f = open("./slack_setup_true")
		# Do something with the file
		slackInt = True
		f.close()
	except IOError:
		slackInt = False

	if(slackInt==True):
		panelAlertJson= {
			"alertRuleTags": {},
			"conditions": [
			{
				"evaluator": {
				"params": [
					15
				],
				"type": "gt"
				},
				"operator": {
				"type": "and"
				},
				"query": {
				"params": [
					"A",
					"15m",
					"now"
					]
				},
				"reducer": {
				"params": [],
				"type": "percent_diff"
				},
				"type": "query"
				}
			],
			"executionErrorState": "alerting",
			"for": "15m",
			"frequency": "1m",
			"handler": 1,
			"message": "A difference of 15% change has occurred to online devices in the "+orgName+" monitor.",
			"name": "Online Diff Check",
			"noDataState": "no_data",
			"notifications": []
		}
		panelAlertThreshold=[
			{
			"colorMode": "critical",
			"fill": "true",
			"line": "true",
			"op": "gt",
			"value": 15
			}
		]

		alertPanel = {
			"dashboardFilter": "",
			"dashboardTags": [],
			"datasource": "null",
			"folderId": "null",
			"gridPos": {
				"h": 8,
				"w": 7,
				"x": 17,
				"y": 12
			},
			"id": 16,
			"limit": 10,
			"nameFilter": "",
			"onlyAlertsOnDashboard": "true",
			"options": {},
			"show": "changes",
			"sortOrder": 1,
			"stateFilter": [],
			"timeFrom": "null",
			"timeShift": "null",
			"title": "Recent Alerts",
			"transparent": "true",
			"type": "alertlist"
			}
		dashboard['panels'][0]['alert'] = panelAlertJson
		dashboard['panels'][0]['threshold'] = panelAlertThreshold
		dashboard['panels'].append(alertPanel)

	# Add Panels online/alerting/offline
	gaugePanel=None

	with open(os.path.abspath(pathname)+"/conf/gaugepanel.json") as json_template:
		tmpPanel = json.load(json_template)

	# Online Devices panel
	tmpPanel['gridPos']['h'] = 6
	tmpPanel['gridPos']['w'] = 5
	tmpPanel['gridPos']['x'] = 0
	tmpPanel['gridPos']['y'] = 0
	tmpPanel['id'] = 10
	tmpPanel['options']['fieldOptions']['defaults']['max'] = str(totalDev)
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][0]['value'] = 0
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['value'] = str(round(totalDev/2))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['value'] = str(totalDev-(round(totalDev*0.1)))
	tmpPanel['options']['fieldOptions']['defaults']['title'] = "${__series.name} devices online"
	tmpPanel['targets'][0]['rawSql'] = "SELECT\n  datecreated AS \"time\",\n  organization_name AS metric,\n  numonline\nFROM mnode_stats\nWHERE\n  organization_name = '"+orgName.strip()+"'\nORDER BY 1,2"
	tmpPanel['title'] = "Devices Online"

	dashboard['panels'].append(tmpPanel)

	with open(os.path.abspath(pathname)+"/conf/gaugepanel.json") as json_template:
		tmpPanel = json.load(json_template)

	# Alerting Devices Panel
	tmpPanel['gridPos']['h'] = 6
	tmpPanel['gridPos']['w'] = 5
	tmpPanel['gridPos']['x'] = 5
	tmpPanel['gridPos']['y'] = 0
	tmpPanel['id'] = 11
	tmpPanel['options']['fieldOptions']['defaults']['max'] = str(totalDev)
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][0]['value'] = 0
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['value'] = str(round(totalDev/2))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['value'] = str(totalDev-(round(totalDev*0.1)))
	tmpPanel['options']['fieldOptions']['defaults']['title']= "${__series.name} devices alerting"
	tmpPanel['targets'][0]['rawSql'] = "SELECT\n  datecreated AS \"time\",\n  organization_name AS metric,\n  numalerting\nFROM mnode_stats\nWHERE\n  organization_name = '"+orgName.strip()+"'\nORDER BY 1,2"
	tmpPanel['title'] = "Devices Alerting"

	dashboard['panels'].append(tmpPanel)

	with open(os.path.abspath(pathname)+"/conf/gaugepanel.json") as json_template:
		tmpPanel = json.load(json_template)

	# Offline Devices panel
	tmpPanel['gridPos']['h'] = 6
	tmpPanel['gridPos']['w'] = 5
	tmpPanel['gridPos']['x'] = 10
	tmpPanel['gridPos']['y'] = 0
	tmpPanel['id'] = 12
	tmpPanel['options']['fieldOptions']['defaults']['max'] = str(totalDev)
	tmpPanel['options']['fieldOptions']['defaults']['max'] = str(totalDev)
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][0]['value'] = 0
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['value'] = str(round(totalDev/2))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['value'] = str(totalDev-(round(totalDev*0.1)))
	tmpPanel['options']['fieldOptions']['defaults']['title']= "${__series.name} devices offline"
	tmpPanel['targets'][0]['rawSql'] = "SELECT\n  datecreated AS \"time\",\n  organization_name AS metric,\n  numoffline\nFROM mnode_stats\nWHERE\n  organization_name = '"+orgName.strip()+"'\nORDER BY 1,2"
	tmpPanel['title'] = "Devices Offline"

	dashboard['panels'].append(tmpPanel)

	# Offline Devices table with links

	with open(os.path.abspath(pathname)+"/conf/tabletemplate.json") as json_template:
		tmpPanel = json.load(json_template)

	tmpPanel['gridPos']['h'] = 12
	tmpPanel['gridPos']['w'] = 7
	tmpPanel['gridPos']['x'] = 17
	tmpPanel['gridPos']['y'] = 0
	tmpPanel['targets'][0]['rawSql']="SELECT devicename, deviceurl\nFROM mnode\nWHERE org_id='"+str(orgId)+"' AND devStatus='offline'"

	dashboard['panels'].append(tmpPanel)

	orgFileName = orgName.replace(" ","_")
	with open(os.path.abspath(pathname)+'/conf/dashboard_'+orgFileName+'.json', 'w') as outfile:
		json.dump(dashboard, outfile)


print("Pulling orgs...")
orgJson=json.loads(apiObj.sendGet(apiAction))

for org in orgJson:
	mOrganization = mnode.mOrg(org["id"],org["name"].strip(),org["url"])
	print("Pulling device status on " + str(mOrganization.organization_id))

	# org[] holds the following string:
	# {u'url': u'https://n174.meraki.com/o/sXoAMa/manage/organization/overview', u'id': u'ORGID', u'name': u'NAME '}
	apiAction = "organizations/"+str(mOrganization.organization_id)+"/deviceStatuses"
	devStatus = json.loads(apiObj.sendGet(apiAction))
	totalDevices = len(devStatus)
	orgChange = False
	orgExists = False
	deviceChange = False
	deviceFound = False

	# Check to see if this org is in the orgs table
	sqlOrgCheck = "SELECT * FROM mnode_org"
	result = dbObj.execSQL(sqlOrgCheck)
	for r in result:
		print ("Checking Org " + str(r[2]) + " - " + str(r[3]))
		if(r[2]==str(mOrganization.organization_id)):
			orgExists = True
			if(r[3].strip()!=org["name"].strip()):
				orgChange=True
				print ("Org changed!")
			if(r[5]!=totalDevices):
				orgChange=True
				print ("Org changed!")
			print ("Org Found!")
			break
	# If no - add it, if yes:
	    # Check if the details are still the same (org name, total devices, etc)
	if orgExists == False:
		orgChange = True
		sqlOrgAdd = "INSERT INTO mnode_org (dateCreated, organization_id, organization_name, organization_url, totalDevices) \
VALUES ("+str(time.time())+", "+str(mOrganization.organization_id)+", '"+mOrganization.organization_name.strip()+"', '"+mOrganization.organization_url+"', "+str(totalDevices)+")"
		dbObj.execSQL(sqlOrgAdd)
	else:
		# Update if changed
		if(orgChange == True):
			sqlUpdateOrg = "UPDATE mnode_org SET organization_name='"+mOrganization.organization_name.strip()+"', totalDevices="+str(totalDevices)+" WHERE organization_id="+str(mOrganization.organization_id)
			dbObj.execSQL(sqlUpdateOrg)
	# Any changes above should result in orgChange = True

		"""
		CREATE TABLE mnode (
		id SERIAL PRIMARY KEY,
		dateCreated integer,
		org_id varchar(64),
		macAddr varchar(32),
		deviceName varchar(64),
		deviceModel varchar(32),
		deviceSerial varchar(16),
		deviceNetwork varchar(64),
		deviceUrl varchar
		);
		"""
	for device in devStatus:
		deviceChange = False
		# Check to see if this node is in the mnode table
		sqlDev = "SELECT * FROM mnode"
		result = dbObj.execSQL(sqlDev)
		for r in result:
			if str(r[6]) == device["serial"]:
				# Found it!
				deviceFound = True
				break
		# If no - add it, if yes:
		if deviceFound == False:
			print("Dev not found "+device["serial"])
			# https://n174.meraki.com/o/sXoAMa/manage/organization/overview#t=device&q=Q2HP-Q2CM-K3F7
			orgUrl = mOrganization.organization_url
			deviceUrl = "<a href="+orgUrl+"#t=device&q=" + device["serial"]+" target=\"_blank\">"+device["serial"]+"</a>"
			devName = device["name"]

			if isinstance(devName, type(None))==True:
				devName="(No Name)"
			devName = devName.replace("'","")
			#print(str(time.time())+", "+str(mOrganization.organization_id)+", '"+device["mac"]+"', '"+devName+"', 'unknown', '"+device["serial"]+"', '"+device["networkId"]+"', '"+deviceUrl+"', '"+device["status"]+"'")
			sqlDevAdd = "INSERT INTO mnode (dateCreated, org_id, macAddr, deviceName, deviceModel, deviceSerial, deviceNetwork, deviceUrl, devStatus) VALUES ("+str(time.time())+", '"+str(mOrganization.organization_id)+"', '"+device["mac"]+"', '"+devName+"', 'unknown', '"+device["serial"]+"', '"+device["networkId"]+"', '"+deviceUrl+"', '"+device["status"]+"')"
			result=dbObj.execSQL(sqlDevAdd)
			print(result)
            # Check if the details are still the same (dev name, link, etc)

        # Any changes above should result in deviceChange = True
        # If deviceChange = True, update the database

		print("Org ID: " + str(mOrganization.organization_id) + " Device status - " + device["status"])
		if("online" in device["status"].lower()):
			numOnline += 1
		elif("offline" in device["status"].lower()):
			numOffline += 1
		else:
			numAlerting += 1


	sql="INSERT INTO mnode_stats (dateCreated, org_id, organization_name, numOnline, numAlerting, numOffline) \
	VALUES ("+str(time.time())+", '"+str(mOrganization.organization_id)+"', '"+mOrganization.organization_name+"', "+str(numOnline)+", "+str(numAlerting)+", "+str(numOffline)+")"
	result=dbObj.execSQL(sql)


	numOnline=0
	numOffline=0
	# If orgChange = True, rebuild the dashboard.json files in conf/
	if orgChange == True or orgExists == False:
		print("BUILDING GRAFANA")
		buildDashboards(mOrganization.organization_name,mOrganization.organization_id, totalDevices)
		# Put the json files in /var/lib
		os.system('sudo mkdir -p /var/lib/grafana/dashboards')
		os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/dashboard_*.json /var/lib/grafana/dashboards/')
		os.system('sudo chown -hR grafana:grafana /var/lib/grafana/')
		os.system('sudo systemctl restart grafana-server')
