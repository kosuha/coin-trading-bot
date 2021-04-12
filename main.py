import pyupbit
import time
import schedule
import config.conn as pw
import config.upbitToken as token
import pandas as pd
import pymysql
from sqlalchemy import create_engine

# DB에 연결
engine = create_engine(pw.conn)
conn = engine.connect()

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# # KRW-DOGE 조회
# print(upbit.get_balance("KRW-DOGE")
# # 보유 현금 조회
# print(upbit.get_balance("KRW"))
# # 현재 가격
# print(pyupbit.get_current_price("KRW-DOGE"))
# # 1분 단위로 시, 고, 저, 종, 거래량 데이터 count만큼 가져오기
# print(pyupbit.get_ohlcv("KRW-DOGE", interval="minute1", count=1))

# 이평선
def ma():
    sql = 'SELECT * FROM 1_minute_data ORDER BY date DESC LIMIT 20;'
    df = pd.read_sql(sql, con=engine)   
    print(df)
    ma_5 = 0
    ma_20 = 0

    if len(df) == 20:
        sum = 0
        for i in range(0, 5):
            sum += df.open[i]
        ma_5 = sum/5
        for i in range(5, 20):
            sum += df.open[i]
        ma_20 = sum/20
        return {5: ma_5, 20: ma_20}

    return None


# # 1초마다 실행
# schedule.every(1).second.do()

# while True:
#     schedule.run_pending()
#     time.sleep(1)
