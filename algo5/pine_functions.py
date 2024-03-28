import numpy as np
import pandas as pd
def pine_ema(data, length):
    """
    Calculate the Exponential Moving Average (EMA) equivalent to the Pine Script function.
    :param data: Pandas Series containing the data to calculate EMA on (e.g., close prices).
    :param length: The length of the EMA.
    :return: Pandas Series containing the calculated EMA.
    """
    alpha = 2 / (length + 1)
    ema_values = [np.nan for i in range(data.isna().sum())]
    data_new = data.dropna()
    # Calculate the first EMA value using SMA (Simple Moving Average)
    first_ema = data_new.rolling(window=length).mean().iloc[length - 1]

    # Initialize a list to store EMA values
    ema_values.append(first_ema)

    # Calculate the rest of the EMA values
    for price in data_new.iloc[length:]:
        new_ema = alpha * price + (1 - alpha) * ema_values[-1]
        ema_values.append(new_ema)

    # Fill the initial part with NaN
    ema_series = pd.Series([np.nan] * (length - 1) + ema_values, index=data.index)
    return ema_series

def pine_sma(data, length):
    """
    Calculate the Simple Moving Average (SMA) equivalent to the Pine Script function.
    :param data: Pandas Series containing the data to calculate SMA on.
    :param length: The length of the SMA calculation period.
    :return: Pandas Series containing the calculated SMA.
    """
    return data.rolling(window=length).mean()

def pine_rma(data, length):
    """
    Calculate the Rolling Moving Average (RMA) equivalent to the Pine Script function.
    :param data: Pandas Series containing the data to calculate RMA on (e.g., close prices).
    :param length: The length of the RMA.
    :return: Pandas Series containing the calculated RMA.
    """
    alpha = 1 / length

    # Initialize the RMA series with NaN values
    rma = pd.Series(index=data.index)

    # Calculate the first RMA value using SMA (Simple Moving Average)
    first_rma = data.rolling(window=length).mean().iloc[length - 1]
    rma.iloc[length - 1] = first_rma

    # Calculate the rest of the RMA values
    for i in range(length, len(data)):
        rma.iloc[i] = alpha * data.iloc[i] + (1 - alpha) * rma.iloc[i - 1]

    return rma

def pine_rsi(data, period):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = pine_rma(gain, period)
    avg_loss = pine_rma(loss, period)
    rs = avg_gain/avg_loss
    rsi = 100-(100/(1+rs))
    return rsi

def pine_cross(data1, data2):
    data1_prev = data1.shift(1)
    data2_prev = data2.shift(1)
    return ((data1 > data2) & (data1_prev <= data2_prev))

def pine_stdev(src, length):
    return src.rolling(window=length).std(ddof=0)

def pine_dziwne(ma_type, ma_period, ma_period_smoothing, stock):
    if ma_type=="EMA":
        moving_average=pine_ema
    elif ma_type=="SMA":
        moving_average=pine_sma
    # Re-calculate the moving averages with the updated function
    stock['o_ma'] = moving_average(stock['open'], ma_period)
    stock['c_ma'] = moving_average(stock['close'], ma_period)
    stock['h_ma'] = moving_average(stock['high'], ma_period)
    stock['l_ma'] = moving_average(stock['low'], ma_period)
    stock['o_ma'].fillna(stock["open"], inplace=True)
    stock['c_ma'].fillna(stock["close"], inplace=True)
    stock['h_ma'].fillna(stock["high"], inplace=True)
    stock['l_ma'].fillna(stock["low"], inplace=True)
    # Re-calculate Heikin Ashi and smoothed values
    stock["ha_o"] = (stock['o_ma'] + stock['c_ma']) / 2
    stock['ha_c'] = (stock['o_ma'] + stock['h_ma'] + stock['l_ma'] + stock['c_ma']) / 4
    for i in range(len(stock)):
        if i!=0:
            stock.loc[i,"ha_o"] = (stock.loc[i-1,"ha_o"] + stock.loc[i-1,"ha_c"])/2
    # stock['ha_o'] = (stock['ha_o'].shift(1).fillna(stock['ha_o']) + stock['ha_c'].shift(1).fillna(stock['ha_c']))/2
    stock['ha_h'] = stock[['h_ma', 'ha_o', 'ha_c']].max(axis=1)
    stock['ha_l'] = stock[['l_ma', 'ha_o', 'ha_c']].min(axis=1)

    stock['ha_o_smooth'] = moving_average(stock['ha_o'], ma_period_smoothing)
    stock['ha_c_smooth'] = moving_average(stock['ha_c'], ma_period_smoothing)
    stock['ha_h_smooth'] = moving_average(stock['ha_h'], ma_period_smoothing)
    stock['ha_l_smooth'] = moving_average(stock['ha_l'], ma_period_smoothing)

    # Update Trend Determination
    stock['dziwne_trend'] = stock.apply(lambda row: 1 if row['ha_c_smooth'] >= row['ha_o_smooth'] else -1, axis=1)
    return stock

