import pymysql
import config.conn as conn
import datetime

db = pymysql.Connect(
	host=conn.host,
	user=conn.user,
	password=conn.password,
	database=conn.database
)

def insert_data(balance, price):
	now = datetime.datetime.now()
	now_datetime = f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}"

	cursor = db.cursor()
	query = "INSERT INTO trade_history.history (date, balance, price) VALUES (%s, %s, %s)"
	data = (now_datetime, balance, price)
	cursor.execute(query, data)
	db.commit()