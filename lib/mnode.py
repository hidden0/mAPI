#!/usr/bin/env python
# Function library not tied to any class Architecture
# Example: file manipulation, loading/creating list of meraki nodes etc
import fileinput
import sys
import os
"""
Class: mnode
Description: Defines a meraki device and provides access to it's data as well as functions to investigate the device.

Fields:
- MAC
- Serial Number
- Model
- Device Name

Methods:
+ deviceStatus()

"""

# Auto install dependencies
def install(package):
	try:
		__import__(package)
	except:
		import subprocess
		print("Detected " + package + " dependency missing. Installing to local user.")
		print("sudo pip install " + str(package))
		if package == "psycopg2":
			os.system('sudo pip install -q psycopg2-binary')
		else:
			os.system('sudo pip install -q ' + str(package))


# Dependency check
install('psycopg2')
install('requests')
install('configparser')
import psycopg2
import requests
from configparser import ConfigParser

class mAPI:
	api_key 		= ""
	addedHeaders 	= ""
	apiUrl			= "https://api.meraki.com/api/v0/"
	apiAction		= ""

	def __init__(self, key):
		self.api_key = key
		self.addedHeaders = {'X-Cisco-Meraki-API-Key': key, 'Content-Type': 'application/json'}

	def sendGet(self, action):
		try:
			# sending post request and saving response as response object
			r2 = requests.get(url = self.apiUrl+action, headers=self.addedHeaders)
			return r2.text
		except Exception as e:
			return str(e)

class mOrg:
	organization_id = 0
	organization_name = "Unknown"
	organization_url = ""
	def __init__(self, id, name, url):
		self.organization_id = id
		self.organization_name = name
		self.organization_url = url

class mnode:
	macAddr		= ""
	serialNum	= ""
	deviceModel	= ""
	deviceName	= ""
	deviceUrl	= ""
	networkName = ""

	# Constructor
	def __init__(self, serial):
		self.serialNum=serial

	# Set / Get Methods for mnode
	#### GET
	def getMacAddress(self):
		return self.macAddr
	def getSerial(self):
		return self.serialNum
	def getModel(self):
		return self.deviceModel
	def getName(self):
		return self.deviceName
	def getUrl(self):
		return self.deviceUrl
	def getNetworkName(self):
		return self.networkName
	#### SET
	def setMacAddress(self, val):
		self.macAddr = val
		return True
	def setSerial(self, val):
		self.serialNum = val
		return True
	def setModel(self, val):
		self.deviceModel = val
		return True
	def setName(self, val):
		self.deviceName = val
		return True
	def setUrl(self, val):
		self.deviceUrl = val
		return True
	def setNetworkName(self, val):
		self.networkName = val
		return True

	# Methods



class mNodeStorage:
	## Postgres stuff
	dbConn			= None	# Will handle the db connection state
	dbCursor		= None	# Handles the db cursor state
	dbConfig = "../conf/database.ini"
	dbConfigSection = "local"

	def __init__(self, config, section):
		self.dbConfig=config
		self.dbConfigSection=section

	def setDbHandlers(self, dbData):
		self.dbConn = dbData[0]
		self.dbCursor = dbData[1]

	# Open connection
	def openDB(self):
		# Connect to the PostgreSQL database server
		try:
			# create a parser
			parser = ConfigParser()
			# read config file
			parser.read(self.dbConfig)
			section = self.dbConfigSection
			filename = self.dbConfig
			# get section, default to postgresql
			# Check database exists first
			db = {}
			if parser.has_section(self.dbConfigSection):
				params = parser.items(self.dbConfigSection)
				for param in params:
					db[param[0]] = param[1]
			else:
				raise Exception('Section {0} not found in the {1} file'.format(section, filename))

			# create the connection
			self.dbConn = psycopg2.connect(**db)
			self.dbConn.set_isolation_level(0)
			# create a cursor
			self.dbCursor = self.dbConn.cursor()
			return 1
		except (Exception, psycopg2.DatabaseError) as error:
			theError = str(error)
			if(theError.find("does not exist")!=-1):
				# Database not found, create it!
				print(error)
				return 0

			print(error)
			return 0
		except Exception as e:
			return e

	# Close connection
	def closeDB(self):
		if(self.dbCursor is not None):
			self.dbCursor.close()
			return 1
		if(self.dbConn is not None):
			# save changes first
			self.dbConn.commit()
			self.dbConn.close()
			return 1

	# Execute SQL
	# Schema Example for tables:
		"""
		CREATE TABLE vendors (
			vendor_id SERIAL PRIMARY KEY,
			vendor_name VARCHAR(255) NOT NULL
		)
		"""
	def execSQL(self,sql):
		# Create a table
		if self.openDB() == 1:
			try:
				self.dbCursor.execute(sql)
				# What kind of query is it?
				if("select" in sql.lower()):
					# fetch all and return
					return self.dbCursor.fetchall()
				elif("insert" in sql.lower()):
					# return new ID
					self.dbCursor.execute('SELECT LASTVAL()')
					lastid = self.dbCursor.fetchone()[0]
					return lastid
			except Exception as e:
				return e
			self.closeDB()
			return 1
		return 0

	def checkTable(self,tblName):
		rows = None
		"""
		SELECT
		   *
		FROM
		   pg_catalog.pg_tables
		WHERE
		   schemaname != 'pg_catalog'
		AND schemaname != 'information_schema';
		"""
		sql="SELECT * FROM pg_catalog.pg_tables WHERE tablename = '"+tblName+"'"
		if self.openDB() == 1:
			try:
				self.dbCursor.execute(sql)
				rows=self.dbCursor.fetchall()
			except:
				return 0
			self.closeDB()
		if isinstance(rows, type(None))==False:
			if(len(rows)>0):
				return True
			else:
				return False
		else:
			return False
