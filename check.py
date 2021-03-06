#!/usr/bin/env python
import sys
import os
import time
import json
import requests
from random import seed
from random import randint
pathname = os.path.dirname(sys.argv[0])
demoMode = None
outageMode = None
try:
	val = sys.argv[1]
	if val == "demo":
		demoMode = True
except:
	demoMode = False
try:
	val = sys.argv[2]
	if val == "outage":
		outageMode = True
except:
	outageMode = False

sys.path.append(os.path.abspath(os.path.abspath(pathname)+'/lib'))
import mnode

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

	targetTmpD= {
		"refId": "D",
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
		"rawSql": "SELECT\n  datecreated AS \"time\",\n  CONCAT(organization_name, ' Online Change') AS metric,\n  percdiff as \"Online Device Change\"\nFROM mnode_stats\nWHERE organization_name = '"+orgName.strip()+"'\nORDER BY 1,2",
		"hide": "true"
	}
	dashboard['panels'][0]['targets'][0]=targetTmpA
	dashboard['panels'][0]['targets'].append(targetTmpB)
	dashboard['panels'][0]['targets'].append(targetTmpC)
	dashboard['panels'][0]['targets'].append(targetTmpD)
	dashboard['panels'][0]['stack']="true"
	dashboard['panels'][0]['fill']=10
	dashboard['panels'][0]['aliasColors'] = {
		orgName+" Online": "green",
		orgName+" Alerting": "orange",
		orgName+" Offline": "red",
		orgName+" Online Change": "purple"
	}

	# Scale adjustment for large orgs
	if totalDev > 1000:
		dashboard['panels'][0]['yaxes'][0]['logBase']=2
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
					"D",
					"5m",
					"now"
					]
				},
				"reducer": {
				"params": [],
				"type": "last"
				},
				"type": "query"
				}
			],
			"executionErrorState": "alerting",
			"for": "5m",
			"frequency": "1m",
			"handler": 1,
			"message": orgName+" observed a change in online devices >15%!",
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
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][0]['color'] = "red"
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['value'] = str(round(totalDev/2))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['color'] = "orange"
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['value'] = str(totalDev-(round(totalDev*0.1)))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['color'] = "green"
	tmpPanel['options']['fieldOptions']['defaults']['title'] = ""
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
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][0]['color'] = "green"
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['value'] = str(round(totalDev*0.1))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['color'] = "orange"
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['value'] = str(round(totalDev/2))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['color'] = "red"
	tmpPanel['options']['fieldOptions']['defaults']['title']= ""
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
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][0]['color'] = "green"
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['value'] = str(round(totalDev*0.1))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][1]['color'] = "orange"
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['value'] = str(round(totalDev/2))
	tmpPanel['options']['fieldOptions']['defaults']['thresholds'][2]['color'] = "red"
	tmpPanel['options']['fieldOptions']['defaults']['title']= ""
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

def fuzzNodeData(fakeNum, orgNum, percOnline, percAlerting, percOffline):
	deviceStatusArray = []

	onlineTarget = int(round(fakeNum * percOnline))
	oTargetCounter = 0
	alertTarget = int(round(fakeNum * percAlerting))
	aTargetCounter = 0
	offlineTarget = int(round(fakeNum * percOffline))
	offTargetCounter = 0

	for x in range(fakeNum):
		seed(time.time())
		state = randint(0,100)
		if oTargetCounter <= onlineTarget:
			devState="online"
			oTargetCounter+=1
		elif aTargetCounter <= alertTarget:
			devState="alerting"
			aTargetCounter+=1
		elif offTargetCounter <= offlineTarget:
			devState="offline"
			offTargetCounter+=1

		# Randomize a few online devices to offline
		if (state > 95):
			# 5% chance to knock an online node down
			devState="offline"

		deviceStatusArray.append({
				"name": "Fake Node "+str(randint(1000,9999))+" "+str(x),
				"serial": "Q2XX-"+str(orgNum)+"-"+str(x),
				"mac": "00:11:22:33:44:55",
				"status": devState,
				"lanIp": "1.2.3.4",
				"publicIp": "123.123.123.1",
				"networkId": "N_24329156"
			})
	return deviceStatusArray