def pine_atr(length,stock,changeATR):
    # Calculate True Range and Average True Range (ATR)
    stock['tr0'] = abs(stock['high'] - stock['low'])
    stock['tr1'] = abs(stock['high'] - stock['close'].shift())
    stock['tr2'] = abs(stock['low'] - stock['close'].shift())
    stock['tr'] = stock[['tr0', 'tr1', 'tr2']].max(axis=1)
    if changeATR:
        stock['atr'] = pine_rma(stock['tr'], length)
    else:
        stock['atr'] = pine_sma(stock['tr'], length)
    return stock

def pine_atr_stoplossfinder(stock, length=8, smoothing=pine_rma, m=1.5,src1="high", src2="low"):
    for i in range(len(stock)):
        if i==0:
            stock.loc[i,"tr"] = stock.loc[i, "high"] -stock.loc[i, "low"]
        else:
            stock.loc[i,"tr"] = max(max(stock.loc[i, "high"] -stock.loc[i, "low"], abs(stock.loc[i, "high"]-stock.loc[i-1, "close"])), abs(stock.loc[i, "low"]-stock.loc[i-1, "close"]))
    a = smoothing(stock["tr"], length) * m
    x = smoothing(stock["tr"], length) * m + stock[src1]
    x2 = stock[src2] - smoothing(stock["tr"], length) * m
    stock["atr_shortStopLoss"] = x
    stock["atr_longStopLoss"] = x2
    return stock

def pine_supertrend(length, mult, stock, changeATR, wicks):
    stock = pine_atr(length, stock, changeATR)
    # Calculate highPrice and lowPrice based on wicks
    stock['highPrice'] = stock['high'] if wicks else stock['close']
    stock['lowPrice'] = stock['low'] if wicks else stock['close']

    # Source (hl2)
    stock['src'] = (stock['high'] + stock['low']) / 2

    # Determine if the current candlestick is a Doji
    stock['doji4price'] = (stock['open'] == stock['close']) & (stock['open'] == stock['low']) & (stock['open'] == stock['high'])

    # Long and Short Stop Calculation
    stock['longStop'] = stock['src'] - mult * stock['atr']

    for i in range(1, len(stock)):
        if i==1:
            stock.loc[i,'longStopPrev'] = stock.loc[i,'longStop']
        else:
            stock.loc[i,'longStopPrev'] = stock.loc[i-1,'longStop']
        if stock.loc[i-1, "close"] > stock.loc[i-1, "longStopPrev"]:
            stock.loc[i,'longStop'] = max(stock['longStop'][i], stock['longStopPrev'][i])

    stock['shortStop'] = stock['src'] + mult * stock['atr']

    for i in range(1, len(stock)):
        if i==1:
            stock.loc[i,'shortStopPrev'] = stock.loc[i,'shortStop']
        else:
            stock.loc[i,'shortStopPrev'] = stock.loc[i-1,'shortStop']
        if stock.loc[i-1, "close"] < stock.loc[i-1, "shortStopPrev"]:
            stock.loc[i,'shortStop'] = min(stock['shortStop'][i], stock['shortStopPrev'][i])

    # Trend Calculation
    stock['supertrend_dir'] = 1
    for i in range(1, len(stock)):
        if stock['supertrend_dir'][i-1] == -1 and stock['close'][i] > stock['shortStopPrev'][i]:
            stock.at[i, 'supertrend_dir'] = 1
        elif stock['supertrend_dir'][i-1] == 1 and stock['close'][i] < stock['longStopPrev'][i]:
            stock.at[i, 'supertrend_dir'] = -1
        else:
            stock.at[i, 'supertrend_dir'] = stock['supertrend_dir'][i-1]
    return stock

