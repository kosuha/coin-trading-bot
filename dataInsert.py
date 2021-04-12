import pyupbit
import time
import schedule
import config.conn as pw
import config.upbitToken as token
import pandas as pd
import pymysql
from sqlalchemy import create_engine

# DB에 연결
db_connection = create_engine(pw.conn)
conn = db_connection.connect()

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# DB에 1분마다 거래소 데이터 입력
def dataInsert():
    df = pyupbit.get_ohlcv("KRW-DOGE", interval="minute1", count=1)
    df.to_sql(name='1_minute_data', con=db_connection, if_exists='append', index=False)
    print(df)

schedule.every(60).seconds.do(dataInsert) # 60초마다 실행

while True:
    schedule.run_pending()
    time.sleep(1)