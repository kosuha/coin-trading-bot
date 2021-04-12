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
 
isTest = True
testMoney = 50000
testCoin = 0.0
fee = 0.05
coin = "KRW-DOGE"

# 이평선
def movingAverage():
    df = pyupbit.get_ohlcv(coin, interval="minute1", count=21)
    # print(df)
    sum = 0
    preSum = 0

    for i in range(15, 20):
        sum += df.open[i]

    ma_5 = sum/5

    for i in range(0, 15):
        sum += df.open[i]

    ma_20 = sum/20

    for i in range(16, 21):
        preSum += df.open[i]

    preMa_5 = preSum/5

    for i in range(1, 16):
        preSum += df.open[i]

    preMa_20 = preSum/20

    return {5: ma_5, 20: ma_20, 'pre_5': preMa_5, 'pre_20': preMa_20}

def checkGoldenCross(ma):
    if ma['pre_20'] >= ma['pre_5'] and ma[20] < ma[5]:
        print('## golden cross!')
        return True
    else:
        return False

def checkSell(ma):
    price = pyupbit.get_current_price(coin)
    if ma[5] > price:
        print('## go down!')
        return True
    else:
        return False

def buy():
    global testMoney, testCoin
    price = pyupbit.get_current_price(coin)
    myMoney = 0
    myCoin = 0

    if isTest:
        myMoney = testMoney
        myCoin = testCoin
    else:
        myMoney = upbit.get_balance("KRW")
        myCoin = upbit.get_balance("KRW-DOGE")

    if myMoney > 0:
        print("## buy coin\n")
        if isTest:
            testMoney = 0
            testCoin = price / (myMoney - (myMoney * fee))
        else:
            print("실제 거래입니다.")

def sell():
    global testMoney, testCoin
    price = pyupbit.get_current_price(coin)
    myMoney = 0
    myCoin = 0

    if isTest:
        myMoney = testMoney
        myCoin = testCoin
    else:
        myMoney = upbit.get_balance("KRW")
        myCoin = upbit.get_balance("KRW-DOGE")

    if myCoin > 0:
        print("## sell coin\n")
        if isTest:
            testMoney = (myCoin * price) - ((myCoin * price) * fee)
            testCoin = 0
        else:
            print("실제 거래입니다.")

def trade():
    ma = movingAverage()

    if isTest:
        print("현금: ", testMoney)
        print("코인: ", testCoin)
        print("자산 :", testMoney + (pyupbit.get_current_price(coin) * testCoin))
    else:
        print("실제거래입니다.")

    if checkGoldenCross(ma):
        buy()
    elif checkSell(ma):
        sell();

schedule.every(5).seconds.do(trade)

while True:
    schedule.run_pending()
    time.sleep(1)