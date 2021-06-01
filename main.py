import pyupbit
import time
from datetime import datetime
import config.upbit_token as token
import market_order_info as market
import slack_bot
import numpy as np
import pandas as pd

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 프로그램 값 설정
main_coin = "KRW-XRP"
currency = "KRW"
interval = "day"

# 코인 매수
def buy_coin(coin):
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    current_price = pyupbit.get_current_price(coin)
    if my_money > 5000 and my_coin == 0:
        buy_data = upbit.buy_market_order(coin, (my_money - 5000))
        message = f"""
        < Buy >
        current price: {current_price}
        total: {format(round(my_money + (my_coin * current_price)), ",")}

        """
        slack_bot.post_message(message)

# 코인 매도
def sell_coin(coin):
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    current_price = pyupbit.get_current_price(coin)
    if my_coin > 0:
        sell_data = upbit.sell_market_order(coin, my_coin)
        message = f"""
        < Sell >
        current price: {current_price}
        total: {format(round(my_money + (my_coin * current_price)), ",")}

        """
        slack_bot.post_message(message)

# 오늘의 요일을 출력, 0 = 월요일
def today_weekday():
    return datetime.today().weekday()

# 지표 구하기
def get_indicator(coin):
    df = pyupbit.get_ohlcv(coin, interval=interval, count=50)

    # 지표 계산
    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['ma8'] = df['close'].rolling(window=8).mean().shift(1)
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)
    df['ma20'] = df['close'].rolling(window=20).mean().shift(1)
    df['ma40'] = df['close'].rolling(window=40).mean().shift(1)

    df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])

    df['ma'] = np.where((df['open'] > df['ma40']),
                            df['close'].rolling(window=8).mean().shift(1),
                            df['close'].rolling(window=5).mean().shift(1))

    df['k'] = np.where((df['open'] > df['ma40']),
                            0,
                            df['noise'].rolling(window=20).mean().shift(1))

    this_interval = df.iloc[-1]
    last_interval = df.iloc[-2]

    this_interval_open = this_interval['open']
    last_interval_high = last_interval['high']
    last_interval_low = last_interval['low']

    k = this_interval['k']
    ma = this_interval['ma']
    target = this_interval_open + (last_interval_high - last_interval_low) * k

    result = {
        'k': k,
        'ma': ma,
        'open_price': this_interval_open, 
        'target_price': target
        }

    return result

# 프로그램 실행 시 지표 계산
indicators = get_indicator()
daily_checker = False

start_money = upbit.get_balance(currency)
start_coin = upbit.get_balance(main_coin)
start_price = pyupbit.get_current_price(main_coin)

# 실행
print("\n")
print("########### START ###########")
print("coin : ", main_coin)
print("currency : ", currency)
print("interval : ", interval)
print("\n")

start_message = f"""
<Start Trader> 
main coin: {main_coin}
start price: {start_price}
currency: {currency}
interval: {interval}
date: {time.strftime('%Y/%m/%d %H:%M:%S')}
total: {format(round(start_money + (start_coin * start_price)), ",")}

"""
slack_bot.post_message(start_message)

while True:
    try:
        current_price = pyupbit.get_current_price(main_coin)
        now_time = int(time.strftime('%H%M%S'))

        # 지표 업데이트, 매도
        if 90000 <= now_time < 90005:
            indicators = get_indicator()
            if indicators['open_price'] > indicators['ma']:
                pass
            else:
                sell_coin(main_coin)

        # 매수
        if (current_price > indicators['target_price']) and (indicators['open_price'] > indicators['ma']):
            buy_coin(main_coin)

        if 90100 <= now_time < 90105:
            now_money = upbit.get_balance(currency)
            now_coin = upbit.get_balance(main_coin)

            if daily_checker == False:
                daily_message = f"""
                <{time.strftime('%Y/%m/%d %H:%M:%S')}>
                total: {format(round(now_money + (now_coin * current_price)), ",")}
                return: {round((round(now_money + (now_coin * current_price)) / 1000000 * 100) - 100, 2)} %
                """
                slack_bot.post_message(daily_message)
                daily_checker = True
        else:
            daily_checker = False
            

            # print(time.strftime('%Y/%m/%d %H:%M:%S'))
            # print("현재가: ", current_price)
            # print("매수 목표가: ", target_price)
            # print()

    except Exception as e:
        print("########### ERROR ###########")
        print(e)
        slack_bot.post_message(f"<ERROR> \n{e}")

    time.sleep(1)
