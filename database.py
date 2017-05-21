import sys
from os import getenv
from os.path import dirname as directoryName, join as joinPaths
import sqlite3
import json
import util

databaseFileName = 'local.db'

if getattr(sys, 'frozen', False):
	applicationPath = directoryName(sys.executable)
elif __file__:
	applicationPath = directoryName(__file__)

databaseLocation = joinPaths(applicationPath, databaseFileName)

def commandHistoryLimit():
	return int(getenv('COMMAND_HISTORY', '100'))

def begin():
	connection = sqlite3.connect(databaseLocation)
	cursor = connection.cursor()
	return connection, cursor

def initialize(rebuild=False):
	connection, cursor = begin()
	try:
		if rebuild:
			cursor.execute('''DROP TABLE IF EXISTS star_logs''')
		cursor.execute('''CREATE TABLE IF NOT EXISTS star_logs (hash, previous_hash, height, time, json)''')
		cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (active, name, private_key, public_key)''')
		cursor.execute('''CREATE TABLE IF NOT EXISTS command_history (command, time, session_order)''')
		connection.commit()
	finally:
		connection.close()

def getCommand(index):
	connection, cursor = begin()
	try:
		result = cursor.execute('SELECT command FROM command_history ORDER BY time DESC, session_order DESC LIMIT 1 OFFSET ?', (index,)).fetchone()
		if result:
			return result[0]
		else:
			return None
	finally:
		connection.close()

def addCommand(command, time, order):
	if command is None or getCommand(0) == command:
		return
	connection, cursor = begin()
	try:
		cursor.execute('INSERT INTO command_history VALUES (?, ?, ?)', (command, time, order))
		if commandHistoryLimit() <= countCommands():
			deleteStart = cursor.execute('SELECT time FROM command_history ORDER BY time DESC, session_order DESC LIMIT 1 OFFSET ?', (commandHistoryLimit(),)).fetchone()[0]
			cursor.execute('DELETE FROM command_history WHERE time <= ?', (deleteStart,))
		connection.commit()
	finally:
		connection.close()

def countCommands():
	connection, cursor = begin()
	try:
		return cursor.execute('SELECT COUNT(*) FROM command_history').fetchone()[0]
	finally:
		connection.close()

def getAccount(name=None):
	connection, cursor = begin()
	try:
		result = None
		if name:
			result = cursor.execute('SELECT * FROM accounts WHERE name=?', (name,)).fetchone()
		else:
			result = cursor.execute('SELECT * FROM accounts WHERE active=1').fetchone()
		if result:
			return {
				'active': result[0] == 1,
				'name': result[1],
				'private_key': result[2],
				'public_key': result[3]
			}
		return None
	finally:
		connection.close()

def getAccounts():
	connection, cursor = begin()
	try:
		results = []
		fetched = cursor.execute('SELECT * FROM accounts').fetchall()
		if fetched:
			for account in fetched:
				results.append({
					'active': account[0] == 1,
					'name': account[1],
					'private_key': account[2],
					'public_key': account[3]
				})
		return results
	finally:
		connection.close()

def anyAccount(name):
	return getAccount(name) != None

def addAccount(accountJson):
	connection, cursor = begin()
	try:
		if cursor.execute('SELECT * FROM accounts WHERE name=?', (accountJson['name'],)).fetchone():
			return
		
		cursor.execute('INSERT INTO accounts VALUES (?, ?, ?, ?)', (0, accountJson['name'], accountJson['private_key'], accountJson['public_key']))
		connection.commit()
	finally:
		connection.close()

def setAccountActive(name):
	connection, cursor = begin()
	try:
		cursor.execute('UPDATE accounts SET active=0')
		cursor.execute('UPDATE accounts SET active=1 WHERE name=?', (name,))
		connection.commit()
	finally:
		connection.close()

def dropAccount(name):
	connection, cursor = begin()
	try:
		cursor.execute('DELETE FROM accounts WHERE name=?', (name,))
		connection.commit()
	finally:
		connection.close()

def dropAccounts():
	connection, cursor = begin()
	try:
		cursor.execute('DELETE FROM accounts')
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
					previousHash = currentParent['previous_hash']
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

def getStarLogHighestFromList(systemHashes):
	highest = None
	for currentHash in systemHashes:
		currentSystem = getStarLog(currentHash)
		if highest is None or highest['height'] < currentSystem['height']:
			highest = currentSystem
	return highest['hash']

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
		if previousHash == lowest['hash']:
			return True
		currentSystem = getStarLog(previousHash)
		if currentSystem['height'] <= lowest['height']:
			return False
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
				usedEvents.append(eventInput['key'])
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
					if eventOutput['star_system'] is None:
						eventOutput['star_system'] = system['hash']
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

def getFleets(fromStarLog=None):
	if fromStarLog is None:
		fromStarLog = getStarLogHighest()['hash']
	results = []
	while not util.isGenesisStarLog(fromStarLog):
		system = getStarLog(fromStarLog)
		for event in system['events']:
			for eventOutput in event['outputs']:
				if eventOutput['fleet_hash'] not in results:
					results.append(eventOutput['fleet_hash'])
		fromStarLog = system['previous_hash']
	return results