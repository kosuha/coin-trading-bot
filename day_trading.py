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
coin = "KRW-DOGE"
currency = "KRW"
interval = "minute5"
K = 2.0

# 코인 매수
def buy_coin():
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    current_price = pyupbit.get_current_price(coin)
    if my_money > 5000:
        buy_data = upbit.buy_market_order(coin, my_money - 5000)
        message = f"""
        < Buy >
        uuid: {buy_data['uuid']}
        side: {buy_data['side']}
        ord_type: {buy_data['ord_type']}
        price: {buy_data['price']}
        state: {buy_data['state']}
        market: {buy_data['market']}
        created_at: {buy_data['created_at']}
        volume: {buy_data['volume']}
        remaining_volume: {buy_data['remaining_volume']}
        reserved_fee: {buy_data['reserved_fee']}
        remaining_fee: {buy_data['remaining_fee']}
        paid_fee: {buy_data['paid_fee']}
        locked: {buy_data['locked']}
        executed_volume: {buy_data['executed_volume']}
        trades_count: {buy_data['trades_count']}

        current price: {current_price}
        total: {format(round(my_money + (my_coin * current_price)), ",")}

        """
        slack_bot.post_message(message)

# 코인 매도
def sell_coin():
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    current_price = pyupbit.get_current_price(coin)
    if my_coin > 0:
        sell_data = upbit.sell_market_order(coin, my_coin)
        message = f"""
        < Sell >
        uuid: {sell_data['uuid']}
        side: {sell_data['side']}
        ord_type: {sell_data['ord_type']}
        price: {sell_data['price']}
        state: {sell_data['state']}
        market: {sell_data['market']}
        created_at: {sell_data['created_at']}
        volume: {sell_data['volume']}
        remaining_volume: {sell_data['remaining_volume']}
        reserved_fee: {sell_data['reserved_fee']}
        remaining_fee: {sell_data['remaining_fee']}
        paid_fee: {sell_data['paid_fee']}
        locked: {sell_data['locked']}
        executed_volume: {sell_data['executed_volume']}
        trades_count: {sell_data['trades_count']}

        current price: {current_price}
        total: {format(round(my_money + (my_coin * current_price)), ",")}

        """
        slack_bot.post_message(message)

# 오늘의 요일을 출력, 0 = 월요일
def today_weekday():
    return datetime.today().weekday()

# 지표 구하기
def get_indicator():
    df = pyupbit.get_ohlcv(coin, interval=interval, count=20)

    # 지표 계산
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)

    this_interval = df.iloc[-1]
    last_interval = df.iloc[-2]

    this_interval_open = this_interval['open']
    last_interval_high = last_interval['high']
    last_interval_low = last_interval['low']

    target = this_interval_open + (last_interval_high - last_interval_low) * K

    return {'open_price': this_interval_open, 'target_price': target, 'ma10': df['ma10']}

# 프로그램 실행 시 지표 계산
indicators = get_indicator()

start_money = upbit.get_balance(currency)
start_coin = upbit.get_balance(coin)
start_price = pyupbit.get_current_price(coin)

# 실행
print("\n")
print("########### START ###########")
print("coin : ", coin)
print("currency : ", currency)
print("interval : ", interval)
print("\n")

start_message = f"""
<Start Trader> 
coin: {coin}
start price: {start_price}
currency: {currency}
interval: {interval}
date: {time.strftime('%Y/%m/%d %H:%M:%S')}
total: {format(round(start_money + (start_coin * start_price)), ",")}

"""
slack_bot.post_message(start_message)

while True:
    try:
        current_price = pyupbit.get_current_price(coin)
        now_time = int(time.strftime('%H%M%S'))
        now_minute = int(time.strftime('%M'))
        now_second = int(time.strftime('%S'))

        # 매도, 지표 계산
        if now_minute == 0 or now_minute % 30 == 0:
            if 0 <= now_second < 5:
                sell_coin()
                indicators = get_indicator()

        # 매수
        if (current_price > indicators['target_price']) and (indicators['open_price'] > indicators['ma10']):
            buy_coin()

        # print(time.strftime('%Y/%m/%d %H:%M:%S'))
        # print("현재가: ", current_price)
        # print("매수 목표가: ", indicators['target_price'])
        # print()

    except Exception as e:
        print("########### ERROR ###########")
        print(e)
        slack_bot.post_message(f"<ERROR> \n{e}")

    time.sleep(1)