print("Pulling orgs...")
# Check for rebuild of dashboards
rebuild=False
try:
	f = open("./rebuild")
	# Do something with the file
	rebuild = True
	f.close()
	os.system("rm -f ./rebuild")
except IOError:
	rebuild = False
orgJson=None
# If demo mode, build out 3 fake orgs:
if demoMode==True:
	orgJson = [
		{
			"id": 1,
			"name": "Demo Org 1",
			"url": "https://dashboard.meraki.com/"
		},
		{
			"id": 2,
			"name": "Demo Org 2",
			"url": "https://dashboard.meraki.com/"
		},
		{
			"id": 3,
			"name": "Demo Org 3",
			"url": "https://dashboard.meraki.com/"
		},
		{
			"id": 4,
			"name": "Demo Org 4",
			"url": "https://dashboard.meraki.com/"
		},
		{
			"id": 5,
			"name": "Demo Org 5 - Large",
			"url": "https://dashboard.meraki.com/"
		}
	]
else:
	orgJson=json.loads(apiObj.sendGet(apiAction))

for org in orgJson:
	mOrganization = mnode.mOrg(org["id"],org["name"].strip(),org["url"])
	#print("Pulling device status on " + str(mOrganization.organization_id))
	devStatus = []
	# org[] holds the following string:
	# {u'url': u'https://n174.meraki.com/o/sXoAMa/manage/organization/overview', u'id': u'ORGID', u'name': u'NAME '}
	apiAction = "organizations/"+str(mOrganization.organization_id)+"/deviceStatuses"
	if demoMode==False:
		devStatus = json.loads(apiObj.sendGet(apiAction))
	# If demo mode, replace dev Status with a new object (~2500-5000 devices per 4 orgs)
	else:
		# Outage simulator (~8% chance)
		seed(time.time())
		outageChance = randint(0,100)
		if outageMode==True:
			outageChance=100
		orgHit = randint(1,5)
		onlineVariant = randint(80,100)
		alertVariant = randint(0, (100 - onlineVariant))
		offlineVariant = 100 - onlineVariant - alertVariant
		if(offlineVariant>0):
			offlineVariant = randint(0, 100 - onlineVariant - alertVariant)

		onlineVariant = onlineVariant / 100.00
		alertVariant = alertVariant / 100.00
		offlineVariant = offlineVariant / 100.00

		if mOrganization.organization_id==1:
			if outageChance > 92 and orgHit==1:
				print(colorize(mOrganization.organization_name + " simulated outage ","red")+ colorize(str(time.time()),"yellow"))
				devStatus=fuzzNodeData(100, 1, 0.0, 0.3, 0.7)
			else:
				devStatus=fuzzNodeData(100, 1, onlineVariant, alertVariant, offlineVariant)
		elif mOrganization.organization_id==2:
			if outageChance > 92 and orgHit==2:
				print(colorize(mOrganization.organization_name + " simulated outage ","red")+ colorize(str(time.time()),"yellow"))
				devStatus=fuzzNodeData(200, 2, 0.0, 0.3, 0.7)
			else:
				devStatus=fuzzNodeData(200, 2, onlineVariant, alertVariant, offlineVariant)
		elif mOrganization.organization_id==3:
			if outageChance > 92 and orgHit==3:
				print(colorize(mOrganization.organization_name + " simulated outage ","red")+ colorize(str(time.time()),"yellow"))
				devStatus=fuzzNodeData(300, 3, 0.0, 0.3, 0.7)
			else:
				devStatus=fuzzNodeData(300, 3, onlineVariant, alertVariant, offlineVariant)
		elif mOrganization.organization_id==4:
			if outageChance > 92 and orgHit==4:
				print(colorize(mOrganization.organization_name + " simulated outage ","red")+ colorize(str(time.time()),"yellow"))
				devStatus=fuzzNodeData(500, 4, 0.0, 0.3, 0.7)
			else:
				devStatus=fuzzNodeData(500, 4, onlineVariant, alertVariant, offlineVariant)
		elif mOrganization.organization_id==5:
			if outageChance > 92 and orgHit==5:
				devStatus=fuzzNodeData(2000, 5, 0.0, 0.3, 0.7)
			else:
				devStatus=fuzzNodeData(2000, 5, onlineVariant, alertVariant, offlineVariant)
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
			#print("Dev not found "+device["serial"])
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
			#print(result)
        # Check if the details are still the same (dev name, link, etc)
		else:
			devName = device["name"]
			orgUrl = mOrganization.organization_url
			deviceUrl = "<a href="+orgUrl+"#t=device&q=" + device["serial"]+" target=\"_blank\">"+device["serial"]+"</a>"
			if isinstance(devName, type(None))==True:
				devName="(No Name)"
			devName = devName.replace("'","")
			sqlDevUpdate = "UPDATE mnode SET \
			dateCreated = "+str(time.time())+", \
			org_id = '"+str(mOrganization.organization_id)+"', \
			macAddr = '"+device['mac']+"', \
			deviceName = '"+devName+"', \
			deviceModel = 'unknown', \
			deviceSerial = '"+device['serial']+"', \
			deviceNetwork = '"+device['networkId']+"', \
			deviceUrl = '"+deviceUrl+"', \
			devStatus = '"+device['status']+"'"
        # Any changes above should result in deviceChange = True
        # If deviceChange = True, update the database

		#print("Org ID: " + str(mOrganization.organization_id) + " Device status - " + device["status"])
		if("online" in device["status"].lower()):
			numOnline += 1
		elif("offline" in device["status"].lower()):
			numOffline += 1
		else:
			numAlerting += 1

	# Calculate rate of change
	lastRecord = "SELECT numonline from mnode_stats WHERE org_id = '"+str(mOrganization.organization_id)+"' ORDER BY id DESC LIMIT 1"
	lastRecordResult = dbObj.execSQL(lastRecord)
	lastOnline = 0
	try:
		lastOnline = int(lastRecordResult[0][0])
	except:
		lastOnline = 0
	#print("Last online: " + str(lastOnline) + " Current online: " + str(numOnline))
	#print("(lastOnline - numOnline) > ("+str(lastOnline)+" - " +str(numOnline)+" > "+ str(lastOnline-numOnline))
	#print("(lastOnline + numOnline) > ("+str(lastOnline)+" + " +str(numOnline)+" > "+ str(lastOnline+numOnline))
	percDiff = float(((lastOnline - numOnline) / ((lastOnline + numOnline)/2.00)) * 100.00)
	if(percDiff<0.00):
		percDiff = percDiff*(-1.00)
	#print("Percent diff: " + str(percDiff))
	sql="INSERT INTO mnode_stats (dateCreated, org_id, organization_name, numOnline, numAlerting, numOffline, percDiff) \
	VALUES ("+str(time.time())+", '"+str(mOrganization.organization_id)+"', '"+mOrganization.organization_name+"', "+str(numOnline)+", "+str(numAlerting)+", "+str(numOffline)+", "+str(percDiff)+")"
	result=dbObj.execSQL(sql)


	numOnline=0
	numOffline=0
	# If orgChange = True, rebuild the dashboard.json files in conf/
	if orgChange == True or orgExists == False or rebuild == True:
		print("BUILDING GRAFANA")
		buildDashboards(mOrganization.organization_name,mOrganization.organization_id, totalDevices)
		# Put the json files in /var/lib
		os.system('sudo mkdir -p /var/lib/grafana/dashboards')
		os.system('sudo cp -f '+os.path.abspath(pathname)+'/conf/dashboard_*.json /var/lib/grafana/dashboards/')
		os.system('sudo chown -hR grafana:grafana /var/lib/grafana/')
		os.system('sudo systemctl restart grafana-server')
