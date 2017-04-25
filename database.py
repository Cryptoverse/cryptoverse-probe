import os
import sqlite3
import json

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
			# TODO: Remove this print.
			print 'one already exists'
			return
		
		cursor.execute('INSERT INTO star_logs VALUES (?, ?, ?, ?, ?)', (starLogJson['hash'], starLogJson['previous_hash'], starLogJson['height'], starLogJson['time'], json.dumps(starLogJson)))
		connection.commit()
		# t = ('RHAT',)
		# c.execute('SELECT * FROM stocks WHERE symbol=?', t)
		# print c.fetchone()

		# # Larger example that inserts many records at a time
		# purchases = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
		# 			('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
		# 			('2006-04-06', 'SELL', 'IBM', 500, 53.00),
		# 			]
		# c.executemany('INSERT INTO stocks VALUES (?,?,?,?,?)', purchases)
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