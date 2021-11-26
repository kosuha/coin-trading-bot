import pyupbit
import time
from datetime import datetime
import config.upbit_token as token
import slack_bot
import numpy as np
import pandas as pd

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 프로그램 값 설정
currency = "KRW"
interval = "day"

def get_empty_tickers(tickers):
    empty_tickers = []
    for ticker in tickers:
        if upbit.get_balance(ticker) == 0:
            empty_tickers.append(ticker)

    return empty_tickers

def get_total(tickers, return_type):
    total = 0
    my_money = upbit.get_balance(currency)
    total = total + my_money
    for ticker in tickers:
        current_price = pyupbit.get_current_price(ticker)
        hold_ticker = upbit.get_balance(ticker)
        total = total + (hold_ticker * current_price)

    if return_type == "int":
        return round(total)

    return format(round(total), ",")

# 코인 매수
def buy_coin(ticker, n):
    my_money = upbit.get_balance(currency)
    amount = my_money / n
    current_price = pyupbit.get_current_price(ticker)
    if amount > 5000:
        buy_data = upbit.buy_market_order(ticker, amount - (amount * 0.0005))
        message = f"""
        < Buy >
        ticker: {ticker}
        current price: {current_price}

        """
        slack_bot.post_message(message)

# 코인 매도
def sell_coin(ticker):
    my_coin = upbit.get_balance(ticker)
    current_price = pyupbit.get_current_price(ticker)
    
    if my_coin > 0:
        sell_data = upbit.sell_market_order(ticker, my_coin)
        message = f"""
        < Sell >
        ticker: {ticker}
        current price: {current_price}

        """
        slack_bot.post_message(message)

# 지표 구하기
def get_indicator(coin):
    df = pyupbit.get_ohlcv(coin, interval=interval, count=41)

    # 지표 계산
    df['ma20'] = df['close'].rolling(window=20).mean().shift(1)
    df['ma40'] = df['close'].rolling(window=40).mean().shift(1)

    df['noise'] = 1 - abs(df['open']-df['close'])/(df['high']-df['low'])
    df['k'] = np.where((df['open'] > df['ma40']),
                            0,
                            df['noise'].rolling(window=10).mean().shift(1))

    df['ma'] = np.where((df['open'] > df['ma40']),
                        df['close'].rolling(window=8).mean().shift(1),
                        df['close'].rolling(window=5).mean().shift(1))

    this_interval = df.iloc[-1]
    last_interval = df.iloc[-2]

    this_interval_open = this_interval['open']
    last_interval_high = last_interval['high']
    last_interval_low = last_interval['low']

    k = this_interval['k']
    ma20 = this_interval['ma20']
    bull = this_interval['open'] > this_interval['ma']
    target = this_interval_open + (last_interval_high - last_interval_low) * k

    result = {
        'bull': bull,
        'open': this_interval_open, 
        'target': target,
        'ma20': ma20
        }

    return result

def trader():
    tickers = ["KRW-BTC"]
    start_total = (get_total(tickers, "int"),)
    not_today = False

    # 실행
    print("\n")
    print("########### START ###########")
    print("coin : ", tickers)
    print("currency : ", currency)
    print("interval : ", interval)
    print("\n")

    start_message = f"""
    <Start Trader> 
    tickers: {tickers}
    date: {time.strftime('%Y/%m/%d %H:%M:%S')}
    total: {get_total(tickers, "str")} KRW

    """
    slack_bot.post_message(start_message)

    while True:
        try:
            now = datetime.now()
            if (now.hour == 8) and (now.minute == 59):
                not_today = False

            if not_today:
                continue

            # 지표 업데이트, 매도
            if (now.hour == 9) and (now.minute == 0) and (20 <= now.second < 30):
                for ticker in tickers:
                    indicators = get_indicator(ticker)
                    if not indicators['bull']:
                        sell_coin(ticker)

            # 매수
            tickers_to_buy = get_empty_tickers(tickers)
            for ticker in tickers_to_buy:
                n = len(tickers_to_buy)
                indicators = get_indicator(ticker)
                current_price = pyupbit.get_current_price(ticker)
                if indicators['bull'] and current_price > indicators['target'] and indicators['open'] > indicators['ma20']:
                    buy_coin(ticker, n)

            # 슬랙
            if (now.hour == 9) and (now.minute == 0) and (40 <= now.second < 50):
                daily_message = f"""
                <{time.strftime('%Y/%m/%d %H:%M:%S')}>
                total: {get_total(tickers, "str")} KRW
                return: {format(round((get_total(tickers, "int") / start_total[0] * 100) - 100, 2), ",")} %
                """
                slack_bot.post_message(daily_message)
                time.sleep(11)

        except Exception as e:
            print("########### ERROR ###########")
            print(e)
            now = datetime.now()
            slack_bot.post_message(f"<ERROR {time.strftime('%Y/%m/%d %H:%M:%S')}> \n{e}")

        time.sleep(1)

trader()