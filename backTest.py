import pyupbit
import time
import pandas as pd
import config.upbitToken as token
import numpy as np

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
testLength = 1 # 곱하기 ?
testDataInterval = "week" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month

startMoney = 100000.0
testMoney = startMoney
bougthPrice = 0;
testCoin = 0.0
fee = 0.0005
coin = "KRW-XRP"

print("------------------------------- Test Start -------------------------------")

def checkBuy(indicators):
    # 골든크로스, 데드크로스
    if indicators['now_5'] > indicators['now_20']:
        return True
    
    return False

def checkSell(indicators):
    # 골든크로스, 데드크로스
    if indicators['now_5'] <= indicators['now_20']:
        return True

    return False

# 이평선
def indicators(df):
    sum_5 = 0
    sum_10 = 0
    sum_20 = 0
    preSum_5 = 0
    prePreSum_5 = 0
    preSum_10 = 0
    volume_5 = 0

    for i in range(15, 20):
        volume_5 += df.volume[i]
    
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

    for i in range(13, 18):
        prePreSum_5 += df.close[i]

    bar_1 = df.close[19] - df.open[19] # 음수면 음봉 양수면 양봉
    bar_2 = df.close[18] - df.open[18]

    return { 'price': df.close[19] ,'now_5': sum_5 / 5, 'now_10': sum_10 / 10, 'now_20': sum_20 / 20, 'pre_5': preSum_5 / 5, 'pre_10': preSum_10 / 10, 'bar_1': bar_1, 'volume_5': volume_5 / 5, 'volume_1': df.volume[19] }

def buy(price):
    global testMoney, testCoin, bougthPrice
    if testMoney == 0:
        return 0
    
    testCoin = (testMoney - (testMoney * fee)) / (price * 1.005)
    testMoney = 0
    bougthPrice = price

def sell(price):
    global testMoney, testCoin
    if testCoin == 0:
        return 0

    testMoney = (testCoin * (price * 0.995)) - ((testCoin * (price * 0.995)) * fee)
    testCoin = 0

def trade(df):
    if df.empty:
        return 0

    ma = indicators(df)
    price = ma['price']

    if checkBuy(ma):
        buy(price)
    if checkSell(ma):
        sell(price)

    print("자산 :", testMoney + (price * testCoin))

def getData():
    date = None
    dfs = [ ]

    for i in range(testLength):
        df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date, count=4)
        dfs.append(df)

        date = df.index[0]
        time.sleep(0.1)

    df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date, count=1)
    dfs.append(df)

    df = pd.concat(dfs).sort_index()
    return df

def larryRor(df_, k):
    slippage = 0.0002
    df = df_
    df['range'] = (df['high'] - df['low']) * k
    df['range_shift1'] = df['range'].shift(1)
    df['target'] = df['open'] + df['range'].shift(1)
    df['ror'] = np.where(df['high'] > df['target'], df['close'] / df['target'] - (fee + fee + slippage), 1)
    df['hpr'] = df['ror'].cumprod()
    ror = df['hpr'][-2]

    # fileName = "excels/larry_{}_{}_k{}.xlsx".format(testLength, testDataInterval, k)
    # df.to_excel(fileName)

    return ror

data = getData()
# larryRor(data, 0.0245)
rorList = []
for k in np.arange(0.001, 1.000, 0.001):
    ror = larryRor(data, k)
    rorList.append([round(k, 5), round((ror - 1) * 100, 2)])
    # print("- k: ", round(k, 5), " / 수익률: ", round((ror - 1) * 100, 2), " %")

rorList.sort(key = lambda x:x[1])

for i in rorList:
    print("- k: ", i[0], " / 수익률: ", i[1], " %")

print("\n")
print("테스트시작: ", data.index[0])
print("테스트종료: ", data.index[len(data)-1])
print("시작가: ", data.close[0])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.close[0]) / data.close[0])*100, 3), " %")
print("-------------------------------  Test End  -------------------------------")

# data = getData()
# for i in range(0, (testLength * 100) - 20):
#     data20 = data.iloc[i:i+20]
#     trade(data20)

# total = testMoney + (data.close[len(data)-1] * testCoin)

# print("-----------------------------------------------------------------------")
# print("테스트시작: ", data.index[19])
# print("테스트종료: ", data.index[len(data)-1])
# print("시작가: ", data.close[19])
# print("종료가: ", data.close[len(data)-1])
# print("존버 시 수익률: ", ((data.close[len(data)-1] - data.close[19]) / data.close[19])*100, " %")
# print("프로그램 수익률: ", ((total - startMoney) / startMoney) * 100, " %")
# print("자산 :", testMoney + (data.close[len(data)-1] * testCoin))
# print("-----------------------------------------------------------------------")
