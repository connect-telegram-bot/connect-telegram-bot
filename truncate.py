# this script is for debugging only!!!!

import database

x = input("are you sure you want to clean your database? THIS ACTION IS IRREVERSIVBLE[y][n]> ")

if x == 'n':
	exit()

database.start_connection()

database.execute("delete from groups")
database.execute("delete from halfMember")

database.stop_connection()


