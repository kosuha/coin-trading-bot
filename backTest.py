import pyupbit
import time
import pandas as pd
import config.upbitToken as token

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
testLength = 1 # 곱하기 200, 2 이상
testDataInterval = "minute10"

startMoney = 100000.0
testMoney = startMoney
testCoin = 0.0
fee = 0.0005
coin = "KRW-XRP"

print("start test")

def checkBuy(indicators):
    if indicators['now_5'] < indicators['now_10'] and indicators['now_10'] < indicators['now_20'] and indicators['now_5'] > indicators['pre_5']:
        return True
        
    if indicators['now_5'] > indicators['now_10'] and indicators['now_10'] > indicators['now_20'] and indicators['pre_pre_5'] > indicators['pre_5'] and indicators['pre_5'] < indicators['now_5']:
        return True
    
    return False

def checkSell(indicators):
    if indicators['now_5'] < indicators['now_10'] and indicators['now_10'] < indicators['now_20'] and indicators['now_5'] < indicators['pre_5']:
        return True
    
    if indicators['now_5'] > indicators['now_10'] and indicators['now_10'] > indicators['now_20'] and indicators['now_5'] < indicators['pre_5']:
        return True

    return False

# 이평선
def indicators(df, nextDfClose):
    sum_5 = 0
    sum_10 = 0
    sum_20 = 0
    preSum_5 = 0
    prePreSum_5 = 0
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

    for i in range(13, 18):
        prePreSum_5 += df.close[i]

    bar_1 = df.close[19] - df.open[19] # 음수면 음봉 양수면 양봉
    bar_2 = df.close[18] - df.open[18]
    price = (df.close[19] + df.open[19]) / 2

    return { 'price': nextDfClose ,'now_5': sum_5 / 5, 'now_10': sum_10 / 10, 'now_20': sum_20 / 20, 'pre_5': preSum_5 / 5, 'pre_10': preSum_10 / 10, 'pre_pre_5': prePreSum_5 / 5 }

def buy(price):
    global testMoney, testCoin
    if testMoney == 0:
        return 0
    
    testCoin = (testMoney - (testMoney * fee)) / (price * 1.005)
    testMoney = 0

def sell(price):
    global testMoney, testCoin
    if testCoin == 0:
        return 0

    testMoney = (testCoin * (price * 0.995)) - ((testCoin * (price * 0.995)) * fee)
    testCoin = 0

def trade(df, nextDfClose):
    if df.empty:
        return 0

    ma = indicators(df, nextDfClose)
    price = ma['price']

    if checkBuy(ma):
        buy(price)
    if checkSell(ma):
        sell(price)

    # print("자산 :", testMoney + (price * testCoin))

def getData():
    date = None
    dfs = [ ]

    for i in range(testLength):
        df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date)
        dfs.append(df)

        date = df.index[0]
        time.sleep(0.1)

    df = pyupbit.get_ohlcv(coin, interval=testDataInterval, to=date, count=1)
    dfs.append(df)

    df = pd.concat(dfs).sort_index()
    print(df.index[len(df) - 1])
    print(df.volume[len(df) - 1])
    return df

data = getData()

for i in range(0, (testLength * 200) - 20):
    data20 = data.iloc[i:i+20]
    trade(data20, (data.iloc[i+20].close + data.iloc[i+20].open) / 2)

total = testMoney + (data.close[len(data)-1] * testCoin)

print("-----------------------------------------------------------------------")
print("테스트시작: ", data.index[19])
print("테스트종료: ", data.index[len(data)-1])
print("시작가: ", data.close[19])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", ((data.close[len(data)-1] - data.close[19]) / data.close[19])*100, " %")
print("프로그램 수익률: ", ((total - startMoney) / startMoney) * 100, " %")
print("자산 :", testMoney + (data.close[len(data)-1] * testCoin))
print("-----------------------------------------------------------------------")
