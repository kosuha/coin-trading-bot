import datetime
import ccxt
import pandas as pd
import config.binance_api as ba
import time
import math
import numpy as np
import slack_bot

# 바이낸스 선물거래 객체 생성
binance = ccxt.binance(config={
    'apiKey': ba.api,
    'secret': ba.secret,
    'enableRateLimit': True,
    'options':{
        'defaultType': 'future'
    }
})

# 과거 데이터 조회
def get_ohlcv(ticker, timeframe, limit):
    coin_ohlcv = binance.fetch_ohlcv(
        ticker, 
        timeframe=timeframe, 
        since=None, 
        limit=limit
        )

    df = pd.DataFrame(coin_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    return df

# 지표 계산
def get_rsi(df):
    delta = df['close'].diff(1)
    delta = delta.dropna()

    u = delta.copy()
    d = delta.copy()
    u[u < 0] = 0
    d[d > 0] = 0
    
    au = u.ewm(com = 14-1, min_periods = 14).mean()
    ad = d.abs().ewm(com = 14-1, min_periods = 14).mean()

    rsi = pd.Series(100 - (100 / (1 + au / ad)))
    df['rsi'] = rsi

    return df.iloc[-3]['rsi'], df.iloc[-2]['rsi']

# 레버리지 설정 (주의: 바이낸스가 열려있으면 안됌!)
def set_leverage(ticker, leverage):
    market = binance.market(ticker)
    binance.fapiPrivate_post_leverage({
        'symbol': market['id'],
        'leverage': leverage
    })

# 현재가 조회
def current_price(ticker):
    coin = binance.fetch_ticker(ticker)
    current = coin['last']

    return current

# 자산 조회
def usdt_balance():
    balance = binance.fetch_balance()
    total = balance['total']['USDT']

    return total

# 수량 계산
def get_amount(usdt_balance, current_price, entry_count):
    usdt_trade = usdt_balance
    amount = math.floor((usdt_trade * 1000000) / current_price) / 1000000

    return (amount / entry_count)

# 현재 진입한 포지션 정보를 가져오기
def get_position_amount(ticker):
    ticker_copy = ticker.split('/')[0] + ticker.split('/')[1]
    balance = binance.fetch_balance()
    positions = balance['info']['positions']

    for position in positions:
        if position['symbol'] == ticker_copy:
            return float(position['positionAmt'])

# 잔고 조회
def usdt_balance():
    balance = binance.fetch_balance()
    total = balance['USDT']['free']

    return total

# 자산 조회
def total_balance():
    balance = binance.fetch_balance()
    total = balance['total']['USDT']

    return total

# 모든 포지션 정리
def close_all_positions(ticker, position_amount, start_balance):
    if position_amount > 0:
        response = binance.create_market_sell_order(symbol=ticker, amount=abs(position_amount))
    elif position_amount < 0:
        response = binance.create_market_buy_order(symbol=ticker, amount=abs(position_amount))
    
    total = total_balance()
    slack_bot.post_message(f"Close positions. Return: {round((total / start_balance * 100) - 100, 2)} %")

def entry_long(ticker, amount, leverage):
    response = binance.create_market_buy_order(symbol=ticker, amount=amount * leverage)
    slack_bot.post_message(f"Entry Long x{leverage} {round(amount, 2)} USDT")

def entry_short(ticker, amount, leverage):
    response = binance.create_market_sell_order(symbol=ticker, amount=amount * leverage)
    slack_bot.post_message(f"Entry Short x{leverage} {round(amount, 2)} USDT")

def main():
    ticker = "ETH/USDT"
    start_balance = 100
    reset_bool = False
    total = total_balance()
    rsi_up = 75
    rsi_down = 25
    entry_count = 10
    leverage = 2

    slack_bot.post_message(f"Start Binance Futures Trading. Balance: {round(total, 2)} USDT")

    while True:
        try:
            now = datetime.datetime.now()
            looptimeframe = [0, 15, 30, 45]
            looptimeframe_addone = [1, 16, 31, 46]
            
            # 15분 간격으로 지표 업데이트 후 매매
            if (reset_bool == False) and (now.minute in looptimeframe):
                df = get_ohlcv(ticker, "15m", 20)
                last_rsi, rsi = get_rsi(df)
                long = rsi > rsi_down and last_rsi < rsi_down   # over sold
                short = rsi < rsi_up and last_rsi > rsi_up      # over bought
                position_amount = get_position_amount(ticker)
                price = current_price()
                usdt = usdt_balance()
                amount = get_amount(usdt, price, entry_count)
                if amount < 5.0:
                    slack_bot.post_message(f"You need more USDT balance. End program.")
                    break

                set_leverage(ticker, leverage)

                if long:
                    if position_amount < 0:
                        close_all_positions(ticker, position_amount, start_balance)
                        entry_count = 10
                    elif entry_count > 0:
                        entry_long(ticker, amount, leverage)
                        entry_count -= 1

                if short:
                    if position_amount > 0:
                        close_all_positions(ticker, position_amount, start_balance)
                        entry_count = 10
                    elif entry_count > 0:
                        entry_short(ticker, amount, leverage)
                        entry_count -= 1

                reset_bool = True

            if now.minute in looptimeframe_addone:
                reset_bool = False
        
        except Exception as e:
            slack_bot.post_message(f"binance! {e}")
            print(e)

        time.sleep(1)

main()