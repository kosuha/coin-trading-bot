import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 80
test_data_interval = "week" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
test_end_date = None # None으로 하면 현재까지
start_money = 100000.0
test_money = start_money
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.01
coin = "KRW-TRX"

print("------------------------------- Test Start -------------------------------")

def get_data():
    date = test_end_date
    dfs = [ ]

    if test_length > 200:
        loop_num = math.floor(test_length / 200)
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

def larry_ror(df_, k):
    
    df = df_
    df['range'] = (df['high'] - df['low']) * k
    df['range_shift1'] = df['range'].shift(1)
    df['target'] = df['open'] + df['range'].shift(1)
    df['ror'] = np.where(df['high'] > df['target'], df['close'] / df['target'] - (fee + fee + slippage), 1)
    df['hpr'] = df['ror'].cumprod()
    ror = df['hpr'][-2]

    # file_name = "excels/larry_{}_{}_k{}.xlsx".format(test_length, test_data_interval, k)
    # df.to_excel(file_name)

    return ror

data = get_data()

ror_list = []
for k in np.arange(0.01, 10.00, 0.01):
    ror = larry_ror(data, k)
    ror_list.append([round(k, 5), round((ror - 1) * 100, 2)])
    # print("- k: ", round(k, 5), " / 수익률: ", round((ror - 1) * 100, 2), " %")

ror_list.sort(key = lambda x:x[1])

for i in ror_list:
    print("- k: ", i[0], " / 수익률: ", i[1], " %")

print("\n")
print("Interval: ", test_data_interval)
print("테스트시작: ", data.index[0])
print("테스트종료: ", data.index[len(data)-1])
print("시작가: ", data.close[0])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.close[0]) / data.close[0])*100, 3), " %")
print("-------------------------------  Test End  -------------------------------")
