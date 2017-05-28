import json
import sqlite3
import sys
from os import getenv
from os.path import dirname as directory_name, join as join_paths

import util

database_file_name = 'local.db'

if getattr(sys, 'frozen', False):
    application_path = directory_name(sys.executable)
elif __file__:
    application_path = directory_name(__file__)
else:
    raise RuntimeError("Can't find application location")

database_location = join_paths(application_path, database_file_name)


def command_history_limit():
    return int(getenv('COMMAND_HISTORY', '100'))


def begin():
    connection = sqlite3.connect(database_location)
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


def get_command(index):
    connection, cursor = begin()
    try:
        result = cursor.execute('SELECT command FROM command_history ORDER BY time DESC, session_order DESC LIMIT 1 OFFSET ?', (index,)).fetchone()
        if result:
            return result[0]
        else:
            return None
    finally:
        connection.close()


def add_command(command, time, order):
    if command is None or get_command(0) == command:
        return
    connection, cursor = begin()
    try:
        cursor.execute('INSERT INTO command_history VALUES (?, ?, ?)', (command, time, order))
        if command_history_limit() <= count_commands():
            delete_start = cursor.execute('SELECT time FROM command_history ORDER BY time DESC, session_order DESC LIMIT 1 OFFSET ?', (command_history_limit(),)).fetchone()[0]
            cursor.execute('DELETE FROM command_history WHERE time <= ?', (delete_start,))
        connection.commit()
    finally:
        connection.close()


def count_commands():
    connection, cursor = begin()
    try:
        return cursor.execute('SELECT COUNT(*) FROM command_history').fetchone()[0]
    finally:
        connection.close()


def get_account(name=None):
    connection, cursor = begin()
    try:
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


def get_accounts():
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


def any_account(name):
    return get_account(name) is not None


def add_account(account_json):
    connection, cursor = begin()
    try:
        if cursor.execute('SELECT * FROM accounts WHERE name=?', (account_json['name'],)).fetchone():
            return

        cursor.execute('INSERT INTO accounts VALUES (?, ?, ?, ?)', (0, account_json['name'], account_json['private_key'], account_json['public_key']))
        connection.commit()
    finally:
        connection.close()


def set_account_active(name):
    connection, cursor = begin()
    try:
        cursor.execute('UPDATE accounts SET active=0')
        cursor.execute('UPDATE accounts SET active=1 WHERE name=?', (name,))
        connection.commit()
    finally:
        connection.close()


def drop_account(name):
    connection, cursor = begin()
    try:
        cursor.execute('DELETE FROM accounts WHERE name=?', (name,))
        connection.commit()
    finally:
        connection.close()


def drop_accounts():
    connection, cursor = begin()
    try:
        cursor.execute('DELETE FROM accounts')
        connection.commit()
    finally:
        connection.close()


def add_star_log(star_log_json):
    connection, cursor = begin()
    try:
        if cursor.execute('SELECT * FROM star_logs WHERE hash=?', (star_log_json['hash'],)).fetchone():
            return

        values = (star_log_json['hash'], star_log_json['previous_hash'], star_log_json['height'], star_log_json['time'], json.dumps(star_log_json))
        cursor.execute('INSERT INTO star_logs VALUES (?, ?, ?, ?, ?)', values)
        connection.commit()
    finally:
        connection.close()


def get_star_log_latest():
    connection, cursor = begin()
    try:
        result = cursor.execute('SELECT json FROM star_logs ORDER BY time DESC').fetchone()
        return None if result is None else json.loads(result[0])
    finally:
        connection.close()


def get_star_log_children(system_hash):
    connection, cursor = begin()
    try:
        results = []
        children = cursor.execute('SELECT json FROM star_logs WHERE previous_hash=?', (system_hash,)).fetchall()
        for child in children:
            results.append(json.loads(child[0]))
        return results
    finally:
        connection.close()


def get_star_log_highest(system_hash=None):
    connection, cursor = begin()
    try:
        if system_hash:
            target_system = get_star_log(system_hash)
            if target_system is None:
                return None
            checked = []
            highest_child = None
            results = cursor.execute('SELECT hash, previous_hash, height, json FROM star_logs WHERE height > ? ORDER BY height DESC', (target_system['height'],)).fetchall()
            for entry in results:
                if entry[0] in checked:
                    continue
                checked.append(entry[0])
                previous_hash = entry[1]
                while previous_hash != system_hash:
                    current_parent = get_star_log(previous_hash)
                    if current_parent['hash'] in checked:
                        break
                    checked.append(current_parent['hash'])
                    if current_parent['height'] <= target_system['height']:
                        break
                    previous_hash = current_parent['previous_hash']
                if previous_hash == system_hash:
                    highest_child = json.loads(entry[3])
                    break
            return target_system if highest_child is None else highest_child
        else:
            result = cursor.execute('SELECT json FROM star_logs ORDER BY height DESC').fetchone()
            return None if result is None else json.loads(result[0])
    finally:
        connection.close()


def get_star_log(system_hash):
    connection, cursor = begin()
    try:
        result = cursor.execute('SELECT json FROM star_logs WHERE hash=?', (system_hash,)).fetchone()
        return None if result is None else json.loads(result[0])
    finally:
        connection.close()


