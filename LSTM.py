import pyupbit
import config.upbit_token as token
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import model_selection
from sklearn.preprocessing import MinMaxScaler
from keras import models, layers
# from keraspp import skeras
import datetime
import time

start = time.time()

# 업비트에 연결
upbit = pyupbit.Upbit(token.access, token.secret)

# 기본 설정
coin = "KRW-BTC"
interval = "minute60"
data_length = 10000
test_end_date = None
time_series_length = 24
epochs = 200
dense = 1
test_size = 0.2
random_state = 42

scaler = MinMaxScaler()

# 데이터 분석을 위한 테이터 가져오기
def get_data(length, test_end_date):
    date = test_end_date
    dfs = []

    if length > 200:
        loop_num = length // 200
        remainder = length % 200
        for i in range(loop_num):
            df = pyupbit.get_ohlcv(coin, interval=interval, to=date, count=200)
            dfs.append(df)
            date = df.index[0]
            time.sleep(0.1)
        df = pyupbit.get_ohlcv(coin, interval=interval, to=date, count=remainder)
        dfs.append(df)
        
    else:
        df = pyupbit.get_ohlcv(coin, interval=interval, to=date, count=length)
        dfs.append(df)

    df = pd.concat(dfs).sort_index()
    df = df.dropna(axis=0)
    df['change'] = ((df['close'] - df['open']) / df['open']) * 100
    print(df)
    return df

def main():
    machine = Machine()
    machine.run(epochs=epochs)


class Machine():
    def __init__(self):
        self.data = Dataset()
        shape = self.data.X.shape[1:]
        # print("shape", shape)
        self.model = rnn_model(shape)

    def run(self, epochs=epochs):
        d = self.data
        X_train, X_test, y_train, y_test = d.X_train, d.X_test, d.y_train, d.y_test
        X, y = d.X, d.y
        m = self.model
        h = m.fit(X_train, y_train, epochs=epochs, validation_data=[X_test, y_test], verbose=1)

        # skeras.plot_loss(h)
        # plt.title('History of training')
        # plt.show()
        # scaler = MinMaxScaler()
        
        yp = m.predict(X_test)
        columns = ['change']
        
        y_test = scaler.inverse_transform(y_test)
        yp = scaler.inverse_transform(yp)
        y_test_df = pd.DataFrame(y_test, columns=columns)
        yp_df = pd.DataFrame(yp, columns=columns)

        # y_test_df['updown'] = np.where(y_test_df['open'] > y_test_df['close'], 0, 0.5)
        # y_test_df['updown'] = np.where(y_test_df['open'] < y_test_df['close'], 1, y_test_df['updown'])

        # yp_df['updown'] = np.where(yp_df['open'] > yp_df['close'], 0, 0.5)
        # yp_df['updown'] = np.where(yp_df['open'] < yp_df['close'], 1, yp_df['updown'])

        y_test_df['pred_change'] = yp_df['change']
        
        # y_test_df['error'] = abs((y_test_df['pred_change'] / y_test_df['change'] * 100) - 100)
        print(y_test_df)

        # print("평균 오차: ", y_test_df['error'].sum() / len(y_test_df))
        # print(yp_df)

        # correct_num = 0
        # for i in y_test_df.index:
        #     if y_test_df.at[i, 'updown'] == yp_df.at[i, 'updown']:
        #         correct_num += 1
        
        # print("정확도 : ", round(correct_num/len(y_test_df) * 100, 2), "%")


def rnn_model(shape):
    m_x = layers.Input(shape=shape)  # X.shape[1:]
    m_h = layers.LSTM(10)(m_x)
    m_y = layers.Dense(dense)(m_h)
    m = models.Model(m_x, m_y)

    m.compile('adam', 'mean_squared_error')
    m.summary()

    return m


class Dataset:
    def __init__(self, D=time_series_length):
        df = load_data()
        X, y = get_Xy(df, D=D)
        X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=test_size, random_state=random_state)

        self.X, self.y = X, y
        self.X_train, self.X_test, self.y_train, self.y_test = X_train, X_test, y_train, y_test


def load_data():
    df = get_data(data_length, test_end_date)
    df.drop(['open', 'high', 'low', 'close', 'volume'], axis=1, inplace=True)
    
    # data normalize
    scale_cols = ['change']
    df_normalized = scaler.fit_transform(df)
    df_normalized = pd.DataFrame(df_normalized)
    df_normalized.columns = scale_cols
    # print("#############")
    # print(type(df_normalized))
    # print(df_normalized)
    # print("#############")

    return df_normalized


def get_Xy(df, D=time_series_length):
    # make X(예측의 기반이 되는 데이터) and y(예측 대상 데이터)
    data = df.values
    N = len(data)
    X_l = []
    y_l = []

    assert N > D, "N should be larger than D, where N is len(data)"

    for i in range(N - D - 1):
        X_l.append(data[i:i + D - 1])
        y_l.append(data[i + D])
    
    X = np.array(X_l)
    y = np.array(y_l)
    print(X.shape, y.shape)
    return X, y


if __name__ == '__main__':
    main()

print("Time :", round(time.time() - start, 1), "sec")