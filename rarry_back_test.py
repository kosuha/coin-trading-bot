import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 24 * 60
pre_length = 40
test_data_interval = "minute60" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
test_end_date = None # "20210201"/None (None으로 하면 현재까지)
start_money = 1000000
test_money = start_money - 5000
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.002
coin = "KRW-ETH"
currency = "KRW"
K = 0.673
ma_interval = 5

print("------------------------------- Test Start -------------------------------")

# 데이터 분석을 위한 테이터 가져오기
def get_data():
    date = test_end_date
    dfs = [ ]
    length = test_length + pre_length

    if length > 200:
        loop_num = length // 200
        remainder = length % 200
        for i in range(loop_num):
            df = pyupbit.get_ohlcv(coin, interval=test_data_interval, to=date, count=200)
            dfs.append(df)
            date = df.index[0]
            time.sleep(0.1)
        df = pyupbit.get_ohlcv(coin, interval=test_data_interval, to=date, count=remainder)
        dfs.append(df)
        
    else:
        df = pyupbit.get_ohlcv(coin, interval=test_data_interval, to=date, count=length)
        dfs.append(df)

    df = pd.concat(dfs).sort_index()
    df = df.reset_index().rename(columns={"index": "date"})

    # print(df)
    return df

# 레리 윌리엄스의 변동성 돌파 전략, K값에 따른 수익률
def larry(df_, k, ma):
    df = df_

    # 지표 계산
    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['ma8'] = df['close'].rolling(window=8).mean().shift(1)
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)
    df['ma20'] = df['close'].rolling(window=20).mean().shift(1)
    df['ma40'] = df['close'].rolling(window=40).mean().shift(1)

    if k == None:
        df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])
        df['k'] = df['noise'].rolling(window=20).mean().shift(1)
    else:
        df['k'] = k

    df['range'] = (df['high'] - df['low']) * df['k']
    df['target'] = df['open'] + df['range'].shift(1)
    df['bull'] = df['open'] > df['ma10']

    df['ror'] = np.where((df['high'] > df['target']) & df['bull'],
                        df['close'] / df['target'] - (fee + fee + slippage),
                        1)
        
    df.loc[:df.index[pre_length], ['ror']] = 1

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    
    ror = round(df['hpr'][len(df) - 1], 2)
    mdd = round(df['dd'].max(), 2)

    # if k == K:
        # print(df)
        # file_name = "excels/larry_{}_{}_k{}.xlsx".format(test_length, test_data_interval, k)
        # df.to_excel(file_name)
    
    return [ror, mdd]

data = get_data()

rank = []
for k in np.arange(0, 1.0, 0.01):
    larry_result = larry(data, k, ma_interval)
    rank.append([larry_result[0], larry_result[1], round(k, 5), ma_interval])

rank.sort(key=lambda x:x[0])

for i in rank:
    print(i)

result = larry(data, K, ma_interval)

# 테스트 결과 출력
print("\n")
print("Start Money: ", format(round(start_money), ","), currency)
print("Interval: ", test_data_interval)
print("테스트 기간: ", test_length)
print("테스트 시작: ", data.date[pre_length])
print("테스트 종료: ", data.date[len(data)-1])
print("시작가: ", data.open[pre_length])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.open[pre_length]) / data.open[pre_length])*100, 3), "%")
print(f"프로그램 수익률: {round((result[0] - 1) * 100, 3)} % / MDD = {result[1]} %")
print("End Money: ", format(round(start_money + ((start_money - 5000) * (result[0] - 1))), ","), currency)
print("-------------------------------  Test End  -------------------------------")

