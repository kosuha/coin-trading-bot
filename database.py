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
	now_datetime = f"{now.year}-{format(now.month, '02')}-{format(now.day, '02')} {format(now.hour, '02')}:{format(now.minute, '02')}"

	cursor = db.cursor()
	query = "INSERT INTO history (date, balance, price) VALUES(%s, %s, %s)"
	data = (now_datetime, balance, price)
	cursor.execute(query, data)
	db.commit()