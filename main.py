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

print(upbit.get_balance("KRW-DOGE"))     # KRW-DOGE 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회
print(pyupbit.get_current_price("KRW-DOGE"))        # 현재 가격
print(pyupbit.get_ohlcv("KRW-DOGE", interval="minute1", count=1))        # 1분 단위로 시, 고, 저, 종, 거래량 데이터 count만큼 가져오기

# DB에 1분마다 거래소 데이터 입력
def dataInsert():
    df = pyupbit.get_ohlcv("KRW-DOGE", interval="minute1", count=1)
    df.to_sql(name='1_minute_data', con=db_connection, if_exists='append', index=False)
    print(df)


schedule.every(60).second.do(dataInsert) # 60초마다 실행
schedule.every(1).second.do(dataInsert) # 1초마다 실행

while True:
    schedule.run_pending()
    time.sleep(1)
