import yfinance as yf
import talib

# make sure to install yfinance and talib before running the code
# Python version conda 3.9.13
# conda install yfinance
# conda install TA-Lib

class createCSV:
    def __init__(self, start_date:str = None, end_date:str = None):
        # initialize the start and end dates for the time range
        self.start_date = start_date
        self.end_date = end_date
        
    def update_time_range(self, start_date:str, end_date:str):
        # update the start and end dates for the time range
        self.start_date = start_date
        self.end_date = end_date
        
    def process_stock(self, code:str):
        # download the historical stock data for the specified code and time range
        self.df = yf.download(code, start=self.start_date, end=self.end_date)
        # add additional technical indicators to the dataframe
        self.add_info()
        self.df.to_csv(code+'.csv')

    def add_info(self):
        # calculate the MACD technical indicator and add it as a new column to the dataframe
        macd, signal, hist = talib.MACD(self.df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        self.df['MACD'] = macd
        self.df['signal'] = signal
        self.df['hist'] = hist

if __name__ == '__main__':
    # define the stocks to download
    stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOGL']

    # define the time range for the historical data
    start_date = '2015-01-01'
    end_date = '2021-12-31'

    myF = createCSV()
    myF.update_time_range(start_date,end_date)
    for stock in stocks:
        myF.process_stock(stock)