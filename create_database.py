import database
 
f = open("db.sql",'r')
data = f.read()
f.close()

database.start_connection()
database.executescript(data)
database.stop_connection()

print("[+] Database created!! filename: main.db")

