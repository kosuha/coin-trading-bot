import pyupbit
import time
from datetime import datetime
# import config.conn as pw
import config.upbit_token as token
import market_order_info as market
import slack_bot
# import pymysql
# from sqlalchemy import create_engine

# DB에 연결
# engine = create_engine(pw.conn)
# conn = engine.connect()

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 프로그램 값 설정
coin = "KRW-XRP"
currency = "KRW"
interval = "day"
k = 0

print("\n")
print("########### START ###########")
print("coin : ", coin)
print("currency : ", currency)
print("interval : ", interval)
print("K : ", k)
print("\n")

# 코인 구매
def buy_coin():
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    current_price = pyupbit.get_current_price(coin)
    if my_money > 5000:
        buy_data = upbit.buy_market_order(coin, my_money - 5000)
        #buy_data_insert(buy_data)
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

# 코인 판매
def sell_coin():
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    #prev_my_money = upbit.get_balance(currency)
    current_price = pyupbit.get_current_price(coin)
    if my_coin > 0:
        sell_data = upbit.sell_market_order(coin, my_coin)
        #sell_data_insert(sell_data, prev_my_money)
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

# 목표가 설정
def get_target_price():
    df = pyupbit.get_ohlcv(coin, interval=interval, count=5)
    last_interval = df.iloc[-2]

    this_interval_open = last_interval['close']
    last_interval_high = last_interval['high']
    last_interval_low = last_interval['low']
    target = this_interval_open + (last_interval_high - last_interval_low) * k

    return target

# 오늘의 요일을 출력, 0 = 월요일
def today_weekday():
    return datetime.today().weekday()

# 5이동평균값 구하기
def get_last_interval_ma5():
    df = pyupbit.get_ohlcv(coin, interval=interval, count=10)
    close = df['close']
    ma = close.rolling(window=5).mean()

    return ma[-2]

# DB에 거래정보 입력
'''
def buy_data_insert(data):
    fee = float(market.order_info(coin)["bid_fee"])
    current_price = pyupbit.get_current_price(coin)
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    total = my_money + (current_price * my_coin)

    df = pd.DataFrame({
        "side": data['side'],
        "price": float(data['price']) / my_coin,
        "volume": my_coin,
        "fee": float(data['price']) * fee,
        "total": total,
        "money": my_money,
        "coin": my_coin,
        "market": data['market'],
        "date": data['created_at']
         }, index=[0])

    df.to_sql(name='transaction_history', con=engine, if_exists='append', index=False)

def sell_data_insert(data, prev_my_money):
    fee = float(market.order_info(coin)["ask_fee"])
    current_price = pyupbit.get_current_price(coin)
    my_money = upbit.get_balance(currency)
    my_coin = upbit.get_balance(coin)
    total = my_money + (current_price * my_coin)

    df = pd.DataFrame({
        "side": data['side'],
        "price": current_price,
        "volume": float(data['volume']),
        "fee": (my_money - prev_my_money) * fee,
        "total": total,
        "money": my_money,
        "coin": my_coin,
        "market": data['market'],
        "date": data['created_at']
         }, index=[0])
    
    df.to_sql(name='transaction_history', con=engine, if_exists='append', index=False)
'''

# 프로그램 실행 시 목표가와 이동평균값 계산
target_price = get_target_price()
ma5 = get_last_interval_ma5()

start_money = upbit.get_balance(currency)
start_coin = upbit.get_balance(coin)
start_price = pyupbit.get_current_price(coin)

# 실행
start_message = f"""
<Start Trader> 
coin: {coin}
start price: {start_price}
currency: {currency}
interval: {interval}
K: {k}
date: {time.strftime('%Y/%m/%d %H:%M:%S')}
total: {format(round(start_money + (start_coin * start_price)), ",")}

"""
slack_bot.post_message(start_message)

while True:
    try:
        current_price = pyupbit.get_current_price(coin)
        now_time = int(time.strftime('%H%M%S'))
        today_weekday()

        # 매도
        if 85955 <= now_time < 90000:
            # k값이 0이면 상승장에 매도를 하지 않음
            if k == 0 and current_price > ma5:
                pass
            else:
                sell_coin()

        # 목표가, 이평선 계산
        if 90000 <= now_time < 90005:
            target_price = get_target_price()
            ma5 = get_last_interval_ma5()

        # 매수
        if not (85955 <= now_time < 90000):
            if (current_price >= target_price) and (current_price < target_price + (target_price * 0.005)) and (current_price > ma5):
                buy_coin()

        # print(time.strftime('%Y/%m/%d %H:%M:%S'))
        # print("현재가: ", current_price)
        # print("매수 목표가: ", target_price)
        # print()

    except Exception as e:
        print("########### ERROR ###########")
        print(e)
        slack_bot.post_message(f"<ERROR> \n{e}")

    time.sleep(1)
