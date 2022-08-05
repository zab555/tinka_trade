from datetime import timedelta
import time

import pandas as pd
import numpy as np
from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

TOKEN = ''

companies_to_track = {
    'SBER': 'BBG004730N88',
    'LKOH': 'BBG004731032',
    'GAZP': 'BBG004730RP0',
}
pd.set_option('display.max_columns', None)

# CANDLE_INTERVAL_1_MIN
# CANDLE_INTERVAL_5_MIN
# CANDLE_INTERVAL_15_MIN
# CANDLE_INTERVAL_HOUR
# CANDLE_INTERVAL_DAY
CANDLE_INTERVAL = CandleInterval.CANDLE_INTERVAL_5_MIN
RSI_WINDOW = 14
BB_MEAN_WINDOW = 20
BB_STD_WINDOW = 5


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


# Returns RSI values
def rsi(close, periods=RSI_WINDOW):
    close_delta = close.diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi


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
    while True:
        time_start = time.time()
        for company_name, company_figi in companies_to_track.items():
            figi_df = get_historic_data(figi=company_figi)
            figi_df['sma_20'] = sma(figi_df['close'], BB_MEAN_WINDOW)
            figi_df['upper_bb'], figi_df['lower_bb'] = bb(figi_df['close'], figi_df['sma_20'], BB_STD_WINDOW)

            buy_price, sell_price, bb_signal = implement_bb_strategy(figi_df['close'], figi_df['lower_bb'], figi_df['upper_bb'])
            figi_df['buy_price'] = buy_price
            figi_df['sell_price'] = sell_price
            figi_df['bb_signal'] = bb_signal

            figi_df['rsi'] = rsi(figi_df['close'])

            print(company_name.upper())
            if figi_df.tail(1)['bb_signal'].to_list()[0] != 0:
                print("\033[1;32m " + str(figi_df.tail(1)))
            else:
                print(figi_df.tail(1))

            time.sleep(5)

        time_end = time.time()
        exec_time = time_end - time_start

        print(f'next round in {300 - exec_time} sec')
        time.sleep(300 - exec_time)
