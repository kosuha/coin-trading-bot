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
test_end_date = "20210101" # "20210201"/None (None으로 하면 현재까지)
start_money = 100000.0
test_money = start_money
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.001
coin = "KRW-XRP"
K = 0.5

print("------------------------------- Test Start -------------------------------")

# 데이터 분석을 위한 테이터 가져오기
def get_data():
    date = test_end_date
    dfs = [ ]

    if test_length > 200:
        loop_num = test_length // 200
        remainder = test_length % 200
        for i in range(loop_num):
            df = pyupbit.get_ohlcv(coin, interval=test_data_interval, to=date, count=200)
            dfs.append(df)
            date = df.index[0]
            time.sleep(0.1)
        df = pyupbit.get_ohlcv(coin, interval=test_data_interval, to=date, count=remainder)
        dfs.append(df)
        
    else:
        df = pyupbit.get_ohlcv(coin, interval=test_data_interval, to=date, count=test_length)
        dfs.append(df)

    df = pd.concat(dfs).sort_index()
    return df

# 레리 윌리엄스의 변동성 돌파 전략, K값에 따른 수익률
def larry_ror(df_, k):
    
    df = df_

    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['bull'] = df['open'] > df['ma5']
    df['range'] = (df['high'] - df['low']) * k
    df['range_shift1'] = df['range'].shift(1)
    df['target'] = df['open'] + df['range'].shift(1)
    df['ror'] = np.where((df['high'] > df['target']) & df['bull'], df['close'] / df['target'] - (fee + fee + slippage), 1)
    df['hpr'] = df['ror'].cumprod()
    ror = df['hpr'][-2]

    # file_name = "excels/larry_{}_{}_k{}.xlsx".format(test_length, test_data_interval, k)
    # df.to_excel(file_name)

    return ror

data = get_data()

# K값에 따른 수익률이 높은 순서대로 리스트에 정렬하여 출력
ror_list = []
check_K = []
for k in np.arange(0.000, 1.000, 0.001):
    ror = larry_ror(data, k)
    ror_list.append([round(k, 5), round((ror - 1) * 100, 2)])
    if k == K:
        check_K.append([round(k, 5), round((ror - 1) * 100, 2)])

ror_list.sort(key = lambda x:x[1])

for i in ror_list:
    print("- K: ", i[0], " / 수익률: ", i[1], "%")

# 테스트 결과 출력
print("\n")
print("Interval: ", test_data_interval)
print("테스트시작: ", data.index[0])
print("테스트종료: ", data.index[len(data)-1])
print("시작가: ", data.close[0])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.close[0]) / data.close[0])*100, 3), "%")
print("프로그램 최고 수익률: ", ror_list[len(ror_list) - 1][1], "%", "/ K =", ror_list[len(ror_list) - 1][0])
print("K 값 수익률: ", check_K[0][1], "%", "/ K =", check_K[0][0])
print("-------------------------------  Test End  -------------------------------")