def pine_QQEMOD(rsi_period, sf, qqe, src,bb_length, bb_mul, rsi_period2, sf2, qqe2, thres2,src2,stock):
    wilders_period = rsi_period * 2 - 1

    stock["rsi"] = pine_rsi(stock[src], rsi_period)
    stock["rsi_ma"] = pine_ema(stock["rsi"], sf)
    stock["AtrRsi"] = abs(stock["rsi_ma"].shift(1) - stock["rsi_ma"])
    stock["MaAtrRsi"] = pine_ema(stock["AtrRsi"], wilders_period)
    stock["dar"] = pine_ema(stock["MaAtrRsi"], wilders_period) *qqe

    stock["newshortband"] = stock["rsi_ma"] + stock["dar"]
    stock["newlongband"] = stock["rsi_ma"] - stock["dar"]
    for i in range(len(stock)):
        if i<stock["newlongband"].isna().sum():
            continue
        elif i == stock["newlongband"].isna().sum():
            stock.loc[i, "longband"] = stock.loc[i, "newlongband"]
            stock.loc[i, "shortband"] = stock.loc[i, "newshortband"]
        else:
            if stock["rsi_ma"][i-1] > stock["longband"][i-1] and stock["rsi_ma"][i] > stock["longband"][i-1]:
                stock.loc[i, "longband"] = max(stock["newlongband"][i], stock["longband"][i-1])
            else:
                stock.loc[i, "longband"] = stock.loc[i, "newlongband"]
            if stock["rsi_ma"][i-1] < stock["shortband"][i-1] and stock["rsi_ma"][i] < stock["shortband"][i-1]:
                stock.loc[i, "shortband"] = min(stock["newshortband"][i], stock["shortband"][i-1])
            else:
                stock.loc[i, "shortband"] = stock.loc[i, "newshortband"]

    cross_1 = pine_cross(stock["longband"].shift(1), stock["rsi_ma"])
    cross_temp = pine_cross(stock["rsi_ma"],stock["shortband"].shift(1))
    trend = pd.Series()
    for i in range(len(cross_1)):
        if cross_temp[i]:
            trend[i] = 1
        elif cross_1[i]:
            trend[i]=-1
        else:
            if i == 0:
                trend[i] = 1
            else:
                trend[i] = trend[i-1]
        trend.fillna(1)
    for i in range(len(trend)):
        if trend[i] == 1:
            stock.loc[i, "FastAtrRsiTL"] = stock["longband"][i]
        else:
            stock.loc[i, "FastAtrRsiTL"] = stock["shortband"][i]
    ##########

    basis = pine_sma(stock["FastAtrRsiTL"] - 50, bb_length)
    dev = bb_mul * pine_stdev(stock["FastAtrRsiTL"] - 50, bb_length)
    upper = basis + dev
    lower = basis - dev

    # #zero cross
    # QQEzlong = pd.Series([0] * len(stock))
    # QQEzshort = pd.Series([0] * len(stock))
    # for i in range(1, len(QQEzlong)):
    #     QQEzlong[i] = QQEzlong[i-1] + 1 if stock.loc[i, "rsi_ma"] >= 50 else 0
    #     QQEzshort[i] = QQEzshort[i-1] + 1 if stock.loc[i, "rsi_ma"] < 50 else 0

    ########
    wilders_period2 = rsi_period2 * 2 - 1

    stock["rsi2"] = pine_rsi(stock[src2], rsi_period2)
    stock["rsi_ma2"] = pine_ema(stock["rsi2"], sf2)
    # stock["AtrRsi2"] = abs(stock["rsi_ma2"].shift(1) - stock["rsi_ma2"])
    # stock["MaAtrRsi2"] = pine_ema(stock["AtrRsi2"], wilders_period2)
    # stock["dar2"] = pine_ema(stock["MaAtrRsi2"], wilders_period2) *qqe2

    # stock["newshortband2"] = stock["rsi_ma2"] + stock["dar2"]
    # stock["newlongband2"] = stock["rsi_ma2"] - stock["dar2"]
    # for i in range(len(stock)):
    #     if i<stock["newlongband2"].isna().sum():
    #         continue
    #     elif i == stock["newlongband2"].isna().sum():
    #         stock.loc[i, "longband2"] = stock.loc[i, "newlongband2"]
    #         stock.loc[i, "shortband2"] = stock.loc[i, "newshortband2"]
    #     else:
    #         if stock["rsi_ma2"][i-1] > stock["longband2"][i-1] and stock["rsi_ma2"][i] > stock["longband2"][i-1]:
    #             stock.loc[i, "longband2"] = max(stock["newlongband2"][i], stock["longband2"][i-1])
    #         else:
    #             stock.loc[i, "longband2"] = stock.loc[i, "newlongband2"]
    #         if stock["rsi_ma2"][i-1] < stock["shortband2"][i-1] and stock["rsi_ma2"][i] < stock["shortband2"][i-1]:
    #             stock.loc[i, "shortband2"] = min(stock["newshortband2"][i], stock["shortband2"][i-1])
    #         else:
    #             stock.loc[i, "shortband2"] = stock.loc[i, "newshortband2"]

    # cross_2 = pine_cross(stock["longband2"].shift(1), stock["rsi_ma2"])
    # cross_temp2 = pine_cross(stock["rsi_ma2"],stock["shortband2"].shift(1), )
    # trend2 = pd.Series()
    # for i in range(len(cross_2)):
    #     if cross_temp2[i]:
    #         trend2[i] = 1
    #     elif cross_2[i]:
    #         trend2[i]=-1
    #     else:
    #         if i == 0:
    #             trend2[i] = 1
    #         else:
    #             trend2[i] = trend2[i-1]
    #     trend2.fillna(1)
    # for i in range(len(trend2)):
    #     if trend2[i] == 1:
    #         stock.loc[i, "FastAtrRsi2TL"] = stock["longband2"][i]
    #     else:
    #         stock.loc[i, "FastAtrRsi2TL"] = stock["shortband2"][i]
    # #zero cross
    # QQE2zlong = pd.Series([0] * len(stock))
    # QQE2zshort = pd.Series([0] * len(stock))
    # for i in range(1, len(QQE2zlong)):
    #     QQE2zlong[i] = QQE2zlong[i-1] + 1 if stock.loc[i, "rsi_ma2"] >= 50 else 0
    #     QQE2zshort[i] = QQE2zshort[i-1] + 1 if stock.loc[i, "rsi_ma2"] < 50 else 0

    ####
    stock["Greenbar1"] = stock["rsi_ma2"]-50 > thres2
    stock["Greenbar2"] = stock["rsi_ma"]-50 > upper
    stock["Redbar1"] = stock["rsi_ma2"]-50 <0 - thres2
    stock["Redbar2"] = stock["rsi_ma"]-50 < lower

    for i in range(len(stock)):
        if stock["Greenbar1"][i] == 1 and stock["Greenbar2"][i] == 1:
            stock.loc[i, "QQE Dir"] = stock["rsi_ma2"][i]-50
        elif stock["Redbar1"][i] == 1 and stock["Redbar2"][i] == 1:
            stock.loc[i, "QQE Dir"] = stock["rsi_ma2"][i]-50
        else:
            stock.loc[i, "QQE Dir"] = "Nan"
    return stock

