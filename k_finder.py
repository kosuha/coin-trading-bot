import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

test_length = 7
fee = 0.0005
slippage = 0.002
coin = "KRW-BTT"
test_data_interval = "day" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month

# 데이터 분석을 위한 테이터 가져오기
def get_data_k(test_end_date):
    date = test_end_date
    dfs = [ ]
    length = test_length + 20

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

    # 지표 계산
    df['ma'] = df['close'].rolling(window=ma).mean().shift(1)
    df['bull'] = df['open'] > df['ma']
    df['range'] = (df['high'] - df['low']) * k
    df['range_shift1'] = df['range'].shift(1)
    df['target'] = df['open'] + df['range'].shift(1)
    df['sell_condition'] = np.where(df['bull'] == False, True, False)
    df['buy_condition'] = np.where((df['high'] > df['target']) & (df['open'] > df['ma']), True, False)

    df.loc[:df.index[20], ['sell_condition', 'buy_condition']] = False
    
    # 코인을 보유한 상태인지 나타냄
    bought_status = False
    for i in df.index:
        if df.loc[i, 'buy_condition']:
            bought_status = True
        if df.loc[i, 'sell_condition']:
            bought_status = False
        df.loc[i, 'bought'] = bought_status

    # 코인을 사고 팔때만 수수료가 포함된 수익률 계산
    df['bought_shift1'] = df['bought'].shift(1)
    df['bought_shift1'].fillna(False, inplace = True)
    df['ror'] = np.where(df['bought'] == True, df['close'] / df['open'], 1)
    df['ror'] = np.where((df['bought'] == True) & (df['bought_shift1'] == False), df['close'] / df['target'] - (fee + slippage), df['ror'])
    df['ror'] = np.where((df['bought'] == False) & (df['bought_shift1'] == True), 1 - (fee + slippage), df['ror'])

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    ror = df['hpr'][-1]
    mdd = round(df['dd'].max(), 2)
    
    return [ror, mdd]

def finder(test_end_date):
    data = get_data_k(test_end_date)

    rank = []
    for k in np.arange(0, 1.0, 0.1):
        ma = 10
        larry_result = larry(data, k, ma)
        rank.append([larry_result[0], larry_result[1], round(k, 4), ma])

    rank.sort(key=lambda x:-x[0])
    k_sum = 0
    k_num = 0
    for i in rank:
        if i[0] == rank[0][0]:
            k_sum += i[2]
            k_num += 1
        # print(i)
    
    return k_sum / k_num

# print(finder("2021-01-17 09:00:00"))