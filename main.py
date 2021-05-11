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
sub_coin = "KRW-BTC"
currency = "KRW"
interval = "day"
sub_trading = False

# 코인 매수
def buy_coin(coin):
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
def sell_coin(coin):
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
    df = pyupbit.get_ohlcv(main_coin, interval=interval, count=50)
    sub_df = pyupbit.get_ohlcv(sub_coin, interval=interval, count=10)

    # 지표 계산
    df['ma5'] = df['close'].rolling(window=5).mean().shift(1)
    df['ma8'] = df['close'].rolling(window=8).mean().shift(1)
    df['ma10'] = df['close'].rolling(window=10).mean().shift(1)
    df['ma20'] = df['close'].rolling(window=20).mean().shift(1)
    df['ma40'] = df['close'].rolling(window=40).mean().shift(1)

    sub_df['ma8'] = sub_df['close'].rolling(window=8).mean().shift(1)

    df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])

    df['ma'] = np.where((df['open'] > df['ma40']),
                            df['close'].rolling(window=8).mean().shift(1),
                            df['close'].rolling(window=5).mean().shift(1))

    df['k'] = np.where((df['open'] > df['ma40']),
                            0,
                            df['noise'].rolling(window=20).mean().shift(1))

    this_interval = df.iloc[-1]
    last_interval = df.iloc[-2]
    this_interval_sub = sub_df.iloc[-1]

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
        'target_price': target,
        'sub_ma': this_interval_sub['ma8']
        }

    return result

# 프로그램 실행 시 지표 계산
indicators = get_indicator()

start_money = upbit.get_balance(currency)
start_coin = upbit.get_balance(main_coin)
start_coin_sub = upbit.get_balance(sub_coin)
start_price = pyupbit.get_current_price(main_coin)
start_price_sub = pyupbit.get_current_price(sub_coin)

# 실행
print("\n")
print("########### START ###########")
print("main coin : ", main_coin)
print("sub coin : ", sub_coin)
print("sub trading : ", sub_trading)
print("currency : ", currency)
print("interval : ", interval)
print("\n")

start_message = f"""
<Start Trader> 
main coin: {main_coin}
sub coin: {sub_coin}
sub trading: {sub_trading}
start price: {start_price}
currency: {currency}
interval: {interval}
date: {time.strftime('%Y/%m/%d %H:%M:%S')}
total: {format(round(start_money + (start_coin * start_price) + (start_coin_sub * start_price_sub)), ",")}

"""
slack_bot.post_message(start_message)

while True:
    try:
        current_price = pyupbit.get_current_price(main_coin)
        current_price_sub = pyupbit.get_current_price(sub_coin)
        now_time = int(time.strftime('%H%M%S'))

        # 지표 업데이트, 매도
        if 90000 <= now_time < 90005:
            if sub_trading:
                sell_coin(sub_coin)

            indicators = get_indicator()
            if indicators['open_price'] > indicators['ma']:
                pass
            else:
                sell_coin(main_coin)

        # 매수
        if (current_price > indicators['target_price']) and (indicators['open_price'] > indicators['ma']):
            buy_coin(main_coin)

        if sub_trading:
            if not (90000 <= now_time < 90005):
                if (indicators['open_price'] <= indicators['ma']) and (current_price_sub > indicators['sub_ma']):
                    buy_coin(sub_coin)

            # print(time.strftime('%Y/%m/%d %H:%M:%S'))
            # print("현재가: ", current_price)
            # print("매수 목표가: ", target_price)
            # print()

    except Exception as e:
        print("########### ERROR ###########")
        print(e)
        slack_bot.post_message(f"<ERROR> \n{e}")

    time.sleep(1)
