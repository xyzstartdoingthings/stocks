from pine_functions import *
import os
from utils import *

def algo2(ticker, atr_len=13, atr_changeATR=True, macd_fastLen=13, macd_slowLen=34, macd_src="close", macd_signalSmooth=9, macd_oscMA="EMA", macd_sigMA="EMA", macd_peakLen=5, gain_ratio=2, loss_ratio=1.5, peak2_len=20, peak3_len=40, peak2_diff=1/11):
    file = ticker+".csv"
    # perhaps set to external harddrive to accomodate large amount of data
    data_path = Path(os.getcwd()).parent
    path = data_path / 'stock price data'/"company stock price daily"/file
    stock = pd.read_csv(path)
    stock['date'] = pd.to_datetime(stock['date'])
    stock = stock.sort_values(by='date').reset_index(drop=True)

    # atr
    stock = pine_atr(atr_len, stock, atr_changeATR)
    # macd
    stock = pine_MACD(macd_fastLen, macd_slowLen, macd_src,
                      macd_signalSmooth, macd_oscMA, macd_sigMA, stock)

    stock = peak_calc(stock, "close", macd_peakLen, False)
    stock = peak_calc(stock, "MACD_Hist", macd_peakLen, True)

    peak_dict = FixedSizeFIFO()
    short_mark = 0
    trough_dict = FixedSizeFIFO()
    long_mark = 0
    stock["order"] = 0
    stoploss = 0
    stopgain = 0
    sb_date = 0
    for i in range(1, len(stock)):
        if stock.loc[i-1, "order"] == 1:
            if stock.loc[i, "close"] >= stoploss and stock.loc[i, "close"] <= stopgain:
                stock.loc[i, "order"] = 1
            else:
                stock.loc[i, "order"] = 0
                stoploss = 0
                stopgain = 0
        elif stock.loc[i-1, "order"] == -1:
            if stock.loc[i, "close"] <= stoploss and stock.loc[i, "close"] >= stopgain:
                stock.loc[i, "order"] = -1
            else:
                stock.loc[i, "order"] = 0
                stoploss = 0
                stopgain = 0
        else:
            if short_mark == 1:
                if i >= sb_date:
                    if stock.loc[i, "MACD_Hist"] < stock.loc[i-1, "MACD_Hist"]:
                        stock.loc[i, "order"] = -1
                        stoploss = stock.loc[i, "close"] + \
                            stock.loc[i, "atr"] * loss_ratio
                        stopgain = stock.loc[i, "close"] - \
                            gain_ratio * stock.loc[i, "atr"]
                        short_mark = 0
                        sb_date = 0
                else:
                    continue
            elif long_mark == 1:
                if i >= sb_date:
                    if stock.loc[i, "MACD_Hist"] > stock.loc[i-1, "MACD_Hist"]:
                        stock.loc[i, "order"] = 1
                        stoploss = stock.loc[i, "close"] - \
                            stock.loc[i, "atr"] * loss_ratio
                        stopgain = stock.loc[i, "close"] + \
                            gain_ratio * stock.loc[i, "atr"]
                        long_mark = 0
                        sb_date = 0
                else:
                    continue
            elif stock.loc[i, "MACD_Hist_is_peak"] == 1 and (stock.loc[i, "close_is_peak"] == 1 or stock.loc[i-1, "close_is_peak"] == 1):
                peak = dict()
                peak["date"] = stock.loc[i, "date"]
                peak["close"] = max(stock.loc[i, "close"],
                                    stock.loc[i-1, "close"])
                peak["MACD_Hist"] = stock.loc[i, "MACD_Hist"]
                peak_dict.add(peak)
                if peak_dict.length() == 2:
                    if (peak_dict.get(0)["close"] <= peak_dict.get(1)["close"]) and (peak_dict.get(0)["MACD_Hist"] >= peak_dict.get(1)["MACD_Hist"]) and (abs(peak_dict.get(0)["MACD_Hist"])/abs(peak_dict.get(1)["MACD_Hist"]) > 1/peak2_diff):
                        if (peak_dict.get(1)["date"] - peak_dict.get(0)["date"]).days <=peak2_len:
                            short_mark = 1
                            sb_date = i+macd_peakLen//2
                elif peak_dict.length() == 3:
                    # if (peak_dict.get(1)["close"] <= peak_dict.get(2)["close"]) and (peak_dict.get(1)["MACD_Hist"] >= peak_dict.get(2)["MACD_Hist"]) and (abs(peak_dict.get(1)["MACD_Hist"])/abs(peak_dict.get(2)["MACD_Hist"]) > 11/1):
                    #     if (peak_dict.get(2)["date"] - peak_dict.get(1)["date"]).days <=20:
                    #         short_mark = 1
                    #         sb_date = i+peak_len//2
                    if (peak_dict.get(0)["close"] <= peak_dict.get(1)["close"] <= peak_dict.get(2)["close"]) and (peak_dict.get(0)["MACD_Hist"] >= peak_dict.get(1)["MACD_Hist"] >= peak_dict.get(2)["MACD_Hist"]):
                        if (peak_dict.get(2)["date"] - peak_dict.get(0)["date"]).days <= peak3_len:
                            short_mark = 1
                            sb_date = i+macd_peakLen//2
            elif stock.loc[i, "MACD_Hist_is_peak"] == -1 and (stock.loc[i, "close_is_peak"] == -1 or stock.loc[i-1, "close_is_peak"] == -1):
                trough = dict()
                trough["date"] = stock.loc[i, "date"]
                trough["close"] = max(
                    stock.loc[i, "close"], stock.loc[i-1, "close"])
                trough["MACD_Hist"] = stock.loc[i, "MACD_Hist"]
                trough_dict.add(trough)
                if trough_dict.length() == 2:
                    if (trough_dict.get(0)["close"] >= trough_dict.get(1)["close"]) and (trough_dict.get(0)["MACD_Hist"] <= trough_dict.get(1)["MACD_Hist"]) and (abs(trough_dict.get(0)["MACD_Hist"])/abs(trough_dict.get(1)["MACD_Hist"]) < peak2_diff):
                        if (trough_dict.get(1)["date"] - trough_dict.get(0)["date"]).days <=peak2_len:
                            long_mark = 1
                            sb_date = i+macd_peakLen//2
                elif trough_dict.length() == 3:
                    # if (trough_dict.get(1)["close"] >= trough_dict.get(2)["close"]) and (trough_dict.get(1)["MACD_Hist"] <= trough_dict.get(2)["MACD_Hist"]) and (abs(trough_dict.get(1)["MACD_Hist"])/abs(trough_dict.get(2)["MACD_Hist"]) < 1/11):
                    #     if (trough_dict.get(2)["date"] - trough_dict.get(1)["date"]).days <=20:
                    #         long_mark = 1
                    #         sb_date = i+peak_len//2
                    if (trough_dict.get(0)["close"] >= trough_dict.get(1)["close"] >= trough_dict.get(2)["close"]) and (trough_dict.get(0)["MACD_Hist"] <= trough_dict.get(1)["MACD_Hist"] <= trough_dict.get(2)["MACD_Hist"]):
                        if (trough_dict.get(2)["date"] - trough_dict.get(0)["date"]).days <= peak3_len:
                            long_mark = 1
                            sb_date = i+macd_peakLen//2
            else:
                continue
    return stock


