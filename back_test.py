import pyupbit
import time
import pandas as pd
import config.upbit_token as token
import numpy as np
import math
import doge_rarry

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 테스트 설정 
test_length = 1250
pre_length = 40
test_data_interval = "day" # day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
test_end_date = "20210510" # "20200101"/None (None으로 하면 현재까지)
start_money = 3000000
test_money = start_money - 5000
bougth_price = 0;
test_coin = 0.0
fee = 0.0005
slippage = 0.002
main_coin = "KRW-XRP"
sub_coin = "KRW-BTC"
currency = "KRW"
K = None
ma_interval = None
sub_trading = False

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
    df = df.reset_index().rename(columns={"index": "date"})

    return df

def get_sub_coin_ror():
    df = get_data(sub_coin)
    k = 0.0

    # 지표 계산
    df['ma'] = df['close'].rolling(window=8).mean().shift(1)

    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)
    df['bull'] = df['open'] > df['ma']

    df['ror'] = np.where((df['high'] > df['target']) & df['bull'],
                        df['close'] / df['target'] - (fee + fee + slippage),
                        1)
        
    df.loc[:df.index[pre_length], ['ror']] = 1
    
    return [df['ror'], df['bull']]

# 레리 윌리엄스의 변동성 돌파 전략 적용
def larry(df_):
    df = df_

    # 지표 계산
    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['ma8'] = df['close'].rolling(window=8).mean().shift(1)
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)
    df['ma20'] = df['close'].rolling(window=20).mean().shift(1)
    df['ma40'] = df['close'].rolling(window=40).mean().shift(1)

    if K == None:
        df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])
        df['k'] = np.where((df['open'] > df['ma40']),
                                0,
                                df['noise'].rolling(window=20).mean().shift(1))
    else:
        df['k'] = K

    if ma_interval == None:
        df['ma'] = np.where((df['open'] > df['ma40']),
                            df['close'].rolling(window=8).mean().shift(1),
                            df['close'].rolling(window=5).mean().shift(1))
    else: 
        df['ma'] = df['close'].rolling(window=ma_interval).mean().shift(1)

    df['bull'] = df['open'] > df['ma']
    df['range'] = (df['high'] - df['low']) * df['k']
    df['range_shift1'] = df['range'].shift(1)
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

    if sub_trading:
        sub_coins_ror = get_sub_coin_ror()

        df['sub_coin_ror'] = sub_coins_ror[0]
        df['sub_coin_bull'] = sub_coins_ror[1]

        df['ror'] = np.where((df['bought'] == False) & (df['sub_coin_bull'] == True), df['ror'] * df['sub_coin_ror'], df['ror'])
                
    df['hpr'] = df['ror'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    ror = df['hpr'][len(df) - 1]
    mdd = round(df['dd'].max(), 2)

    print(df)
    file_name = "excels/doge.xlsx"
    df.to_excel(file_name)
    
    return [ror, mdd]

data = get_data(main_coin)
result = larry(data)

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
print(f"프로그램 수익률: {round((result[0] - 1) * 100, 2)} % / MDD = {result[1]} %")
print("End Money: ", format(round(start_money + ((start_money - 5000) * (result[0] - 1))), ","), currency)
print("-------------------------------  Test End  -------------------------------")

