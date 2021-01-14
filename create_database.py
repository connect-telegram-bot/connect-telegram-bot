import database
from password_generator import short_id_generator
 
f = open("db.sql",'r')
data = f.read()
f.close()

database.start_connection()
database.executescript(data)
database.stop_connection()

print("[+] Database created!! filename: main.db")