def algo2_test(ticker, atr_len=13, atr_changeATR=True, macd_fastLen=13, macd_slowLen=34, macd_src="close", macd_signalSmooth=9, macd_oscMA="EMA", macd_sigMA="EMA", macd_peakLen=5, gain_ratio=2, loss_ratio=1.5, peak2_len=20, peak3_len=40, peak2_diff=1/11):
    file = ticker+".csv"
    # perhaps set to external harddrive to accomodate large amount of data
    data_path = Path(os.getcwd()).parent
    path = data_path / 'stock price test data'/"company stock price daily"/file
    stock = pd.read_csv(path)
    stock['date'] = pd.to_datetime(stock['date'])
    stock = stock.sort_values(by='date').reset_index(drop=True)

    # atr
    stock = pine_atr(atr_len, stock, atr_changeATR)
    # macd
    stock = pine_MACD(macd_fastLen, macd_slowLen, macd_src,
                      macd_signalSmooth, macd_oscMA, macd_sigMA, stock)

    stock = peak_calc(stock, "close", macd_peakLen, False)
    stock = peak_calc(stock, "MACD_Hist", macd_peakLen, True)

    peak_dict = FixedSizeFIFO()
    short_mark = 0
    trough_dict = FixedSizeFIFO()
    long_mark = 0
    stock["order"] = 0
    stoploss = 0
    stopgain = 0
    sb_date = 0
    for i in range(1, len(stock)):
        if stock.loc[i-1, "order"] == 1:
            if stock.loc[i, "close"] >= stoploss and stock.loc[i, "close"] <= stopgain:
                stock.loc[i, "order"] = 1
            else:
                stock.loc[i, "order"] = 0
                stoploss = 0
                stopgain = 0
        elif stock.loc[i-1, "order"] == -1:
            if stock.loc[i, "close"] <= stoploss and stock.loc[i, "close"] >= stopgain:
                stock.loc[i, "order"] = -1
            else:
                stock.loc[i, "order"] = 0
                stoploss = 0
                stopgain = 0
        else:
            if short_mark == 1:
                if i >= sb_date:
                    if stock.loc[i, "MACD_Hist"] < stock.loc[i-1, "MACD_Hist"]:
                        stock.loc[i, "order"] = -1
                        stoploss = stock.loc[i, "close"] + \
                            stock.loc[i, "atr"] * loss_ratio
                        stopgain = stock.loc[i, "close"] - \
                            gain_ratio * stock.loc[i, "atr"]
                        short_mark = 0
                        sb_date = 0
                else:
                    continue
            elif long_mark == 1:
                if i >= sb_date:
                    if stock.loc[i, "MACD_Hist"] > stock.loc[i-1, "MACD_Hist"]:
                        stock.loc[i, "order"] = 1
                        stoploss = stock.loc[i, "close"] - \
                            stock.loc[i, "atr"] * loss_ratio
                        stopgain = stock.loc[i, "close"] + \
                            gain_ratio * stock.loc[i, "atr"]
                        long_mark = 0
                        sb_date = 0
                else:
                    continue
            elif stock.loc[i, "MACD_Hist_is_peak"] == 1 and (stock.loc[i, "close_is_peak"] == 1 or stock.loc[i-1, "close_is_peak"] == 1):
                peak = dict()
                peak["date"] = stock.loc[i, "date"]
                peak["close"] = max(stock.loc[i, "close"],
                                    stock.loc[i-1, "close"])
                peak["MACD_Hist"] = stock.loc[i, "MACD_Hist"]
                peak_dict.add(peak)
                if peak_dict.length() == 2:
                    if (peak_dict.get(0)["close"] <= peak_dict.get(1)["close"]) and (peak_dict.get(0)["MACD_Hist"] >= peak_dict.get(1)["MACD_Hist"]) and (abs(peak_dict.get(0)["MACD_Hist"])/abs(peak_dict.get(1)["MACD_Hist"]) > 1/peak2_diff):
                        if (peak_dict.get(1)["date"] - peak_dict.get(0)["date"]).days <=peak2_len:
                            short_mark = 1
                            sb_date = i+macd_peakLen//2
                elif peak_dict.length() == 3:
                    # if (peak_dict.get(1)["close"] <= peak_dict.get(2)["close"]) and (peak_dict.get(1)["MACD_Hist"] >= peak_dict.get(2)["MACD_Hist"]) and (abs(peak_dict.get(1)["MACD_Hist"])/abs(peak_dict.get(2)["MACD_Hist"]) > 11/1):
                    #     if (peak_dict.get(2)["date"] - peak_dict.get(1)["date"]).days <=20:
                    #         short_mark = 1
                    #         sb_date = i+peak_len//2
                    if (peak_dict.get(0)["close"] <= peak_dict.get(1)["close"] <= peak_dict.get(2)["close"]) and (peak_dict.get(0)["MACD_Hist"] >= peak_dict.get(1)["MACD_Hist"] >= peak_dict.get(2)["MACD_Hist"]):
                        if (peak_dict.get(2)["date"] - peak_dict.get(0)["date"]).days <= peak3_len:
                            short_mark = 1
                            sb_date = i+macd_peakLen//2
            elif stock.loc[i, "MACD_Hist_is_peak"] == -1 and (stock.loc[i, "close_is_peak"] == -1 or stock.loc[i-1, "close_is_peak"] == -1):
                trough = dict()
                trough["date"] = stock.loc[i, "date"]
                trough["close"] = max(
                    stock.loc[i, "close"], stock.loc[i-1, "close"])
                trough["MACD_Hist"] = stock.loc[i, "MACD_Hist"]
                trough_dict.add(trough)
                if trough_dict.length() == 2:
                    if (trough_dict.get(0)["close"] >= trough_dict.get(1)["close"]) and (trough_dict.get(0)["MACD_Hist"] <= trough_dict.get(1)["MACD_Hist"]) and (abs(trough_dict.get(0)["MACD_Hist"])/abs(trough_dict.get(1)["MACD_Hist"]) < peak2_diff):
                        if (trough_dict.get(1)["date"] - trough_dict.get(0)["date"]).days <=peak2_len:
                            long_mark = 1
                            sb_date = i+macd_peakLen//2
                elif trough_dict.length() == 3:
                    # if (trough_dict.get(1)["close"] >= trough_dict.get(2)["close"]) and (trough_dict.get(1)["MACD_Hist"] <= trough_dict.get(2)["MACD_Hist"]) and (abs(trough_dict.get(1)["MACD_Hist"])/abs(trough_dict.get(2)["MACD_Hist"]) < 1/11):
                    #     if (trough_dict.get(2)["date"] - trough_dict.get(1)["date"]).days <=20:
                    #         long_mark = 1
                    #         sb_date = i+peak_len//2
                    if (trough_dict.get(0)["close"] >= trough_dict.get(1)["close"] >= trough_dict.get(2)["close"]) and (trough_dict.get(0)["MACD_Hist"] <= trough_dict.get(1)["MACD_Hist"] <= trough_dict.get(2)["MACD_Hist"]):
                        if (trough_dict.get(2)["date"] - trough_dict.get(0)["date"]).days <= peak3_len:
                            long_mark = 1
                            sb_date = i+macd_peakLen//2
            else:
                continue
    return stock


