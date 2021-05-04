import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math
import k_finder

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 30
test_data_interval = "day" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
test_end_date = "20210504" # "20210201"/None (None으로 하면 현재까지)
start_money = 1000000
test_money = start_money - 5000
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.002
coin = "KRW-BTT"
currency = "KRW"
K = None
ma_interval = 5

print("------------------------------- Test Start -------------------------------")

# 데이터 분석을 위한 테이터 가져오기
def get_data():
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
    df = df.reset_index().rename(columns={"index": "date"})

    print(df)
    return df

# 레리 윌리엄스의 변동성 돌파 전략, K값에 따른 수익률
def larry(df_, k, ma):
    df = df_

    if k == None:
        for i in df.index:
            df.loc[i, 'k'] = k_finder.finder(df.at[i, 'date'])
            print(df.loc[i, 'date'])
    else:
        df['k'] = k

    if ma_interval == None:
        for i in df.index:
            mai = k_finder.finder(df.at[i, 'date'])
            df['ma'] = df['close'].rolling(window=mai).mean().shift(1)
            print(df.loc[i, 'date'])
    else:
        df['ma'] = df['close'].rolling(window=ma_interval).mean().shift(1)
    
    # 지표 계산
    df['bull'] = df['open'] > df['ma']
    df['range'] = (df['high'] - df['low']) * df['k']
    df['range_shift1'] = df['range'].shift(1)
    df['target'] = df['open'] + df['range'].shift(1)
    df['sell_condition'] = np.where(df['bull'] == False, True, False)
    df['buy_condition'] = np.where((df['high'] > df['target']) & df['bull'], True, False)

    df.loc[:df.index[20], ['sell_condition', 'buy_condition']] = False
    
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

    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    ror = df['hpr'][len(df) - 1]
    mdd = round(df['dd'].max(), 2)

    print(df)
    # file_name = "excels/larry_{}_{}_k{}.xlsx".format(test_length, test_data_interval, k)
    # df.to_excel(file_name)
    
    return [ror, mdd]

data = get_data()
result = larry(data, K, ma_interval)

# 테스트 결과 출력
print("\n")
print("Start Money: ", format(round(start_money), ","), currency)
print("Interval: ", test_data_interval)
print("테스트 기간: ", test_length)
print("테스트 시작: ", data.date[20])
print("테스트 종료: ", data.date[len(data)-1])
print("시작가: ", data.open[20])
print("종료가: ", data.close[len(data)-1])
print("존버 시 수익률: ", round(((data.close[len(data)-1] - data.open[20]) / data.open[20])*100, 3), "%")
print(f"프로그램 수익률: {round((result[0] - 1) * 100, 2)} % / MDD = {result[1]} %")
print("End Money: ", format(round(start_money + ((start_money - 5000) * (result[0] - 1))), ","), currency)
print("-------------------------------  Test End  -------------------------------")

