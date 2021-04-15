import pyupbit
import time
import pandas as pd
import config.upbitToken as token
import numpy as np

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
testLength = 40
testDataInterval = "week" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
testEndDate = None # None으로 하면 현재까지
startMoney = 100000.0
testMoney = startMoney
bougthPrice = 0;
testCoin = 0.0
fee = 0.0005
coin = "KRW-XRP"

print("------------------------------- Test Start -------------------------------")

def getData():
    date = testEndDate
    dfs = [ ]

    if testLength > 200:
        loopNum = round(testLength / 200)
        remainder = testLength % 200
        for i in range(loopNum):
            df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date, count=200)
            dfs.append(df)
            date = df.index[0]
            time.sleep(0.1)
        df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date, count=remainder)
        dfs.append(df)
        
    else:
        df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date, count=testLength)
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
print("Interval: ", testDataInterval)
print("테스트시작: ", data.index[0])
print("테스트종료: ", data.index[len(data)-1])
print("시작가: ", data.close[0])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.close[0]) / data.close[0])*100, 3), " %")
print("-------------------------------  Test End  -------------------------------")
