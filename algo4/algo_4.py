
from pathlib import Path
import numpy as np
import pandas as pd
import os
from utils import *
from pine_functions import *

def algo4(ticker, sma_length = 200, rsi_period = 10, long_range = 30, oversell = 30, overbuy = 70, midline_buy=40, midline_sell=60,day_max=11, percent_trend=0.5, percent_trend2=1):
    file = ticker+".csv"
    data_path = Path(os.getcwd()) # perhaps set to external harddrive to accomodate large amount of data
    path = data_path / 'stock price data'/"company stock price daily"/file
    stock = pd.read_csv(path)
    stock['date'] = pd.to_datetime(stock['date'])
    stock = stock.sort_values(by='date').reset_index(drop=True) 
    stock["sma"] = pine_sma(stock["close"], sma_length)
    stock["rsi"] = pine_rsi(stock["close"], rsi_period)
    stock = stock.dropna().reset_index(drop=True)

    day_count = 0
    long_in = 0
    short_in = 0
    long_out = 0
    short_out = 0
    stock.loc[:, "order"] = 0
    for i in range(1,len(stock)):
        stock.loc[i,"long_trend"] = (stock.loc[i,"sma"] > stock.loc[i-1,"sma"])
        stock.loc[i,"short_trend"] = (stock.loc[i,"sma"] < stock.loc[i-1,"sma"])
        if i <= long_range:
            stock.loc[i, "order"] = 0
        else:
            if long_in == 1:
                stock.loc[i, "order"] = 1
                day_count+=1
                long_in = 0
                if stock.loc[i, "rsi"] >= midline_buy:
                    long_out = 1
            elif short_in ==1:
                stock.loc[i, "order"] = -1
                day_count+=1
                short_in = 0
                if stock.loc[i, "rsi"] <= midline_sell:
                    short_out = 1
            elif long_out == 1:
                stock.loc[i, "order"] = 0
                day_count = 0
                long_out = 0
            elif short_out == 1:
                stock.loc[i, "order"] = 0
                day_count = 0
                short_out = 0
            elif stock.loc[i-1, "order"] == 1:
                if stock.loc[i, "rsi"] >= midline_buy or day_count >= day_max:
                    long_out = 1
                stock.loc[i, "order"] = stock.loc[i-1, "order"]
                day_count+=1
            elif stock.loc[i-1, "order"] == -1:
                if stock.loc[i, "rsi"] <= midline_sell or day_count >= day_max:
                    short_out = 1
                stock.loc[i, "order"] = stock.loc[i-1, "order"]
                day_count+=1
            # elif stock.loc[i, "close"] >= stock.loc[i,"sma"]:
            elif sum(stock.loc[i-long_range:i, "close"] >= stock.loc[i,"sma"])/long_range >= percent_trend and sum(stock.loc[i-long_range:i,"long_trend"]) >= percent_trend2*long_range:
                if stock.loc[i, "rsi"] <= oversell:
                    long_in = 1
                stock.loc[i,"order"] = 0
            # elif stock.loc[i, "close"] <= stock.loc[i,"sma"]:
            elif sum(stock.loc[i-long_range:i, "close"] <= stock.loc[i,"sma"])/long_range >= percent_trend and sum(stock.loc[i-long_range:i,"short_trend"]) >= percent_trend2*long_range:
                if stock.loc[i, "rsi"] >= overbuy:
                    short_in = 1
                stock.loc[i, "order"] = 0
            else:
                stock.loc[i,"order"] = 0
                day_count=0
    return stock


