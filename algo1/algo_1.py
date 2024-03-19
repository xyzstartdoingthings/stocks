
from pathlib import Path
import numpy as np
import pandas as pd
import os
from utils import *
from pine_functions import *

def algo1(ticker, dziwne_maPeriod = 52, dziwne_maPeriodSmooth = 10, supertrend_atrLength = 9, supertrend_atrMul = 3.9):
    data_path = Path(os.getcwd()).parent # perhaps set to external harddrive to accomodate large amount of data
    file = ticker+".csv"
    path = data_path / 'stock price data'/"company stock price daily"/file
    stock = pd.read_csv(path)
    stock['date'] = pd.to_datetime(stock['date'])
    stock = stock.sort_values(by='date').reset_index(drop=True)

    #dziwne
    ma_type = "EMA"
    dziwne_maPeriod = 52
    dziwne_maPeriodSmooth = 10
    stock = pine_dziwne(ma_type, dziwne_maPeriod, dziwne_maPeriodSmooth, stock) 
     
    #supertrend
    supertrend_atrLength = 9  # ATR Period
    supertrend_atrMul = 3.9  # ATR Multiplier
    wicks = True  # Whether to take wicks into account
    changeATR = True
    stock = pine_supertrend(supertrend_atrLength, supertrend_atrMul, stock, changeATR, wicks)

    #QQE MOD
    rsi_period = 6
    sf = 5
    qqe = 3
    src = "close"
    bb_length = 50
    bb_mul = 0.35
    rsi_period2 = 6
    sf2 = 5
    qqe2 = 1.61
    thres2 = 3
    src2 = "close"

    stock = pine_QQEMOD(rsi_period, sf, qqe, src,bb_length, bb_mul, rsi_period2, sf2, qqe2, thres2,src2,stock)

    long = False
    short = False
    stop_loss_price = False
    stop_loss=False
    stop_gain=False
    buy_price = False
    for i in range(len(stock)):
        if i == 0:
            if stock.loc[i, "dziwne_trend"] == 1 and stock.loc[i,"supertrend_dir"] == 1 and (stock.loc[i, "QQE Dir"]!= "Nan" and stock.loc[i, "QQE Dir"] >=0) and stop_loss != "long" and stop_gain != "long":
                stock.loc[i, "order"] = 1
                long = True
                stop_loss = False
                stop_gain = False
                buy_price = stock.loc[i-1, "close"]
                stop_loss_price = stock.loc[i-1, "ha_o_smooth"]
            elif stock.loc[i, "dziwne_trend"] == -1 and stock.loc[i,"supertrend_dir"] == -1 and (stock.loc[i, "QQE Dir"]!= "Nan" and stock.loc[i, "QQE Dir"] <0) and stop_loss != "short" and stop_gain != "short":
                stock.loc[i, "order"] = -1
                long = True
                stop_loss = False
                stop_gain = False
                buy_price = stock.loc[i-1, "close"]
                stop_loss_price = stock.loc[i-1, "ha_o_smooth"]
            else:
                stock.loc[i, "order"] = 0
        else:
            if long:
                if stock.loc[i, "close"] <= stop_loss_price:
                    stock.loc[i, "order"] = 0
                    long = False
                    stop_loss = "long"
                    continue
                elif stock.loc[i, "close"] >= buy_price * 2 - stop_loss_price:
                    stock.loc[i, "order"] = 0
                    long = False
                    # stop_gain = "long"
                    continue
                # elif stock.loc[i, "dziwne_trend"] != 1 or stock.loc[i,"supertrend_dir"] != 1 or (stock.loc[i, "QQE Dir"]== "Nan" or stock.loc[i, "QQE Dir"] < 0):
                #     stock.loc[i, "order"] = 0
                #     long = False
                #     continue
            elif short:
                if stock.loc[i, "close"] >= stop_loss_price:
                    stock.loc[i, "order"] = 0
                    short = False
                    stop_loss = "short"
                    continue
                elif stock.loc[i, "close"] <= buy_price * 2 - stop_loss_price:
                    stock.loc[i, "order"] = 0
                    short = False
                    # stop_gain = "short"
                    continue
                # elif stock.loc[i, "dziwne_trend"] != -1 or stock.loc[i,"supertrend_dir"] != -1 or (stock.loc[i, "QQE Dir"]== "Nan" or stock.loc[i, "QQE Dir"] >= 0):
                #     stock.loc[i, "order"] = 0
                #     short = False
                #     continue
            if stock.loc[i, "dziwne_trend"] == 1 and stock.loc[i,"supertrend_dir"] == 1 and (stock.loc[i, "QQE Dir"]!= "Nan" and stock.loc[i, "QQE Dir"] >=0) and stop_loss != "long" and stop_gain != "long" and not long:
                stock.loc[i, "order"] = 1
                long = True
                stop_loss = False
                stop_gain = False
                buy_price = stock.loc[i-1, "close"]
                stop_loss_price = stock.loc[i-1, "ha_o_smooth"]
            elif stock.loc[i, "dziwne_trend"] == -1 and stock.loc[i,"supertrend_dir"] == -1 and (stock.loc[i, "QQE Dir"]!= "Nan" and stock.loc[i, "QQE Dir"] <0) and stop_loss != "short" and stop_gain != "short" and not short:
                stock.loc[i, "order"] = -1
                short = True
                stop_loss = False
                stop_gain = False
                buy_price = stock.loc[i-1, "close"]
                stop_loss_price = stock.loc[i-1, "ha_o_smooth"]
            else:
                stock.loc[i, "order"] = stock.loc[i-1, "order"]
    return stock