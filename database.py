import os
import sqlite3
import json
import util

databaseFileName = 'local.db'

def begin():
	connection = sqlite3.connect(databaseFileName)
	cursor = connection.cursor()
	return connection, cursor

def initialize(rebuild=False):
	exists = os.path.isfile(databaseFileName)
	if rebuild and exists:
		os.remove(databaseFileName)
		exists = False
	if exists:
		return
	
	connection, cursor = begin()
	try:
		cursor.execute('''CREATE TABLE star_logs (hash, previous_hash, height, time, json)''')
		connection.commit()
	finally:
		connection.close()

def addStarLog(starLogJson):
	connection, cursor = begin()
	try:
		if cursor.execute('SELECT * FROM star_logs WHERE hash=?', (starLogJson['hash'],)).fetchone():
			return
		
		cursor.execute('INSERT INTO star_logs VALUES (?, ?, ?, ?, ?)', (starLogJson['hash'], starLogJson['previous_hash'], starLogJson['height'], starLogJson['time'], json.dumps(starLogJson)))
		connection.commit()
	finally:
		connection.close()

def getStarLogLatest():
	connection, cursor = begin()
	try:
		result = cursor.execute('SELECT json FROM star_logs ORDER BY time DESC').fetchone()
		return None if result is None else json.loads(result[0])
	finally:
		connection.close()

def getStarLogHighest():
	connection, cursor = begin()
	try:
		result = cursor.execute('SELECT json FROM star_logs ORDER BY height DESC').fetchone()
		return None if result is None else json.loads(result[0])
	finally:
		connection.close()

def getStarLog(systemHash):
	connection, cursor = begin()
	try:
		result = cursor.execute('SELECT json FROM star_logs WHERE hash=?', (systemHash,)).fetchone()
		return None if result is None else json.loads(result[0])
	finally:
		connection.close()

def getStarLogsAtHight(height, limit):
	connection, cursor = begin()
	try:
		dbResults = cursor.execute('SELECT json FROM star_logs WHERE height=? LIMIT ?', (height, limit)).fetchall()
		results = []
		for result in dbResults:
			results.append(json.loads(result[0]))
		return results
	finally:
		connection.close()

def getStarLogHashes():
	connection, cursor = begin()
	try:
		fetched = cursor.execute('SELECT hash FROM star_logs').fetchall()
		hashes = []
		for entry in fetched:
			hashes.append(entry[0])
		return hashes
	finally:
		connection.close()

def getUnusedDeployments(fromStarLog=None, systemHash=None, fleetHash=None):
	connection, cursor = begin()
	try:
		if fromStarLog is None:
			fromStarLog = getStarLogHighest()['hash']
		usedEvents = []
		results = []
		while fromStarLog is not None and not util.isGenesisStarLog(fromStarLog):
			system = getStarLog(fromStarLog)
			for event in system['events']:
				if event['type'] not in util.shipEventTypes:
					continue
				for eventInput in event['inputs']:
					usedEvents.append(eventInput)
				for eventOutput in event['outputs']:
					if eventOutput['type'] in util.shipEventTypes and eventOutput['key'] not in usedEvents:
						if systemHash is not None and eventOutput['star_system'] != systemHash:
							continue
						if fleetHash is not None and eventOutput['fleet_hash'] != fleetHash:
							continue
						results.append(eventOutput)
			fromStarLog = system['previous_hash']
		return results
	finally:
		connection.close()