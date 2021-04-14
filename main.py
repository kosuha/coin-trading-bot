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

# # KRW-DOGE 조회
# print(upbit.get_balance("KRW-DOGE"))
# # 보유 현금 조회
# print(upbit.get_balance("KRW"))
# # 현재 가격
# print("현재가: ", pyupbit.get_current_price("KRW-XRP"))
# # 1분 단위로 시, 고, 저, 종, 거래량 데이터 count만큼 가져오기
# print(pyupbit.get_ohlcv("KRW-DOGE", interval="minute1", count=1))
 
isTest = True
testMoney = 100000.0
testCoin = 0.0
fee = 0.0005
coin = "KRW-XRP"
boughtPrice = 0;

print("현재가: ", pyupbit.get_current_price(coin))
print("시작시간: ", datetime.now())

# 이평선
def indicators(df):
    price = pyupbit.get_current_price(coin)
    # print(df)
    sum_5 = 0
    sum_10 = 0
    sum_20 = 0
    preSum_5 = 0
    preSum_10 = 0

    for i in range(15, 20):
        sum_5 += df.close[i]

    for i in range(10, 20):
        sum_10 += df.close[i]

    for i in range(0, 20):
        sum_20 += df.close[i]

    for i in range(14, 19):
        preSum_5 += df.close[i]

    for i in range(9, 19):
        preSum_10 += df.close[i]

    bar_1 = df.close[19] - df.open[19] # 음수면 음봉 양수면 양봉
    bar_2 = df.close[18] - df.open[18]

    return { 'price': price ,'now_5': sum_5 / 5, 'now_10': sum_10 / 10, 'now_20': sum_20 / 20, 'pre_5': preSum_5 / 5, 'pre_10': preSum_10 / 10 }


def checkBuy(indicators):
    if indicators['now_5'] < indicators['now_10'] and indicators['now_10'] < indicators['now_20'] and indicators['now_5'] > indicators['pre_5']:
        return True

    return False

def checkSell(indicators):
    if indicators['now_5'] < indicators['now_10'] and indicators['now_10'] < indicators['now_20'] and indicators['now_5'] < indicators['pre_5']:
        return True
    
    if indicators['now_5'] > indicators['now_10'] and indicators['now_10'] > indicators['now_20'] and indicators['now_5'] < indicators['pre_5']:
        return True

    return False

def buy():
    global testMoney, testCoin, boughtPrice
    price = pyupbit.get_current_price(coin)
    myMoney = 0
    myCoin = 0

    if isTest:
        myMoney = testMoney
        myCoin = testCoin
    else:
        myMoney = upbit.get_balance("KRW")
        myCoin = upbit.get_balance(coin)

    if myMoney > 0:
        print("## buy coin")
        if isTest:
            testMoney = 0
            testCoin = (myMoney - (myMoney * fee)) / price
            boughtPrice = price
            print("현재시간: ", datetime.now())
            print("자산 :", testMoney + (price * testCoin))
            print("현금: ", testMoney)
            print("코인: ", testCoin)
            print("매수가: ", boughtPrice)
            print("\n")
        else:
            print("실제 거래입니다.")

def sell():
    global testMoney, testCoin, boughtPrice
    price = pyupbit.get_current_price(coin)
    myMoney = 0
    myCoin = 0

    if isTest:
        myMoney = testMoney
        myCoin = testCoin
    else:
        myMoney = upbit.get_balance("KRW")
        myCoin = upbit.get_balance(coin)

    if myCoin > 0:
        print("## sell coin")
        if isTest:
            testMoney = (myCoin * price) - ((myCoin * price) * fee)
            testCoin = 0
            boughtPrice = 0
            print("현재시간: ", datetime.now())
            print("자산 :", testMoney + (price * testCoin))
            print("현금: ", testMoney)
            print("코인: ", testCoin)
            print("매도가: ", price)
            print("\n")
        else:
            print("실제 거래입니다.")

def trade():
    df = pyupbit.get_ohlcv(coin, interval="minute1", count=20)

    if df.empty:
        return 0

    ma = indicators(df)
    price = pyupbit.get_current_price(coin)

    if checkBuy(ma):
        buy()
    if checkSell(ma):
        sell()


schedule.every(5).seconds.do(trade)

while True:
    schedule.run_pending()
    time.sleep(1)