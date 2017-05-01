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

def getStarLogChildren(systemHash):
	connection, cursor = begin()
	try:
		results = []
		children = cursor('SELECT json FROM star_logs WHERE previous_hash=?', (systemHash,)).fetchall()
		for child in children:
			results.append(json.loads(child[0]))
		return results
	finally:
		connection.close()

def getStarLogHighest(systemHash=None):
	connection, cursor = begin()
	try:
		if systemHash:
			targetSystem = getStarLog(systemHash)
			if targetSystem is None:
				return None
			checked = []
			highestChild = None
			results = cursor.execute('SELECT hash, previous_hash, height, json FROM star_logs WHERE height > ? ORDER BY height DESC', (targetSystem['height'],)).fetchall()
			for entry in results:
				if entry[0] in checked:
					continue
				checked.append(entry[0])
				previousHash = entry[1]
				while previousHash != systemHash:
					currentParent = getStarLog(previousHash)
					if currentParent['hash'] in checked:
						break
					checked.append(currentParent['hash'])
					if currentParent['height'] <= targetSystem['height']:
						break
					previousHash = currentParent['hash']
				if previousHash == systemHash:
					highestChild = json.loads(entry[3])
					break
			return targetSystem if highestChild is None else highestChild
		else:
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

def getStarLogHashes(systemHash=None, fromHighest=False):
	connection, cursor = begin()
	try:
		if fromHighest:
			systemHash = getStarLogHighest()['hash']

		if systemHash:
			lastHash = systemHash if fromHighest else getStarLogHighest(systemHash)['hash']
			results = []
			while not util.isGenesisStarLog(lastHash):
				results.append(lastHash)
				lastHash = getStarLog(lastHash)['previous_hash']
			return results
		else:
			fetched = cursor.execute('SELECT hash FROM star_logs').fetchall()
			results = []
			for entry in fetched:
				results.append(entry[0])
			return results
	finally:
		connection.close()

def getStarLogsShareChain(systemHashes):
	highest = None
	lowest = None
	for currentHash in systemHashes:
		currentSystem = getStarLog(currentHash)
		if highest is None or highest['height'] < currentSystem['height']:
			highest = currentSystem
		if lowest is None or currentSystem['height'] < lowest['height']:
			lowest = currentSystem
	if None in [highest, lowest]:
		return False
	previousHash = highest['previous_hash']
	while not util.isGenesisStarLog(previousHash):
		currentSystem = getStarLog(previousHash)
		if currentSystem['height'] <= lowest['height']:
			return False
		if currentSystem['previous_hash'] == lowest['hash']:
			return True
		previousHash = currentSystem['previous_hash']
	return False

def getUnusedEvents(fromStarLog=None, systemHash=None, fleetHash=None):
	if fromStarLog is None:
		fromStarLog = getStarLogHighest(systemHash)['hash']
	usedEvents = []
	results = []
	while not util.isGenesisStarLog(fromStarLog):
		system = getStarLog(fromStarLog)
		for event in system['events']:
			if event['type'] not in util.shipEventTypes:
				continue
			for eventInput in event['inputs']:
				usedEvents.append(eventInput)
			for eventOutput in event['outputs']:
				if eventOutput['type'] in util.shipEventTypes and eventOutput['key'] not in usedEvents:
					if systemHash is not None:
						if eventOutput['star_system'] is None:
							if fromStarLog != systemHash:
								continue
						elif eventOutput['star_system'] != systemHash:
							continue
					if fleetHash is not None and eventOutput['fleet_hash'] != fleetHash:
						continue
					results.append(eventOutput)
		fromStarLog = system['previous_hash']
	return results

def anyEventsExist(events, fromStarLog=None):
	if fromStarLog is None:
		fromStarLog = getStarLogHighest()['hash']
	while not util.isGenesisStarLog(fromStarLog):
		system = getStarLog(fromStarLog)
		for event in system['events']:
			for eventEntry in event['inputs'] + event['outputs']:
				if eventEntry['key'] in events:
					return True
		fromStarLog = system['previous_hash']
	return False

def anyEventsUsed(events, fromStarLog=None):
	if fromStarLog is None:
		fromStarLog = getStarLogHighest()['hash']
	while not util.isGenesisStarLog(fromStarLog):
		system = getStarLog(fromStarLog)
		for event in system['events']:
			for eventEntry in event['inputs']:
				if eventEntry['key'] in events:
					return True
		fromStarLog = system['previous_hash']
	return False