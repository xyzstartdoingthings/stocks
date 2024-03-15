import argparse
from concurrent.futures import ProcessPoolExecutor
from utils import *
from algo_2 import *
import pickle

# perhaps set to external harddrive to accomodate large amount of data
data_path = Path(os.getcwd())
path = data_path / 'stock price data'
ticker_all = pd.read_csv(path/"finer_data_complete_stock.csv")

variables = {"atr_len": np.arange(11, 14, 1), "macd_fastLen": np.arange(11, 14, 1), "macd_slowLen": np.arange(32, 36, 2), "macd_signalSmooth": np.arange(
    7, 10, 1), "macd_peakLen": [3, 5], "gain_ratio": np.arange(1, 3, 1), "loss_ratio": np.arange(1, 3, 1), "peak2_len": [20, 30], "peak3_len": [40, 50]}

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--idx", type=int, default=144)
    parser.add_argument("--batch_size", type=int, default=96)
    return parser.parse_args()

def optimizer_parallel(algo, ticker, variables):
    result = optimizer(algo, ticker, variables, max_dd=0.15, wl_ratio=0.7)
    if result:
        return result
    else:
        return []


def main():
    args = parse_args()
    # change
    ticker_range = range(args.idx, args.idx + args.batch_size)
    a = len(ticker_range) // 6 if len(ticker_range) >= 6 else len(ticker_range)
    # change cpu number
    with ProcessPoolExecutor(max_workers=16) as executor:
        # change ticker range
        futures = [executor.submit(optimizer_parallel, algo2, ticker, variables)
                   for ticker in ticker_all["Symbol"].unique()[ticker_range[0]:ticker_range[-1]]]
        top_a_tickers = [future.result() for future in futures]

    # Sort and select the top 'a' results
    top_a_tickers = [ele for ele in top_a_tickers if ele != []]
    top_a_tickers.sort(key=lambda x: x[0][1], reverse=True)
    top_a_tickers = top_a_tickers[:a]
    with open("output"+str(ticker_range[0])+"_to_"+str(ticker_range[-1]), "wb") as fp:   #Pickling
        pickle.dump(top_a_tickers, fp)

    return top_a_tickers


if __name__ == '__main__':
    print(main())