def algo2_trade(ticker, atr_len=13, atr_changeATR=True, macd_fastLen=13, macd_slowLen=34, macd_src="close", macd_signalSmooth=9, macd_oscMA="EMA", macd_sigMA="EMA", macd_peakLen=5, gain_ratio=2, loss_ratio=1.5, peak2_len=20, peak3_len=40, peak2_diff=1/11):
    file = ticker+".csv"
    # perhaps set to external harddrive to accomodate large amount of data
    data_path = Path(os.getcwd()).parent
    path = data_path / 'stock price test data'/"company stock price daily"/file
    stock = pd.read_csv(path)
    stock['date'] = pd.to_datetime(stock['date'])
    stock = stock.sort_values(by='date').reset_index(drop=True)

    # atr
    stock = pine_atr(atr_len, stock, atr_changeATR)
    # macd
    stock = pine_MACD(macd_fastLen, macd_slowLen, macd_src,
                      macd_signalSmooth, macd_oscMA, macd_sigMA, stock)

    stock = peak_calc(stock, "close", macd_peakLen, False)
    stock = peak_calc(stock, "MACD_Hist", macd_peakLen, True)

    peak_dict = FixedSizeFIFO()
    short_mark = 0
    trough_dict = FixedSizeFIFO()
    long_mark = 0
    stock["order"] = 0
    stoploss = 0
    stopgain = 0
    sb_date = 0
    for i in range(1, len(stock)):
        if stock.loc[i-1, "order"] == 1:
            if stock.loc[i, "close"] >= stoploss and stock.loc[i, "close"] <= stopgain:
                stock.loc[i, "order"] = 1
            else:
                stock.loc[i, "order"] = 0
                stoploss = 0
                stopgain = 0
        elif stock.loc[i-1, "order"] == -1:
            if stock.loc[i, "close"] <= stoploss and stock.loc[i, "close"] >= stopgain:
                stock.loc[i, "order"] = -1
            else:
                stock.loc[i, "order"] = 0
                stoploss = 0
                stopgain = 0
        else:
            if short_mark == 1:
                if i >= sb_date:
                    if stock.loc[i, "MACD_Hist"] < stock.loc[i-1, "MACD_Hist"]:
                        stock.loc[i, "order"] = -1
                        stoploss = stock.loc[i, "close"] + \
                            stock.loc[i, "atr"] * loss_ratio
                        stopgain = stock.loc[i, "close"] - \
                            gain_ratio * stock.loc[i, "atr"]
                        short_mark = 0
                        sb_date = 0
                else:
                    continue
            elif long_mark == 1:
                if i >= sb_date:
                    if stock.loc[i, "MACD_Hist"] > stock.loc[i-1, "MACD_Hist"]:
                        stock.loc[i, "order"] = 1
                        stoploss = stock.loc[i, "close"] - \
                            stock.loc[i, "atr"] * loss_ratio
                        stopgain = stock.loc[i, "close"] + \
                            gain_ratio * stock.loc[i, "atr"]
                        long_mark = 0
                        sb_date = 0
                else:
                    continue
            elif stock.loc[i, "MACD_Hist_is_peak"] == 1 and (stock.loc[i, "close_is_peak"] == 1 or stock.loc[i-1, "close_is_peak"] == 1):
                peak = dict()
                peak["date"] = stock.loc[i, "date"]
                peak["close"] = max(stock.loc[i, "close"],
                                    stock.loc[i-1, "close"])
                peak["MACD_Hist"] = stock.loc[i, "MACD_Hist"]
                peak_dict.add(peak)
                if peak_dict.length() == 2:
                    if (peak_dict.get(0)["close"] <= peak_dict.get(1)["close"]) and (peak_dict.get(0)["MACD_Hist"] >= peak_dict.get(1)["MACD_Hist"]) and (abs(peak_dict.get(0)["MACD_Hist"])/abs(peak_dict.get(1)["MACD_Hist"]) > 1/peak2_diff):
                        if (peak_dict.get(1)["date"] - peak_dict.get(0)["date"]).days <=peak2_len:
                            short_mark = 1
                            sb_date = i+macd_peakLen//2
                elif peak_dict.length() == 3:
                    # if (peak_dict.get(1)["close"] <= peak_dict.get(2)["close"]) and (peak_dict.get(1)["MACD_Hist"] >= peak_dict.get(2)["MACD_Hist"]) and (abs(peak_dict.get(1)["MACD_Hist"])/abs(peak_dict.get(2)["MACD_Hist"]) > 11/1):
                    #     if (peak_dict.get(2)["date"] - peak_dict.get(1)["date"]).days <=20:
                    #         short_mark = 1
                    #         sb_date = i+peak_len//2
                    if (peak_dict.get(0)["close"] <= peak_dict.get(1)["close"] <= peak_dict.get(2)["close"]) and (peak_dict.get(0)["MACD_Hist"] >= peak_dict.get(1)["MACD_Hist"] >= peak_dict.get(2)["MACD_Hist"]):
                        if (peak_dict.get(2)["date"] - peak_dict.get(0)["date"]).days <= peak3_len:
                            short_mark = 1
                            sb_date = i+macd_peakLen//2
            elif stock.loc[i, "MACD_Hist_is_peak"] == -1 and (stock.loc[i, "close_is_peak"] == -1 or stock.loc[i-1, "close_is_peak"] == -1):
                trough = dict()
                trough["date"] = stock.loc[i, "date"]
                trough["close"] = max(
                    stock.loc[i, "close"], stock.loc[i-1, "close"])
                trough["MACD_Hist"] = stock.loc[i, "MACD_Hist"]
                trough_dict.add(trough)
                if trough_dict.length() == 2:
                    if (trough_dict.get(0)["close"] >= trough_dict.get(1)["close"]) and (trough_dict.get(0)["MACD_Hist"] <= trough_dict.get(1)["MACD_Hist"]) and (abs(trough_dict.get(0)["MACD_Hist"])/abs(trough_dict.get(1)["MACD_Hist"]) < peak2_diff):
                        if (trough_dict.get(1)["date"] - trough_dict.get(0)["date"]).days <=peak2_len:
                            long_mark = 1
                            sb_date = i+macd_peakLen//2
                elif trough_dict.length() == 3:
                    # if (trough_dict.get(1)["close"] >= trough_dict.get(2)["close"]) and (trough_dict.get(1)["MACD_Hist"] <= trough_dict.get(2)["MACD_Hist"]) and (abs(trough_dict.get(1)["MACD_Hist"])/abs(trough_dict.get(2)["MACD_Hist"]) < 1/11):
                    #     if (trough_dict.get(2)["date"] - trough_dict.get(1)["date"]).days <=20:
                    #         long_mark = 1
                    #         sb_date = i+peak_len//2
                    if (trough_dict.get(0)["close"] >= trough_dict.get(1)["close"] >= trough_dict.get(2)["close"]) and (trough_dict.get(0)["MACD_Hist"] <= trough_dict.get(1)["MACD_Hist"] <= trough_dict.get(2)["MACD_Hist"]):
                        if (trough_dict.get(2)["date"] - trough_dict.get(0)["date"]).days <= peak3_len:
                            long_mark = 1
                            sb_date = i+macd_peakLen//2
            else:
                continue
    return stock, short_mark, long_mark, peak_dict, trough_dict, stoploss, stopgain