def get_star_log_at_height(system_hash, height):
    connection, cursor = begin()
    try:
        db_result = cursor.execute('SELECT height, hash, previous_hash, json FROM star_logs WHERE hash=?', (system_hash,)).fetchone()
        if db_result is None:
            return None
        relative_height = db_result[0]
        if relative_height == height:
            return json.loads(db_result[3])
        decreasing = height < relative_height
        while db_result is not None and db_result[0] != height:
            if decreasing:
                if db_result[0] == 0:
                    return None
                db_result = cursor.execute('SELECT height, hash, previous_hash, json FROM star_logs WHERE hash=?', (db_result[2],)).fetchone()
            else:
                db_result = cursor.execute('SELECT height, hash, previous_hash, json FROM star_logs WHERE previous_hash=?', (db_result[1],)).fetchone()
        return None if db_result is None else json.loads(db_result[3])
    finally:
        connection.close()


def get_star_logs_at_height(height, limit):
    connection, cursor = begin()
    try:
        db_results = cursor.execute('SELECT json FROM star_logs WHERE height=? LIMIT ?', (height, limit)).fetchall()
        results = []
        for result in db_results:
            results.append(json.loads(result[0]))
        return results
    finally:
        connection.close()


def get_star_log_hashes(system_hash=None, from_highest=False):
    connection, cursor = begin()
    try:
        if from_highest:
            system_hash = get_star_log_highest()['hash']

        if system_hash:
            last_hash = system_hash if from_highest else get_star_log_highest(system_hash)['hash']
            results = []
            while not util.is_genesis_star_log(last_hash):
                results.append(last_hash)
                last_hash = get_star_log(last_hash)['previous_hash']
            return results
        else:
            fetched = cursor.execute('SELECT hash FROM star_logs').fetchall()
            results = []
            for entry in fetched:
                results.append(entry[0])
            return results
    finally:
        connection.close()


def get_star_log_highest_from_list(system_hashes):
    highest = None
    for current_hash in system_hashes:
        current_system = get_star_log(current_hash)
        if highest is None or highest['height'] < current_system['height']:
            highest = current_system
    return highest['hash']


def get_star_logs_share_chain(system_hashes):
    highest = None
    lowest = None
    for current_hash in system_hashes:
        current_system = get_star_log(current_hash)
        if highest is None or highest['height'] < current_system['height']:
            highest = current_system
        if lowest is None or current_system['height'] < lowest['height']:
            lowest = current_system
    if None in [highest, lowest]:
        return False
    previous_hash = highest['previous_hash']
    while not util.is_genesis_star_log(previous_hash):
        if previous_hash == lowest['hash']:
            return True
        current_system = get_star_log(previous_hash)
        if current_system['height'] <= lowest['height']:
            return False
        previous_hash = current_system['previous_hash']
    return False


def get_unused_events(from_star_log=None, system_hash=None, fleet_hash=None):
    if from_star_log is None:
        from_star_log = get_star_log_highest(system_hash)['hash']
    used_events = []
    results = []
    while not util.is_genesis_star_log(from_star_log):
        system = get_star_log(from_star_log)
        for event in system['events']:
            if event['type'] not in util.SHIP_EVENT_TYPES:
                continue
            for eventInput in event['inputs']:
                used_events.append(eventInput['key'])
            for eventOutput in event['outputs']:
                if eventOutput['type'] in util.SHIP_EVENT_TYPES and eventOutput['key'] not in used_events:
                    if system_hash is not None:
                        if eventOutput['star_system'] is None:
                            if from_star_log != system_hash:
                                continue
                        elif eventOutput['star_system'] != system_hash:
                            continue
                    if fleet_hash is not None and eventOutput['fleet_hash'] != fleet_hash:
                        continue
                    if eventOutput['star_system'] is None:
                        eventOutput['star_system'] = system['hash']
                    results.append(eventOutput)
        from_star_log = system['previous_hash']
    return results


def any_events_exist(events, from_star_log=None):
    if from_star_log is None:
        from_star_log = get_star_log_highest()['hash']
    while not util.is_genesis_star_log(from_star_log):
        system = get_star_log(from_star_log)
        for event in system['events']:
            for eventEntry in event['inputs'] + event['outputs']:
                if eventEntry['key'] in events:
                    return True
        from_star_log = system['previous_hash']
    return False


def any_events_used(events, from_star_log=None):
    if from_star_log is None:
        from_star_log = get_star_log_highest()['hash']
    while not util.is_genesis_star_log(from_star_log):
        system = get_star_log(from_star_log)
        for event in system['events']:
            for event_entry in event['inputs']:
                if event_entry['key'] in events:
                    return True
        from_star_log = system['previous_hash']
    return False


def get_fleets(from_star_log=None):
    if from_star_log is None:
        from_star_log = get_star_log_highest()['hash']
    results = []
    while not util.is_genesis_star_log(from_star_log):
        system = get_star_log(from_star_log)
        for event in system['events']:
            for event_output in event['outputs']:
                if event_output['fleet_hash'] not in results:
                    results.append(event_output['fleet_hash'])
        from_star_log = system['previous_hash']
    return results
