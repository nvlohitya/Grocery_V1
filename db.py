import sqlite3

#Open database
conn = sqlite3.connect('database.db')

#Create table
try:
    conn.execute('''CREATE TABLE users 
                (userId integer primary key autoincrement,
  		password TEXT,
		email TEXT unique,
		firstName TEXT,
		lastName TEXT
		)''')
except:
    pass
try:
    conn.execute('''CREATE TABLE products
                (productId INTEGER primary key autoincrement,
		name TEXT,
		price REAL,
		description TEXT,
		image TEXT,
		stock INTEGER,
		categoryId INTEGER,
		FOREIGN KEY(categoryId) REFERENCES categories(categoryId)
		)''')
except:
    pass
try:
    conn.execute('''CREATE TABLE kart
		(userId Integer 
		productId INTEGER,
                quantity integer,
		FOREIGN KEY(userId) REFERENCES users(userId),
		FOREIGN KEY(productId) REFERENCES products(productId),
        PRIMARY KEY(userId,productId)
		)''')
except:
    pass

try:
    conn.execute('''CREATE TABLE categories
		(categoryId INTEGER PRIMARY KEY,
		name TEXT,
                image TEXT
		)''')
except:
    pass

try :
    conn.execute('''CREATE TABLE admins (
	adminId	INTEGER,
	password	TEXT,
	email	TEXT UNIQUE,
	firstname	TEXT,
	lastname	TEXT,
	PRIMARY KEY(adminId AUTOINCREMENT)
)''')
except:
    pass