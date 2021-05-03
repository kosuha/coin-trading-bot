import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 1000
test_data_interval = "day" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
test_end_date = "20201103" # "20210201"/None (None으로 하면 현재까지)
start_money = 1000000
test_money = start_money - 5000
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.0015
coin = "KRW-XRP"
currency = "KRW"
K = 0.5
ma_interval = 6

print("------------------------------- Test Start -------------------------------")

# 데이터 분석을 위한 테이터 가져오기
def get_data():
    date = test_end_date
    dfs = [ ]
    length = test_length + ma_interval

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
    return df

# 레리 윌리엄스의 변동성 돌파 전략, K값에 따른 수익률
def larry(df_, k, ma):
    df = df_

    df['ma5'] = df['close'].rolling(window=ma).mean().shift(1)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)
    df['bull'] = df['open'] > df['ma5']

    df['ror'] = np.where((df['high'] > df['target']) & df['bull'],
                        df['close'] / df['target'] - (fee + fee + slippage),
                        1)

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    
    ror = round(df['hpr'][-2], 2)
    mdd = round(df['dd'].max(), 2)

    # if k == K:
        # print(df)
        # file_name = "excels/larry_{}_{}_k{}.xlsx".format(test_length, test_data_interval, k)
        # df.to_excel(file_name)
    
    return [ror, mdd]

data = get_data()

rank = []
for k in np.arange(0, 1.0, 0.1):
    for ma in np.arange(2, 10, 1):
        larry_result = larry(data, k, ma)
        rank.append([larry_result[0], larry_result[1], round(k, 2), ma])

rank.sort(key=lambda x:x[0])

for i in rank:
    print(i)

result = larry(data, K, ma_interval)

# 테스트 결과 출력
print("\n")
print("Start Money: ", format(round(start_money), ","), currency)
print("Interval: ", test_data_interval)
print("테스트 기간: ", test_length)
print("테스트 시작: ", data.index[ma_interval])
print("테스트 종료: ", data.index[len(data)-1])
print("시작가: ", data.open[ma_interval])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.open[ma_interval]) / data.open[ma_interval])*100, 3), "%")
print(f"프로그램 수익률: {round((result[0] - 1) * 100, 2)} % / MDD = {result[1]} %")
print("End Money: ", format(round(start_money + ((start_money - 5000) * (result[0] - 1))), ","), currency)
print("-------------------------------  Test End  -------------------------------")

