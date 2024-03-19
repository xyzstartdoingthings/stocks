from concurrent.futures import ProcessPoolExecutor
from utils import *
from algo_1 import *
import pickle

# # coarse selecting
# data_path = Path(os.getcwd()).parent
# path = data_path / 'stock price data'
# ticker_all = pd.read_csv(path/"finer_data_complete_stock.csv")
# # change
# ticker_range = range(485, 677)
# a = int(len(ticker_range)/6)

#finer selecting
data_path = Path(os.getcwd())
with open('ticker_coarse','rb') as f:
     ticker_all = pickle.load(f)
ticker_range = range(0, 168)
a = int(len(ticker_range))
variables = {"atr_len": np.arange(10, 13, 1), "macd_fastLen": np.arange(10, 14, 1), "macd_slowLen": np.arange(30, 36, 2), "macd_signalSmooth": np.arange(
    6, 9, 1), "macd_peakLen": [3], "gain_ratio": np.arange(1, 2.5, 0.5), "loss_ratio": np.arange(1.5, 3, 0.5), "peak2_len": [20], "peak3_len": [40,50]}

def optimizer_parallel(algo, ticker, variables):
    result = optimizer(algo, ticker, variables, max_dd=0.15, wl_ratio=0.7)
    if result:
        return result
    else:
        return []


def main():
    # change cpu number
    with ProcessPoolExecutor(max_workers=24) as executor:
        #coarse
        # futures = [executor.submit(optimizer_parallel, algo2, ticker, variables)
        #            for ticker in ticker_all["Symbol"].unique()[ticker_range[0]:ticker_range[-1]]]
        #finer
        futures = [executor.submit(optimizer_parallel, algo1, ticker, variables)
                   for ticker in ticker_all[ticker_range[0]:ticker_range[-1]]]
        top_a_tickers = [future.result() for future in futures]

    # Sort and select the top 'a' results
    top_a_tickers = [ele for ele in top_a_tickers if ele != []]
    top_a_tickers.sort(key=lambda x: x[0][1], reverse=True)
    top_a_tickers = top_a_tickers[:a]
    with open("output finer "+str(ticker_range[0])+" to "+str(ticker_range[-1]), "wb") as fp:   #Pickling
        pickle.dump(top_a_tickers, fp)

    return top_a_tickers


if __name__ == '__main__':
    print(main())
