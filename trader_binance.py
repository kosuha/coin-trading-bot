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

# 선물거래에 상장된 티커 중 USDT 시장 리스트 가져오기
def get_future_tickers():
    result = []
    markets = binance.fetch_tickers()
    for i in markets:
        if "/USDT" in i:
            result.append(i)
    
    return result

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
def calc_indicators(df):
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

    ema14 = df['close'].ewm(14).mean().shift(1)
    ema50 = df['close'].ewm(50).mean().shift(1)

    df['bear'] = ema14 < ema50
    df['bull'] = ema14 > ema50

    return df

# 레버리지 설정 (주의: 바이낸스가 열려있으면 안됌!)
def set_leverage(ticker, position, leverage_long, leverage_short):
    market = binance.market(ticker)
    if position == 'long':
        binance.fapiPrivate_post_leverage({
            'symbol': market['id'],
            'leverage': leverage_long
        })
    elif position == 'short':
        binance.fapiPrivate_post_leverage({
            'symbol': market['id'],
            'leverage': leverage_short
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

# 포지션 선정
def get_position(df, up, down, _position):
    prev_frame = df.iloc[-2]

    sell = np.where((prev_frame['rsi'] < down) & prev_frame['bear'], True, False)
    buy = np.where((prev_frame['rsi'] > up) & prev_frame['bull'], True, False)

    position = _position

    if buy:
        position = 'long'
        print("##### long condition!")
    elif sell:
        position = 'short'
        print("##### short condition!")
    
    return position

# 수량 계산
def get_amount(usdt_balance, current_price):
    usdt_trade = usdt_balance
    amount = math.floor((usdt_trade * 1000000) / current_price) / 1000000

    return amount

# 현재 진입한 포지션 정보를 가져오기
def get_position_amount(ticker):
    ticker_copy = ticker.split('/')[0] + ticker.split('/')[1]
    balance = binance.fetch_balance()
    positions = balance['info']['positions']

    for position in positions:
        if position['symbol'] == ticker_copy:
            return float(position['positionAmt'])

# 모든 포지션 정리
def exit_all_positions(tickers):
    for ticker in tickers:
        position_amount = get_position_amount(ticker)

        if position_amount > 0:
            response = binance.create_market_sell_order(symbol=ticker, amount=abs(position_amount))
        elif position_amount < 0:
            response = binance.create_market_buy_order(symbol=ticker, amount=abs(position_amount))

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

def trade(ticker, entry_price, position, start_balance):
    leverage_long = 3
    leverage_short = 3
    
    # 현재 진입한 포지션과 금액
    position_amount = get_position_amount(ticker)

    # 현재가와 구매가능 수량
    usdt = usdt_balance()
    current = current_price(ticker)
    amount = get_amount(usdt, current)
    set_leverage(ticker, position, leverage_long, leverage_short)
    
    # 포지션없을때
    if position_amount == 0:
        if position == 'long':
            # 매수
            total = total_balance()
            response = binance.create_market_buy_order(symbol=ticker, amount=amount * leverage_long)
            entry_price = current
            slack_bot.post_message(f"none => short / {round((total / start_balance * 100) - 100, 2)} %")
            
        elif position == 'short':
            # 매도
            total = total_balance()
            response = binance.create_market_sell_order(symbol=ticker, amount=amount * leverage_short)
            entry_price = current
            slack_bot.post_message(f"none => short / {round((total / start_balance * 100) - 100, 2)} %")
            
    # 롱포지션일때
    elif position_amount > 0:
        if position == 'short':
            # 매도후 매도
            total = total_balance()
            response = binance.create_market_sell_order(symbol=ticker, amount=abs(position_amount * 2))
            entry_price = current
            slack_bot.post_message(f"long => short / {round((total / start_balance * 100) - 100, 2)} %")
            
        elif position == '':
            # 매도
            total = total_balance()
            response = binance.create_market_sell_order(symbol=ticker, amount=abs(position_amount))
            slack_bot.post_message(f"long => none / {round((total / start_balance * 100) - 100, 2)} %")

    # 숏포지션일때
    elif position_amount < 0:
        if position == 'long':
            # 매수 후 매수
            total = total_balance()
            response = binance.create_market_buy_order(symbol=ticker, amount=abs(position_amount * 2))
            entry_price = current
            slack_bot.post_message(f"short => long / {round((total / start_balance * 100) - 100, 2)} %")

        elif position == '':
            # 매수
            total = total_balance()
            response = binance.create_market_buy_order(symbol=ticker, amount=abs(position_amount))
            slack_bot.post_message(f"short => none / {round((total / start_balance * 100) - 100, 2)} %")

    return position, entry_price

# 스탑
def stop(ticker, position, entry_price, stoploss, stopprofit, start_balance):
    if position == 'long':
        current = current_price(ticker)
        # 롱 프로핏, 로스
        if (entry_price * (1 + stopprofit)) < current:
            total = total_balance()
            position_amount = get_position_amount(ticker)
            response = binance.create_market_sell_order(symbol=ticker, amount=abs(position_amount))
            position = ''
            slack_bot.post_message(f"long => stop profit / {round((total / start_balance * 100) - 100, 2)} %")
        elif (entry_price * (1 - stoploss)) > current:
            total = total_balance()
            position_amount = get_position_amount(ticker)
            response = binance.create_market_sell_order(symbol=ticker, amount=abs(position_amount))
            position = ''
            slack_bot.post_message(f"long => stop loss / {round((total / start_balance * 100) - 100, 2)} %")

    elif position == 'short':
        current = current_price(ticker)
        # 숏 프로핏, 로스
        if (entry_price * (1 - stopprofit)) > current:
            total = total_balance()
            position_amount = get_position_amount(ticker)
            response = binance.create_market_buy_order(symbol=ticker, amount=abs(position_amount))
            position = ''
            slack_bot.post_message(f"short => stop profit / {round((total / start_balance * 100) - 100, 2)} %")
        elif (entry_price * (1 + stoploss)) < current:
            total = total_balance()
            position_amount = get_position_amount(ticker)
            response = binance.create_market_buy_order(symbol=ticker, amount=abs(position_amount))
            position = ''
            slack_bot.post_message(f"short => stop loss / {round((total / start_balance * 100) - 100, 2)} %")

    return position

def main():
    ticker = "ETH/USDT"
    start_balance = 100
    reset_bool = False
    position = ""
    entry_price = 0
    total = total_balance()

    slack_bot.post_message(f"start binance trading / {round((total / start_balance * 100) - 100, 2)} %")

    while True:
        try:
            now = datetime.datetime.now()
            looptimeframe = [0, 15, 30, 45]
            looptimeframe_addone = [1, 16, 31, 46]
            
            # 15분 간격으로 지표 업데이트 후 매매
            if (reset_bool == False) and (now.minute in looptimeframe):
                df = get_ohlcv(ticker, "15m", 60)
                df = calc_indicators(df)
                position = get_position(df, 80, 20, position)
                position, entry_price = trade(ticker, entry_price, position, start_balance)

                total = total_balance()

                # message = f"""
                # <{time.strftime('%Y/%m/%d %H:%M:%S')}>
                # ticker: {ticker}
                # position: {position}
                # total: {format(round(total, 2), ",")} USDT
                # return: {round((total / start_balance * 100) - 100, 2)} %
                # """
                # print(message)

                reset_bool = True

            if now.minute in looptimeframe_addone:
                reset_bool = False

            # 스탑로스, 스탑프로핏
            stoploss, stopprofit = 0.085, 0.085
            position = stop(ticker, position, entry_price, stoploss, stopprofit, start_balance)

            # print(time.strftime('%Y/%m/%d %H:%M:%S'), current_price(ticker))
        
        except Exception as e:
            slack_bot.post_message(f"{e}")
            print(e)

        time.sleep(1)

main()