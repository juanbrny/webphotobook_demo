
# temporary
dbtype='sqlite3'

if dbtype == 'sqlite3':
  import sqlite3
  connection = sqlite3.connect('database.db')
#else:
#  DROP DATABASE IF EXISTS photos;
#  CREATE DATABASE photos;
#  USE photos;

with open('static/schema.sql') as file:
    connection.executescript(file.read())

cursor = connection.cursor()

cursor.execute("INSERT INTO photos (title, description, url) VALUES (?, ?, ?)",
            ('Mountain Views', 'A sea of mountains', 'mountains.jpg')
            )

cursor.execute("INSERT INTO photos (title, description, url) VALUES (?, ?, ?)",
            ('Sandy Beach', 'The picture of a sandy beach', 'beach.jpg')
            )

connection.commit()
connection.close()
