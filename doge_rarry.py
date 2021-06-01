import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 1
pre_length = 10
test_data_interval = "day" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
fee = 0.0005
slippage = 0.002
coin = "KRW-ETC"
currency = "KRW"

# 데이터 분석을 위한 테이터 가져오기
def get_data(date):
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

    print(df)

    df = pd.concat(dfs).sort_index()
    df = df.reset_index().rename(columns={"index": "date"})
    print(date)
    # print(df)
    return df

# 레리 윌리엄스의 변동성 돌파 전략, K값에 따른 수익률
def get_ror(date):
    df = get_data(date)
    k = 0.6

    # 지표 계산
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)

    df['range'] = (df['high'] - df['low']) * k
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

    return ror