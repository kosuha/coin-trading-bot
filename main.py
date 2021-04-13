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
# print(upbit.get_balance("KRW-DOGE"))
# # 보유 현금 조회
# print(upbit.get_balance("KRW"))
# # 현재 가격
print("현재가: ", pyupbit.get_current_price("KRW-DOGE"))
# # 1분 단위로 시, 고, 저, 종, 거래량 데이터 count만큼 가져오기
# print(pyupbit.get_ohlcv("KRW-DOGE", interval="minute1", count=1))
 
isTest = True
testMoney = 50000.0
testCoin = 0.0
fee = 0.0005
coin = "KRW-DOGE"

# 이평선
def indicators():
    df = pyupbit.get_ohlcv(coin, interval="minute1", count=6)
    # print(df)
    sum = 0
    preSum = 0

    for i in range(1, 6):
        sum += df.close[i]

    for i in range(0, 5):
        preSum += df.close[i]

    return { 'now': sum / 5, 'pre': preSum / 5, 'lastClose': df.close[5] }


def checkBuy(indicators):
    if indicators['pre'] < indicators['now']:
        # print('## go up!')
        return True
    else:
        return False

def checkSell(indicators):
    if indicators['now'] > indicators['lastClose']:
        # print('## go down!')
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
            testCoin = (myMoney - (myMoney * fee)) / price
            print("자산 :", testMoney + (price * testCoin))
            print("현금: ", testMoney)
            print("코인: ", testCoin)
            print("매수가: ", price)
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
            print("자산 :", testMoney + (price * testCoin))
            print("현금: ", testMoney)
            print("코인: ", testCoin)
            print("매도가: ", price)
        else:
            print("실제 거래입니다.")

def trade():
    ma = indicators()
    price = pyupbit.get_current_price(coin)

    if checkBuy(ma):
        buy()
    elif checkSell(ma):
        sell()


schedule.every(5).seconds.do(trade)

while True:
    schedule.run_pending()
    time.sleep(1)