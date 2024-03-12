from concurrent.futures import ProcessPoolExecutor
from utils import *
from algo_2 import *

# perhaps set to external harddrive to accomodate large amount of data
data_path = Path(os.getcwd())
path = data_path / 'stock price data'
ticker_all = pd.read_csv(path/"finer_data_complete_stock.csv")
# change
a = 24
variables = {"atr_len": np.arange(11, 14, 1), "macd_fastLen": np.arange(11, 14, 1), "macd_slowLen": np.arange(32, 36, 2), "macd_signalSmooth": np.arange(
    7, 10, 1), "macd_peakLen": [3, 5], "gain_ratio": np.arange(1, 3, 1), "loss_ratio": np.arange(1, 3, 1), "peak2_len": [20, 30], "peak3_len": [40, 50]}


def optimizer_parallel(algo, ticker, variables):
    result = optimizer(algo, ticker, variables, max_dd=0.15, wl_ratio=0.7)
    if result:
        return optimizer(algo, ticker, variables, max_dd=0.15, wl_ratio=0.7)[0]
    else:
        return []


def main():
    # change cpu number
    with ProcessPoolExecutor() as executor:

        # change ticker range
        futures = [executor.submit(optimizer_parallel, algo2, ticker, variables)
                   for ticker in ticker_all["Symbol"].unique()[0:96]]
        top_a_tickers = [future.result() for future in futures]

    # Sort and select the top 'a' results
    top_a_tickers.sort(key=lambda x: x[1], reverse=True)
    top_a_tickers = top_a_tickers[:a]
    return top_a_tickers


if __name__ == '__main__':
    print(main())
