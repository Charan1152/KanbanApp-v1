import sqlite3

con = sqlite3.connect('database.sqlite3')
cur = con.cursor()
cur.execute('SELECT * FROM LISTS;')
for row in cur:
    print(row)
con.close()
