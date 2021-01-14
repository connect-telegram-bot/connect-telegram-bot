'''
if you want to execute sql codes in the database, use the following idiom:

	>>> import database
	>>> database.start_connection()
	>>> database.execute("insert into groups (id,name,short_id) values (990099,'aau_math2','abcde')")
	<sqlite3.Cursor object at 0x7f53f9c12810>
	>>> a = database.execute("select * from groups")
	>>> 
	>>> for row in a.fetchall():
	...     print(f"id: {row[0]} \t name: {row[1]}")
	... 
	id: 89222 	 name: family
	id: 990099 	 name: aau_math2
	>>> database.stop_connection()
	>>> 
	>>> exit()
'''

import sqlite3
import threading

DATABASE_NAME = "main.db" 
conn = None # connection
curr = None # cursor

lock = threading.Lock()

def start_connection():
	global conn,curr
	if (conn is None) and (curr is None):
		#isolation_level=None -> autocommit mode
		#check_same_thread = so that it is possible to share connection objects b/n threads.
		conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False, isolation_level=None)
		curr = conn.cursor()	
		curr.execute("PRAGMA foreign_keys=true")
	else:
		raise RuntimeError("database already connected!!") 

def execute(sql_code:str,parameters=None):
	data = None
	with lock:
		if parameters is None:
			data = curr.execute(sql_code)
		else:
			data = curr.execute(sql_code,parameters)
	return data	
	
def executescript(script:str):
	data = None
	with lock:
		data = curr.executescript(script)
	return data
		
	
def stop_connection():
	global conn,curr
	if conn is None:
		raise RuntimeError("trying to close a connection, that is not opened yet!")
	conn.commit()
	conn.close()
	conn = None
	curr = None


'''
beautiful command
PRAGMA foreign_keys=true;
'''