def pine_MACD(fast_length, slow_length, src, signal_smoothing, osc_ma, sig_ma, stock):
    if osc_ma =="EMA":
        ma_sor = pine_ema
    else:
        ma_sor = pine_sma
    fast_ma = ma_sor(stock[src], fast_length)
    slow_ma = ma_sor(stock[src], slow_length)
    macd = fast_ma - slow_ma
    if sig_ma == "EMA":
        ma_sig = pine_ema
    else:
        ma_sig = pine_sma
    signal = ma_sig(macd, signal_smoothing)
    hist = macd - signal
    stock["MACD"] = macd
    stock["MACD_Signal"] = signal
    stock["MACD_Hist"] = hist
    for i in range(1,len(stock)):
        if (stock.loc[i,"MACD_Hist"] >= 0) and (stock.loc[i-1,"MACD_Hist"] < stock.loc[i,"MACD_Hist"]):
            stock.loc[i,"MACD_Color"] = "Increasing Pos"
        elif (stock.loc[i,"MACD_Hist"] >= 0):
            stock.loc[i,"MACD_Color"] = "Decreaing Pos"
        elif (stock.loc[i,"MACD_Hist"] < 0) and (stock.loc[i-1,"MACD_Hist"] > stock.loc[i,"MACD_Hist"]):
            stock.loc[i,"MACD_Color"] = "Increasing Neg"
        elif (stock.loc[i,"MACD_Hist"] < 0):
            stock.loc[i,"MACD_Color"] = "Decreasing Neg"
    return stock

