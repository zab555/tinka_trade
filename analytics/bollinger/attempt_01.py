import os
from datetime import timedelta

import pandas as pd
import numpy as np
from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

# TOKEN = os.environ["INVEST_TOKEN"]
TOKEN = 'INSERT_YOUR_TOKEN_HERE'

# 'BBG004730N88' - SBER
# 'BBG004731032' - LKOH
# 'RU0007661625' - GAZP
pd.set_option('display.max_columns', None)

# CANDLE_INTERVAL_1_MIN
# CANDLE_INTERVAL_5_MIN
# CANDLE_INTERVAL_15_MIN
# CANDLE_INTERVAL_HOUR
# CANDLE_INTERVAL_DAY
CANDLE_INTERVAL = CandleInterval.CANDLE_INTERVAL_15_MIN


def get_historic_data(figi):
    df = pd.DataFrame()

    date = []
    open = []
    high = []
    low = []
    close = []

    def qq_2_float(qq):
        return float(qq.units) + float('0.' + str(qq.nano))

    with Client(TOKEN) as client:
        for candle in client.get_all_candles(
            figi=figi,
            from_=now() - timedelta(days=1),
            interval=CANDLE_INTERVAL,
        ):
            # print(candle)

            date.append(candle.time.strftime("%m/%d/%Y, %H:%M:%S"))
            open.append(qq_2_float(candle.open))
            high.append(qq_2_float(candle.high))
            low.append(qq_2_float(candle.low))
            close.append(qq_2_float(candle.close))

    df['date'] = date
    df['open'] = open
    df['high'] = high
    df['low'] = low
    df['close'] = close
    return df


def sma(data, window):
    sma = data.rolling(window=window).mean()
    return sma


def bb(data, sma, window):
    std = data.rolling(window=window).std()
    upper_bb = sma + std * 2
    lower_bb = sma - std * 2
    return upper_bb, lower_bb


def implement_bb_strategy(data, lower_bb, upper_bb):
    buy_price = [None]
    sell_price = [None]
    bb_signal = [None]
    signal = 0

    for i in range(1, len(data)):
        if data[i - 1] > lower_bb[i - 1] and data[i] < lower_bb[i]:
            if signal != 1:
                buy_price.append(data[i])
                sell_price.append(np.nan)
                signal = 1
                bb_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                bb_signal.append(0)
        elif data[i - 1] < upper_bb[i - 1] and data[i] > upper_bb[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(data[i])
                signal = -1
                bb_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                bb_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            bb_signal.append(0)

    return buy_price, sell_price, bb_signal


if __name__ == "__main__":
    figi_df = get_historic_data(figi="BBG004731032")
    figi_df['sma_20'] = sma(figi_df['close'], 5)
    figi_df['upper_bb'], figi_df['lower_bb'] = bb(figi_df['close'], figi_df['sma_20'], 5)

    buy_price, sell_price, bb_signal = implement_bb_strategy(figi_df['close'], figi_df['lower_bb'], figi_df['upper_bb'])
    figi_df['buy_price'] = buy_price
    figi_df['sell_price'] = sell_price
    figi_df['bb_signal'] = bb_signal

    print(figi_df)
