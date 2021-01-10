# this script is for debugging only!!!!
# data53

import database

database.start_connection()

print("DUMP OF groups TABLE")
for row in database.execute("select * from groups").fetchall():
	print(row)
print("")

print("DUMP OF halfMember TABLE")
for row in database.execute("select * from halfMember").fetchall():
	print(row)
print("")
 
print("DUMP OF groups_halfMember TABLE")
for row in database.execute("select * from groups_halfMember").fetchall():
	print(row)
print("")
	
database.stop_connection()