def pine_ADX_DI(stock, leng=14, th=20):
    for i in range(len(stock)):
        if i == 0:
            stock.loc[i,"tr"] = max(max(stock.loc[i, "high"] -stock.loc[i, "low"], abs(stock.loc[i, "high"]-0)), abs(stock.loc[i, "low"]-0))
            stock.loc[i,"DirectionalMovementPlus"] =  stock.loc[i, "high"]
            stock.loc[i,"DirectionalMovementMinus"] = 0
            stock.loc[i,"SmoothedTrueRange"] = stock.loc[i,"tr"]
            stock.loc[i,"SmoothedDirectionalMovementPlus"] = 0
            stock.loc[i,"SmoothedDirectionalMovementMinus"] = 0
        else:
            stock.loc[i,"tr"] = max(max(stock.loc[i, "high"] -stock.loc[i, "low"], abs(stock.loc[i, "high"]-stock.loc[i-1, "close"])), abs(stock.loc[i, "low"]-stock.loc[i-1, "close"]))
            if stock.loc[i, "high"] - stock.loc[i-1, "high"] > stock.loc[i-1, "low"] - stock.loc[i, "low"]:
                stock.loc[i,"DirectionalMovementPlus"] = max(stock.loc[i, "high"] - stock.loc[i-1, "high"], 0)
            else:
                stock.loc[i,"DirectionalMovementPlus"] = 0
            if stock.loc[i-1, "low"] - stock.loc[i, "low"] > stock.loc[i, "high"] - stock.loc[i-1, "high"]:
                stock.loc[i,"DirectionalMovementMinus"] = max(stock.loc[i-1, "low"] - stock.loc[i, "low"], 0)
            else:
                stock.loc[i,"DirectionalMovementMinus"] = 0

            stock.loc[i,"SmoothedTrueRange"] = stock.loc[i-1,"SmoothedTrueRange"] - stock.loc[i-1,"SmoothedTrueRange"]/leng + stock.loc[i,"tr"]
            stock.loc[i,"SmoothedDirectionalMovementPlus"] = stock.loc[i-1,"SmoothedDirectionalMovementPlus"] - stock.loc[i-1,"SmoothedDirectionalMovementPlus"]/leng + stock.loc[i,"DirectionalMovementPlus"]
            stock.loc[i,"SmoothedDirectionalMovementMinus"] = stock.loc[i-1,"SmoothedDirectionalMovementMinus"] - stock.loc[i-1,"SmoothedDirectionalMovementMinus"]/leng + stock.loc[i,"DirectionalMovementMinus"]
        stock.loc[i,"DIPlus"] = stock.loc[i,"SmoothedDirectionalMovementPlus"] / stock.loc[i,"SmoothedTrueRange"] * 100
        stock.loc[i,"DIMinus"] = stock.loc[i,"SmoothedDirectionalMovementMinus"] / stock.loc[i,"SmoothedTrueRange"] * 100
        stock.loc[i,"DX"] = abs(stock.loc[i,"DIPlus"]-stock.loc[i,"DIMinus"]) / (stock.loc[i,"DIPlus"]+stock.loc[i,"DIMinus"])*100
    stock["ADX"] = pine_sma(stock["DX"], leng)
    return stock

def pine_stoch_rsi(stock, smoothK=3, smoothD=3, lengthRSI=14, lengthStoch=14):
    rsi1 = pine_rsi(stock["close"], lengthRSI)
    for i in range(len(stock)):
        if i+1 < lengthStoch:
            continue
        stock.loc[i, "stoch"] = 100*(rsi1[i]-min(rsi1[i+1-lengthStoch:i+1]))/(max(rsi1[i+1-lengthStoch:i+1])-min(rsi1[i+1-lengthStoch:i+1]))
    stock["stoch_rsi_k"] = pine_sma(stock["stoch"], smoothK)
    stock["stoch_rsi_d"] = pine_sma(stock["stoch_rsi_k"], smoothD)
    return stock