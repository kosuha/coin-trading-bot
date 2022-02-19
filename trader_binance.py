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
    period = 14
    
    delta = df['close'].diff()
    u, d = delta.copy(), delta.copy()
    u[u < 0] = 0
    d[d > 0] = 0
    
    au = u.ewm(com = period - 1, min_periods = period).mean()
    ad = d.abs().ewm(com = period - 1, min_periods = period).mean()
    rs = au / ad
    rsi = pd.Series(100 - (100 / (1 + rs)))
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
def get_amount(usdt_balance, current_price, count):
    usdt_trade = usdt_balance
    amount = math.floor((usdt_trade * 1000000) / current_price) / 1000000

    return (amount / count)

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
    slack_bot.post_message(f"#\nClose positions\nReturn: {round((total / start_balance * 100) - 100, 2)} %\nTotal: {round(total, 2)} USDT")

def entry_long(ticker, amount, leverage):
    response = binance.create_market_buy_order(symbol=ticker, amount=amount * leverage)

def entry_short(ticker, amount, leverage):
    response = binance.create_market_sell_order(symbol=ticker, amount=amount * leverage)

def main():
    ticker = "ETH/USDT"
    start_balance = 100
    total = total_balance()
    rsi_up = 76
    rsi_down = 24
    entry_count = 0
    entry_max = 10

    slack_bot.post_message(f"#\nStart Binance Futures Trading.\nStart balance: {round(total, 2)} USDT\nTicker: {ticker}")
    print("Start!")

    while True:
        try:
            now = datetime.datetime.now()
            
            # 3분 간격으로 지표 업데이트 후 매매
            if (now.second > 5) and (now.minute == 0 or now.minute % 3 == 0):
                df = get_ohlcv(ticker, "3m", 100)
                last_rsi, rsi = get_rsi(df)
                long = rsi >= rsi_down and last_rsi < rsi_down   # over sold
                short = rsi <= rsi_up and last_rsi > rsi_up      # over bought
                position_amount = get_position_amount(ticker)
                price = current_price(ticker)
                usdt = usdt_balance()
                if (entry_count < entry_max) and ((usdt / (entry_max - entry_count)) < 5.0):
                    slack_bot.post_message(f"#\nYou need more USDT balance.\nEnd program.")
                    break
                amount = get_amount(usdt, price, entry_max - entry_count)
                
                if long:
                    if position_amount < 0:
                        close_all_positions(ticker, position_amount, start_balance)
                        entry_count = 0
                    if entry_count < entry_max:
                        leverage = 1 if entry_count == 0 else (entry_count // 3) + 1
                        set_leverage(ticker, leverage)
                        entry_long(ticker, amount, leverage)
                        entry_count += 1
                        slack_bot.post_message(f"#\nEntry Long x{leverage} ({entry_count} / {entry_max})")

                if short:
                    if position_amount > 0:
                        close_all_positions(ticker, position_amount, start_balance)
                        entry_count = 0
                    if entry_count < entry_max:
                        leverage = 1 if entry_count == 0 else (entry_count // 3) + 1
                        set_leverage(ticker, leverage)
                        entry_short(ticker, amount, leverage)
                        entry_count += 1
                        slack_bot.post_message(f"#\nEntry Short x{leverage} ({entry_count} / {entry_max})")

                time.sleep(60)
        
        except Exception as e:
            slack_bot.post_message(f"#\nError\n{e}")
            print(e)

        time.sleep(1)

main()