import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 12
pre_length = 40
test_data_interval = "minute60" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
# test_end_date = "2021-05-01 09:20:00" # "20210201"/None (None으로 하면 현재까지)
start_money = 1000000
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.005
currency = "KRW"
coins = ["KRW-ETH", "KRW-BTC", "KRW-XRP", "KRW-ETC", "KRW-DOGE"]
# coins = pyupbit.get_tickers(fiat=currency)

# 데이터 분석을 위한 테이터 가져오기
def get_data(coin, test_end_date):
    date = test_end_date
    dfs = []
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
    time.sleep(0.1)

    return df

# 전략 적용
def strategy(df, coin):
    df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])
    df['k'] = df['noise'].rolling(window=20).mean().shift(1)
    df['range'] = (df['high'] - df['low']) * df['k']
    df['target'] = df['open'] + df['range'].shift(1)
    df['buy_condition'] = np.where(df['high'] > df['target'], True, False)
    df[coin] = np.where(df['buy_condition'] == True,
                        df['close'] / df['target'] - (fee + fee + slippage),
                        0)

    return df

def total(test_end_date):
    dfs = []
    i = 0
    for coin in coins:
        dfs.append(strategy(get_data(coin, test_end_date), coin))
        i += 1
        print(f"{i}/{len(coins)}, {coin}")

    df = pd.concat(dfs, axis=1)
    # df = df.reset_index().rename(columns={"index": "date"})

    df = df[coins]
    df = df.fillna(0)
    df['sum'] = df.sum(axis=1)

    for i in range(0, len(df.index)):
        df.loc[df.index[i], 'not_buy_count'] = df.loc[df.index[i], :coins[-1]].value_counts()[0]

    df['ror'] = np.where(df['not_buy_count'] != len(coins),
                        df['sum'] / (len(coins) - df['not_buy_count']),
                        1)

    df.loc[:df.index[pre_length], ['ror']] = 1

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    
    mdd = round(df['dd'].max(), 2)
    ror = round(df['hpr'][len(df) - 1], 2)
    
    return ror

ror = 1
for i in range(1, 20):
    ror = ror * total(f"2021-05-{i} 09:20:00")

print(ror)



