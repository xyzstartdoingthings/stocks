import yfinance as yf
import talib

# make sure to install yfinance and talib before running the code
# Python version conda 3.9.13
# conda install yfinance
# conda install TA-Lib


class createCSV:
    def __init__(self, start_date: str = None, end_date: str = None):
        # initialize the start and end dates for the time range
        self.start_date = start_date
        self.end_date = end_date

    def update_time_range(self, start_date: str, end_date: str):
        # update the start and end dates for the time range
        self.start_date = start_date
        self.end_date = end_date

    def process_stock(self, code: str):
        # download the historical stock data for the specified code and time range
        self.df = yf.download(code, start=self.start_date, end=self.end_date)
        # add additional technical indicators to the dataframe
        self.add_feature()
        self.add_target()
        self.df.to_csv(code+'.csv')

    def add_feature(self):
        # calculate the MACD technical indicator and add it as a new column to the dataframe
        macd, signal, hist = talib.MACD(
            self.df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        rsi = talib.RSI(self.df['Close'], timeperiod=14)
        k_line, d_line = talib.STOCH(
            self.df['High'], self.df['Low'], self.df['Close'], fastk_period=9, slowk_period=3, slowd_period=3)
        j_line = 3 * k_line - 2 * d_line
        upper, middle, lower = talib.BBANDS(self.df['Close'], timeperiod=20)
        # self.df['MACD'] = macd
        # self.df['signal'] = signal
        # self.df['hist'] = hist
        # self.df["k_line"] = k_line
        # self.df["d_line"] = d_line
        # self.df["j_line"] = j_line
        self.df["rsi"] = rsi
        # self.df["BBand_high"] = upper
        # self.df["BBand_low"] = lower
        # self.df["BBand_mid"] = middle
        # self.df["sma_5"] = talib.SMA(self.df['Close'], timeperiod=5)
        # self.df["sma_10"] = talib.SMA(self.df['Close'], timeperiod=10)
        # self.df["sma_30"] = talib.SMA(self.df['Close'], timeperiod=30)
        # self.df["sma_60"] = talib.SMA(self.df['Close'], timeperiod=60)
        self.df["ema_9"] = talib.EMA(self.df['Close'], timeperiod=5)
        self.df["ema_15"] = talib.EMA(self.df['Close'], timeperiod=10)
        self.df["ema_120"] = talib.EMA(self.df['Close'], timeperiod=30)
        # self.df["ema_60"] = talib.EMA(self.df['Close'], timeperiod=60)
        self.df = self.df.reset_index().reset_index().rename(columns={"index": "Bar Time"}).set_index(
            "Bar Time")

    def add_target(self):
        for i in self.df.index:
            next_10 = i + 5
            days = list(range(i+1, next_10+1))
            data_10days = self.df[self.df.index.isin(days)]
            if data_10days.Low.min() <= self.df.loc[i, "Close"]*0.97:
                self.df.loc[i, "Target"] = 2
            elif data_10days.High.max() >= self.df.loc[i, "Close"]*1.03:
                self.df.loc[i, "Target"] = 1
            else:
                self.df.loc[i, "Target"] = 0


if __name__ == '__main__':
    # define the stocks to download
    stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOGL']

    # define the time range for the historical data
    start_date = '2015-01-01'
    end_date = '2021-12-31'

    myF = createCSV()
    myF.update_time_range(start_date, end_date)
    for stock in stocks:
        myF.process_stock(stock)
