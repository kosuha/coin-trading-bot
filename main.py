import pyupbit
import time
from datetime import datetime
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

# 프로그램 값 설정
coin = "KRW-XRP"
currency = "KRW"
interval = "week"
fee = 0.05
k = 0.07442

print("\n")
print("########### START ###########")
print("coin : ", coin)
print("currency : ", currency)
print("interval : ", interval)
print("K : ", 0.07442)
print("\n")

# 코인 구매
def buy_coin():
    my_money = upbit.get_balance(currency)
    if my_money > 5000:
        buy_data = upbit.buy_market_order(coin, my_money - (my_money * fee))
        data_insert(buy_data)

# 코인 판매
def sell_coin():
    my_coin = upbit.get_balance(coin)
    if my_coin > 0:
        sell_data = upbit.sell_market_order(coin, my_coin)
        data_insert(sell_data)

# 목표가 설정
def get_target_price():
    df = pyupbit.get_ohlcv(coin, interval=interval, count=5)
    last_week = df.iloc[-2]

    this_week_open = last_week['close']
    last_week_high = last_week['high']
    last_week_low = last_week['low']
    target = this_week_open + (last_week_high - last_week_low) * k
    print("매수 목표가 : ", target)
    return target

# 오늘의 요일을 출력, 0 = 월요일
def today_weekday():
    return datetime.today().weekday()

# 5이동평균값 구하기
def get_last_week_ma5():
    df = pyupbit.get_ohlcv(coin, interval=interval, count=10)
    close = df['close']
    ma = close.rolling(window=5).mean()

    return ma[-2]

# DB에 거래정보 입력
def data_insert(data):
    print(data)
    current_price = pyupbit.get_current_price(coin)
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    total = my_money + (current_price * my_coin)

    df = pd.DataFrame({
        "side": data['side'],
        "price": float(data['price']) / my_coin,
        "volume": my_coin,
        "fee": float(data['price']) * fee,
        "total": total,
        "money": my_money,
        "coin": my_coin,
        "market": data['market'],
        "date": data['created_at']
         }, index=[0])
    
    df.to_sql(name='transaction_history', con=engine, if_exists='append', index=False)

# 프로그램 실행 시 목표가와 이동평균값 계산
target_price = get_target_price()
ma5 = get_last_week_ma5()

# 실행
while True:
    try:
        if today_weekday() == 0:
            now_time = int(time.strftime('%H%M%S'))
            if 90000 < now_time < 90010:
                sell_coin()
                target_price = get_target_price()
                ma5 = get_last_week_ma5()

        current_price = pyupbit.get_current_price(coin)

        if (current_price > target_price) and (current_price > ma5):
            buy_coin()
    except:
        print("########### ERROR ###########")

    time.sleep(1)