import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 365
test_data_interval = "day" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
test_end_date = None # "20210201"/None (None으로 하면 현재까지)
start_money = 1000000
test_money = start_money - 5000
test_coin = 0.0
fee = 0.0005
slippage = 0.004
coins = ["KRW-XRP"]
currency = "KRW"
pre_length = 40

print("------------------------------- Test Start -------------------------------")

# 데이터 분석을 위한 테이터 가져오기
def get_data(coin):
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
    
    return df

# 전략 적용
def strategy(df):
    # 지표 계산
    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['ma8'] = df['close'].rolling(window=8).mean().shift(1)
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)
    df['ma20'] = df['close'].rolling(window=20).mean().shift(1)
    df['ma40'] = df['close'].rolling(window=40).mean().shift(1)

    df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])

    df['ma'] = df['ma5']

    df['k'] = df['noise'].rolling(window=10).mean().shift(1)

    df['bull'] = df['open'] > df['ma']
    df['range'] = (df['high'] - df['low']) * df['k']
    df['target'] = df['open'] + df['range'].shift(1)
    df['sell_condition'] = np.where(df['bull'] == False, True, False)
    df['buy_condition'] = np.where((df['high'] > df['target']) & df['bull'], True, False)

    df.loc[:df.index[pre_length], ['sell_condition', 'buy_condition']] = False
    
    # 코인을 보유한 상태인지 나타냄
    bought_status = False
    for i in df.index:
        if df.at[i, 'buy_condition']:
            bought_status = True
        if df.at[i, 'sell_condition']:
            bought_status = False
        df.at[i, 'bought'] = bought_status

    # 코인을 사고 팔때만 수수료가 포함된 수익률 계산
    df['bought_shift1'] = df['bought'].shift(1)
    df['bought_shift1'].fillna(False, inplace = True)
    df['ror'] = np.where(df['bought'] == True, df['close'] / df['open'], 1)
    df['ror'] = np.where((df['bought'] == True) & (df['bought_shift1'] == False), df['close'] / df['target'] - (fee + slippage), df['ror'])
    df['ror'] = np.where((df['bought'] == False) & (df['bought_shift1'] == True), 1 - (fee + slippage), df['ror'])

    df.loc[:df.index[pre_length], ['ror']] = 1

    return df

# 코인별 전략 적용한 데이터
def data_coins():
    datas = []
    for coin in coins:
        df = get_data(coin)
        datas.append(strategy(df))
        for column in df.columns:
            df.rename(columns = {column:f'{coin}_{column}'}, inplace=True)

    return pd.concat(datas, axis=1)

def trade(df):
    df['ror'] = 0
    for coin in coins:
        df['ror'] = df['ror'] + (df[f'{coin}_ror'] / len(coins))

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100

    ror = df['hpr'][-1]
    mdd = df['dd'].max()

    return [ror, mdd]

# 테스트 결과 출력
def print_result(df, result):

    print(df)

    rors = 0

    for coin in coins:
        start_price = df[f'{coin}_open'][pre_length]
        end_price = df[f'{coin}_close'][-1]
        r = (end_price - start_price)/start_price * 100
        rors += r

    print("\n")
    print("Start Money: ", format(round(start_money), ","), currency)
    print("Interval: ", test_data_interval)
    print("테스트 기간: ", test_length)
    print("테스트 시작: ", df.index[pre_length])
    print("테스트 종료: ", df.index[len(df)-1])
    print("존버 시 수익률: ", round(rors/len(coins), 2), "%")
    print(f"프로그램 수익률: {round((result[0] - 1) * 100, 2)} % / MDD = {round(result[1], 2)} %")
    print("End Money: ", format(round(start_money + ((start_money - 5000) * (result[0] - 1))), ","), currency)
    print("-------------------------------  Test End  -------------------------------")

df = data_coins();
result = trade(df)
print_result(df, result)

# file_name = "excels/test.xlsx"
# df.to_excel(file_name)
