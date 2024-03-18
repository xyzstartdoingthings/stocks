
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from collections import deque
import itertools
import pickle


def optimizer(algo, ticker, variables, n=3, min_ROI = 1.8, max_dd=0.18, wl_ratio=0.6):
    variables["ticker"] = [ticker]
    keys, values = zip(*variables.items())
    combinations = itertools.product(*values)
    top_n_combinations = []
    count = 1
    for combination in combinations:
        params = dict(zip(keys, combination))
        stock = algo(**params)
        maximum_drawdown, ROI, win_loss_ratio = eval(stock, opt=True, ticker=ticker, variables=params)
        metric = 0.5*ROI-0.25*maximum_drawdown+0.25*win_loss_ratio
        if maximum_drawdown <= max_dd and win_loss_ratio >= wl_ratio and min_ROI <= ROI:
            if len(top_n_combinations) < n:
                top_n_combinations.append((params, metric, (ROI, maximum_drawdown, win_loss_ratio)))
            else:
                # Find the combination with the lowest output to potentially replace
                min_metric = min(top_n_combinations, key=lambda x: x[1])[1]
                if metric > min_metric:
                    # Replace the combination with the lowest output
                    top_n_combinations.remove(min(top_n_combinations, key=lambda x: x[1]))
                    top_n_combinations.append((params, metric, (ROI, maximum_drawdown, win_loss_ratio)))
        top_n_combinations.sort(key=lambda x: x[1], reverse=True)
        if count%200 == 0:
            print(count, " iterations done, current top 3 results are ", top_n_combinations)
        count+=1
    return top_n_combinations


class FixedSizeFIFO:
    def __init__(self, size=3):
        self.size = size
        self.queue = deque(maxlen=size)

    def add(self, item):
        """Add an item to the queue. If the queue is full, the oldest item is removed."""
        self.queue.append(item)

    def length(self):
        """Return the current number of items in the queue."""
        return len(self.queue)

    def get_all(self):
        """Return a list of all items in the queue."""
        return list(self.queue)

    def get(self, i):
        return self.queue[i]

    def clear(self):
        """Clear all items from the queue."""
        self.queue.clear()

    def __repr__(self):
        """String representation of the queue's current state."""
        return f"FixedSizeFIFO({list(self.queue)})"


def peak_calc(stock, col, length, mirror):
    new_col = col+"_is_peak"
    for i in range(length//2, len(stock)-length//2):
        if stock.loc[i, col] == max(stock.loc[i-length//2:i+length//2, col]):
            if not mirror:
                stock.loc[i, new_col] = 1
            else:
                if stock.loc[i, col] >= 0:
                    stock.loc[i, new_col] = 1
                else:
                    stock.loc[i, new_col] = 0
        elif stock.loc[i, col] == min(stock.loc[i-length//2:i+length//2, col]):
            if not mirror:
                stock.loc[i, new_col] = -1
            else:
                if stock.loc[i, col] < 0:
                    stock.loc[i, new_col] = -1
                else:
                    stock.loc[i, new_col] = 0
        else:
            stock.loc[i, new_col] = 0
    return stock


def eval(stock, ticker, variables, opt=False):
    try:
        # perhaps set to external harddrive to accomodate large amount of data
        data_path = Path(os.getcwd())
        buy_orders = []
        sell_orders = []
        current_order = None
        money = 100000
        short = None
        long = None

        for index, row in stock.iterrows():
            if row['order'] > 0:
                if current_order is None and short is None:
                    current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': stock.loc[index -
                                                                                                            1, 'close'], "Shares Purchased": money/stock.loc[index - 1, 'close'], "long/short": "long"}
                    long = True
                elif current_order is not None and short is not None:
                    current_order['Sell Date'] = row['date']
                    current_order['Sell Price'] = row['close']
                    current_order["Price Change"] = current_order["Sell Price"] - \
                        current_order["Buy Price"]
                    current_order["Profit"] = current_order["Price Change"] * \
                        current_order["Shares Purchased"] * -1
                    current_order["Money After Order"] = current_order["Shares Purchased"] * \
                        current_order['Buy Price'] + current_order["Profit"]
                    money = current_order["Money After Order"]
                    sell_orders.append(current_order)
                    short = None
                    current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': row[
                        'close'], "Shares Purchased": money/row['close'], "long/short": "long"}
                    long = True
                else:
                    continue
            elif row['order'] < 0:
                if current_order is None and long is None:
                    current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': stock.loc[index -
                                                                                                            1, 'close'], "Shares Purchased": money/stock.loc[index - 1, 'close'], "long/short": "short"}
                    short = True
                elif current_order is not None and long is not None:
                    current_order['Sell Date'] = row['date']
                    current_order['Sell Price'] = row['close']
                    current_order["Price Change"] = current_order["Sell Price"] - \
                        current_order["Buy Price"]
                    current_order["Profit"] = current_order["Price Change"] * \
                        current_order["Shares Purchased"]
                    current_order["Money After Order"] = current_order["Shares Purchased"] * \
                        current_order['Buy Price'] + current_order["Profit"]
                    money = current_order["Money After Order"]
                    sell_orders.append(current_order)
                    long = None
                    current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': row[
                        'close'], "Shares Purchased": money/row['close'], "long/short": "short"}
                    short = True
                else:
                    continue
            elif row['order'] == 0:
                if current_order is not None:
                    current_order['Sell Date'] = row['date']
                    current_order['Sell Price'] = row['close']
                    current_order["Price Change"] = current_order["Sell Price"] - \
                        current_order["Buy Price"]
                    if current_order['long/short'] == "short":
                        current_order["Profit"] = current_order["Price Change"] * \
                            current_order["Shares Purchased"] * -1
                    elif current_order['long/short'] == "long":
                        current_order["Profit"] = current_order["Price Change"] * \
                            current_order["Shares Purchased"]
                    current_order["Money After Order"] = current_order["Shares Purchased"] * \
                        current_order['Buy Price'] + current_order["Profit"]
                    money = current_order["Money After Order"]
                    sell_orders.append(current_order)
                    current_order = None
                    long = None
                    short = None

        # Create a new DataFrame for buy and sell orders
        orders_df = pd.DataFrame(buy_orders + sell_orders)

        # maximum drawdown
        peak_value = None
        maximum_drawdown = 0.0

        for index, row in stock.iterrows():
            if row['order'] == 1:
                if peak_value is None:
                    peak_value = row['close']
                elif row['close'] > peak_value:
                    peak_value = row['close']
                else:
                    drawdown = (peak_value - row['close']) / peak_value
                    if drawdown > maximum_drawdown:
                        maximum_drawdown = drawdown
            if row['order'] == -1:
                if peak_value is None:
                    peak_value = row['close']
                elif row['close'] < peak_value:
                    peak_value = row['close']
                else:
                    drawdown = (row['close'] - peak_value) / peak_value
                    if drawdown > maximum_drawdown:
                        maximum_drawdown = drawdown
            elif row['order'] == 0:
                # If 'order_column' is 0, reset peak and trough values
                peak_value = None

        # ROI
        ROI = (orders_df.loc[len(orders_df)-1, "Money After Order"] -
            orders_df.loc[0, "Initial Money"])/orders_df.loc[0, "Initial Money"]
        # print(f"ROI: {ROI * 100:.2f}%")
        ROI_noStrategy = (stock.loc[len(stock)-1, "close"] -
                        stock.loc[0, "close"]) / stock.loc[0, "close"]
        # print(f"ROI with no strategy: {ROI_noStrategy * 100:.2f}%")

        # Win-Loss Ratio
        win_loss_ratio = (orders_df['Profit'] > 0).sum()/len(orders_df) * 100
        # print(f"Win-Loss Ratio: {win_loss_ratio:.2f}%")

        if opt:
            return maximum_drawdown, ROI, win_loss_ratio/100
        else:
            # Reset the index of the new DataFrame
            orders_df.reset_index(drop=True, inplace=True)
            # Total Trades
            print("Total Trades: {}".format(len(orders_df)))

            # Average Win
            winning = orders_df[orders_df["Profit"] > 0]
            print(
                f"Average Win: {abs(winning['Price Change']/winning['Buy Price']).mean() * 100:.2f}%")

            # Average Lose
            losing = orders_df[orders_df["Profit"] <= 0]
            print(
                f"Average Lose: {abs(losing['Price Change']/losing['Buy Price']).mean() * 100:.2f}%")

            # Maximum Drawdown is now stored in 'maximum_drawdown'
            print(f"Maximum Drawdown: {maximum_drawdown * 100:.2f}%")

            # ROI
            print(f"ROI: {ROI * 100:.2f}%")
            print(f"ROI with no strategy: {ROI_noStrategy * 100:.2f}%")

            # Compounding Annual Return
            years = (stock["date"].max()-stock["date"].min()).days/365
            print(
                f"Compounding Annual Return: {((orders_df.loc[len(orders_df)-1, 'Money After Order']/orders_df.loc[0, 'Initial Money']) ** (1/years) - 1) * 100:.2f}%")

            # Win-Loss Ratio
            print(f"Win-Loss Ratio: {win_loss_ratio:.2f}%")
            # Profit-Loss Ratio
            print(
                f"Profit-Loss Ratio: {winning['Profit'].sum()/-losing['Profit'].sum()}")

            # Annual Variance
            stock['daily_returns'] = stock['order'] * \
                (stock['close'] / stock['close'].shift(1) - 1)
            variance_daily = np.var(stock['daily_returns'].dropna())
            # Specify the number of trading days in a year (e.g., 252 for U.S. markets)
            trading_days_per_year = 252
            # Annualize the variance by multiplying by the number of trading days in a year
            variance_annualized = variance_daily * trading_days_per_year
            print("Annual Variance: {}".format(variance_annualized))

            # Annual Standard Deviation
            print("Annual Standard Deviation: {}".format(
                np.sqrt(variance_annualized)))

            # Sharoe Ratio
            # Calculate the average daily return
            average_daily_return = stock['daily_returns'].mean()
            # Calculate the daily risk-free rate
            annual_rate = 0.04
            daily_risk_free_rate = (
                1 + annual_rate) ** (1/trading_days_per_year) - 1
            # Calculate the daily excess return
            stock['daily_excess_return'] = stock['daily_returns'] - \
                daily_risk_free_rate
            # Calculate the standard deviation of daily excess returns as the measure of risk
            std_dev_daily_excess_returns = stock['daily_excess_return'].std()
            # Calculate the annualized Sharpe Ratio
            sharpe_ratio = (average_daily_return /
                            std_dev_daily_excess_returns) * np.sqrt(trading_days_per_year)
            print(f"Sharpe Ratio: {sharpe_ratio:.4f}")

            # Beta
            bench_path = data_path / 'stock price data'/"benchmark price daily"
            dates = set(stock['date'])
            number = 0
            fig, axes = plt.subplots(4, 1, figsize=(18, 18), sharex=True)
            fig1, axes1 = plt.subplots(4, 1, figsize=(18, 18), sharex=True)
            for benchmark in [name for name in os.listdir(bench_path) if name not in ["CLUSD.csv", "BTCUSD.csv"]]:
                benchmark_file = pd.read_csv(bench_path/benchmark)
                benchmark_file['date'] = pd.to_datetime(benchmark_file['date'])
                benchmark_file = benchmark_file.sort_values(
                    by='date').reset_index(drop=True)
                benchmark_file = benchmark_file[["date", "open", "high", "low", "close", "adjClose", "Symbol"]].merge(
                    stock[["date", "order"]], on="date", how="inner")
                benchmark_file['daily_returns'] = benchmark_file['order'] * \
                    (benchmark_file['close'] /
                    benchmark_file['close'].shift(1) - 1)
                covariance = np.cov(stock['daily_returns'].dropna(
                ), benchmark_file['daily_returns'].dropna())[0][1]
                variance_market = np.var(benchmark_file['daily_returns'].dropna())
                strategy_beta = covariance / variance_market
                if benchmark == "^DJI.csv":
                    name = "DOW JONES"
                elif benchmark == "^GSPC.csv":
                    name = "S&P 500"
                elif benchmark == "^IXIC.csv":
                    name = "NASDAQ"
                elif benchmark == "^RUT.csv":
                    name = "Russell 2000"
                print(f"Strategy Beta with Benchmark {name}: {strategy_beta:.4f}")

                # benchmark ROI
                benchmark_ROI = (benchmark_file['close'].iloc[-1] -
                                benchmark_file['close'].iloc[0])/benchmark_file['close'].iloc[0]
                print(f"Benchmark {name} ROI: {benchmark_ROI * 100:.2f}%")

                ax = axes1[number]
                ax.plot(benchmark_file['date'], benchmark_file['close'])
                ax.set_title(
                    f"Benchmark {name} With ROI {benchmark_ROI * 100:.2f}%")
                ax.set_xlabel(name)
                ax.set_ylabel('Index')
                ax.grid(True)

                buy_orders = []
                sell_orders = []
                current_order = None
                money = 100000
                long = None
                short = None

                for index, row in benchmark_file.iterrows():
                    if row['order'] > 0:
                        if current_order is None and short is None:
                            current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': benchmark_file.loc[
                                index - 1, 'close'], "Shares Purchased": money/benchmark_file.loc[index - 1, 'close'], "long/short": "long"}
                            long = True
                        elif current_order is not None and short is not None:
                            current_order['Sell Date'] = row['date']
                            current_order['Sell Price'] = row['close']
                            current_order["Price Change"] = current_order["Sell Price"] - \
                                current_order["Buy Price"]
                            current_order["Profit"] = current_order["Price Change"] * \
                                current_order["Shares Purchased"] * -1
                            current_order["Money After Order"] = current_order["Shares Purchased"] * \
                                current_order['Buy Price'] + \
                                current_order["Profit"]
                            money = current_order["Money After Order"]
                            sell_orders.append(current_order)
                            short = None
                            current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': row[
                                'close'], "Shares Purchased": money/row['close'], "long/short": "long"}
                            long = True
                        else:
                            continue
                    elif row['order'] < 0:
                        if current_order is None and long is None:
                            current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': benchmark_file.loc[
                                index - 1, 'close'], "Shares Purchased": money/benchmark_file.loc[index - 1, 'close'], "long/short": "short"}
                            short = True
                        elif current_order is not None and long is not None:
                            current_order['Sell Date'] = row['date']
                            current_order['Sell Price'] = row['close']
                            current_order["Price Change"] = current_order["Sell Price"] - \
                                current_order["Buy Price"]
                            current_order["Profit"] = current_order["Price Change"] * \
                                current_order["Shares Purchased"]
                            current_order["Money After Order"] = current_order["Shares Purchased"] * \
                                current_order['Buy Price'] + \
                                current_order["Profit"]
                            money = current_order["Money After Order"]
                            sell_orders.append(current_order)
                            long = None
                            current_order = {"Initial Money": money, 'Buy Date': row['date'], 'Buy Price': row[
                                'close'], "Shares Purchased": money/row['close'], "long/short": "short"}
                            short = True
                        else:
                            continue
                    elif row['order'] == 0:
                        if current_order is not None:
                            current_order['Sell Date'] = row['date']
                            current_order['Sell Price'] = row['close']
                            current_order["Price Change"] = current_order["Sell Price"] - \
                                current_order["Buy Price"]
                            if current_order['long/short'] == "short":
                                current_order["Profit"] = current_order["Price Change"] * \
                                    current_order["Shares Purchased"] * -1
                            elif current_order['long/short'] == "long":
                                current_order["Profit"] = current_order["Price Change"] * \
                                    current_order["Shares Purchased"]
                            current_order["Money After Order"] = current_order["Shares Purchased"] * \
                                current_order['Buy Price'] + \
                                current_order["Profit"]
                            money = current_order["Money After Order"]
                            sell_orders.append(current_order)
                            current_order = None
                            long = None
                            short = None

                # Create a new DataFrame for buy and sell orders
                orders_benchmark = pd.DataFrame(buy_orders + sell_orders)

                # Reset the index of the new DataFrame
                orders_benchmark.reset_index(drop=True, inplace=True)
                benchmark_ROI = (orders_benchmark.loc[len(orders_benchmark)-1, "Money After Order"] -
                                orders_benchmark.loc[0, "Initial Money"])/orders_benchmark.loc[0, "Initial Money"]
                print(
                    f"Benchmark {name} ROI Following Strategy: {benchmark_ROI * 100:.2f}%")

                for i in range(len(benchmark_file)):
                    if i == 0:
                        benchmark_file.loc[i, "Previous Money"] = 100000
                        if benchmark_file.loc[i, "order"] == 1:
                            benchmark_file.loc[i, "Shares Onhand"] = benchmark_file.loc[i, "order"] * \
                                benchmark_file.loc[i, "Previous Money"] / \
                                benchmark_file.loc[i, "open"]
                            benchmark_file.loc[i, "Stock Value"] = benchmark_file.loc[i,
                                                                                    "Shares Onhand"] * benchmark_file.loc[i, "close"]
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i,
                                                                                    "Previous Money"] * (1 - benchmark_file.loc[i, "order"])
                        elif benchmark_file.loc[i, "order"] == -1:
                            benchmark_file.loc[i, "Shares Onhand"] = -benchmark_file.loc[i, "order"] * \
                                benchmark_file.loc[i, "Previous Money"] / \
                                benchmark_file.loc[i, "open"]
                            benchmark_file.loc[i, "Stock Value"] = 2*benchmark_file.loc[i, "Shares Onhand"] * \
                                benchmark_file.loc[i, "open"] - benchmark_file.loc[i,
                                                                                "Shares Onhand"] * benchmark_file.loc[i, "close"]
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i,
                                                                                    "Previous Money"] * (1 + benchmark_file.loc[i, "order"])
                        else:
                            benchmark_file.loc[i, "Shares Onhand"] = 0
                            benchmark_file.loc[i, "Stock Value"] = 0
                            benchmark_file.loc[i,
                                            "After Money"] = benchmark_file.loc[i, "Previous Money"]
                    else:
                        benchmark_file.loc[i,
                                        "Previous Money"] = benchmark_file.loc[i-1, "After Money"]
                        if benchmark_file.loc[i, "order"] == 1 and benchmark_file.loc[i-1, "order"] == 0:
                            benchmark_file.loc[i, "Shares Onhand"] = benchmark_file.loc[i,
                                                                                        "Previous Money"]/benchmark_file.loc[i-1, "close"]
                            benchmark_file.loc[i, "Stock Value"] = benchmark_file.loc[i,
                                                                                    "Shares Onhand"] * benchmark_file.loc[i, "close"]
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i,
                                                                                    "Previous Money"] * (1 - benchmark_file.loc[i, "order"])
                        elif benchmark_file.loc[i, "order"] == 1 and benchmark_file.loc[i-1, "order"] == 1:
                            benchmark_file.loc[i,
                                            "Shares Onhand"] = benchmark_file.loc[i-1, "Shares Onhand"]
                            benchmark_file.loc[i, "Stock Value"] = benchmark_file.loc[i,
                                                                                    "Shares Onhand"] * benchmark_file.loc[i, "close"]
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i,
                                                                                    "Previous Money"] * (1 - benchmark_file.loc[i, "order"])
                        elif benchmark_file.loc[i, "order"] == 0 and benchmark_file.loc[i-1, "order"] == 1:
                            benchmark_file.loc[i, "Shares Onhand"] = 0
                            benchmark_file.loc[i, "Stock Value"] = 0
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i -
                                                                                    1, "Shares Onhand"] * benchmark_file.loc[i, "close"]
                        elif benchmark_file.loc[i, "order"] == -1 and benchmark_file.loc[i-1, "order"] == 0:
                            benchmark_file.loc[i, "Shares Onhand"] = benchmark_file.loc[i,
                                                                                        "Previous Money"]/benchmark_file.loc[i-1, "close"]
                            benchmark_file.loc[i, "Stock Value"] = benchmark_file.loc[i, "Shares Onhand"] * (
                                2*benchmark_file.loc[i-1, "close"] - benchmark_file.loc[i, "close"])
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i,
                                                                                    "Previous Money"] * (1 + benchmark_file.loc[i, "order"])
                        elif benchmark_file.loc[i, "order"] == -1 and benchmark_file.loc[i-1, "order"] == -1:
                            benchmark_file.loc[i,
                                            "Shares Onhand"] = benchmark_file.loc[i-1, "Shares Onhand"]
                            benchmark_file.loc[i, "Stock Value"] = benchmark_file.loc[i-1, "Stock Value"] + benchmark_file.loc[i,
                                                                                                                            "Shares Onhand"] * (benchmark_file.loc[i-1, "close"] - benchmark_file.loc[i, "close"])
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i,
                                                                                    "Previous Money"] * (1 + benchmark_file.loc[i, "order"])
                        elif benchmark_file.loc[i, "order"] == 0 and benchmark_file.loc[i-1, "order"] == -1:
                            benchmark_file.loc[i, "Shares Onhand"] = 0
                            benchmark_file.loc[i, "Stock Value"] = 0
                            benchmark_file.loc[i, "After Money"] = benchmark_file.loc[i-1, "Stock Value"] + benchmark_file.loc[i -
                                                                                                                            1, "Shares Onhand"] * (benchmark_file.loc[i-1, "close"] - benchmark_file.loc[i, "close"])
                        elif benchmark_file.loc[i, "order"] == 1 and benchmark_file.loc[i-1, "order"] == -1:
                            benchmark_file.loc[i, "Shares Onhand"] = (benchmark_file.loc[i-1, "Stock Value"] + benchmark_file.loc[i-1, "Shares Onhand"] * (
                                benchmark_file.loc[i-1, "close"] - benchmark_file.loc[i, "close"]))/benchmark_file.loc[i, "close"]
                            benchmark_file.loc[i, "Stock Value"] = benchmark_file.loc[i-1, "Stock Value"] + benchmark_file.loc[i -
                                                                                                                            1, "Shares Onhand"] * (benchmark_file.loc[i-1, "close"] - benchmark_file.loc[i, "close"])
                            benchmark_file.loc[i, "After Money"] = 0
                        elif benchmark_file.loc[i, "order"] == -1 and benchmark_file.loc[i-1, "order"] == 1:
                            benchmark_file.loc[i,
                                            "Shares Onhand"] = benchmark_file.loc[i-1, "Shares Onhand"]
                            benchmark_file.loc[i,
                                            "Stock Value"] = benchmark_file.loc[i-1, "Stock Value"]
                            benchmark_file.loc[i, "After Money"] = 0
                        else:
                            benchmark_file.loc[i, "Shares Onhand"] = 0
                            benchmark_file.loc[i, "Stock Value"] = 0
                            benchmark_file.loc[i,
                                            "After Money"] = benchmark_file.loc[i, "Previous Money"]
                    benchmark_file.loc[i, "Total Assets"] = benchmark_file.loc[i,
                                                                            "After Money"] + benchmark_file.loc[i, "Stock Value"]
                axes[number].plot(benchmark_file['date'],
                                benchmark_file['Total Assets'])
                axes[number].set_title(
                    f"Total Assets Change Following Strategy for {name} With ROI {benchmark_ROI * 100:.2f}%")
                axes[number].set_ylabel('Total Assets')
                axes[number].grid(True)

                number += 1

            for i in range(len(stock)):
                if i == 0:
                    stock.loc[i, "Previous Money"] = 100000
                    if stock.loc[i, "order"] == 1:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i,
                                                                "Previous Money"]/stock["open"]
                        stock.loc[i, "Stock Value"] = stock.loc[i,
                                                                "Shares Onhand"] * stock.loc[i, "close"]
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"] * (1 - stock.loc[i, "order"])
                    elif stock.loc[i, "order"] == -1:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i,
                                                                "Previous Money"]/stock["open"]
                        stock.loc[i, "Stock Value"] = stock.loc[i, "Previous Money"] - \
                            stock.loc[i, "Shares Onhand"] * \
                            (stock.loc[i, "close"]-stock.loc[i, "open"])
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"] * (1 + stock.loc[i, "order"])
                    else:
                        stock.loc[i, "Shares Onhand"] = 0
                        stock.loc[i, "Stock Value"] = 0
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"]
                else:
                    stock.loc[i, "Previous Money"] = stock.loc[i-1, "After Money"]
                    if stock.loc[i, "order"] == 1 and stock.loc[i-1, "order"] == 0:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i,
                                                                "Previous Money"]/stock.loc[i-1, "close"]
                        stock.loc[i, "Stock Value"] = stock.loc[i,
                                                                "Shares Onhand"] * stock.loc[i, "close"]
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"] * (1 - stock.loc[i, "order"])
                    elif stock.loc[i, "order"] == 1 and stock.loc[i-1, "order"] == 1:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i -
                                                                1, "Shares Onhand"]
                        stock.loc[i, "Stock Value"] = stock.loc[i,
                                                                "Shares Onhand"] * stock.loc[i, "close"]
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"] * (1 - stock.loc[i, "order"])
                    elif stock.loc[i, "order"] == 0 and stock.loc[i-1, "order"] == 1:
                        stock.loc[i, "Shares Onhand"] = 0
                        stock.loc[i, "Stock Value"] = 0
                        stock.loc[i, "After Money"] = stock.loc[i-1,
                                                                "Shares Onhand"] * stock.loc[i, "close"]
                    elif stock.loc[i, "order"] == -1 and stock.loc[i-1, "order"] == 0:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i,
                                                                "Previous Money"]/stock.loc[i-1, "close"]
                        stock.loc[i, "Stock Value"] = stock.loc[i, "Shares Onhand"] * \
                            (2*stock.loc[i-1, "close"] - stock.loc[i, "close"])
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"] * (1 + stock.loc[i, "order"])
                    elif stock.loc[i, "order"] == -1 and stock.loc[i-1, "order"] == -1:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i -
                                                                1, "Shares Onhand"]
                        stock.loc[i, "Stock Value"] = stock.loc[i-1, "Stock Value"] + stock.loc[i,
                                                                                                "Shares Onhand"] * (stock.loc[i-1, "close"] - stock.loc[i, "close"])
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"] * (1 + stock.loc[i, "order"])
                    elif stock.loc[i, "order"] == 0 and stock.loc[i-1, "order"] == -1:
                        stock.loc[i, "Shares Onhand"] = 0
                        stock.loc[i, "Stock Value"] = 0
                        stock.loc[i, "After Money"] = stock.loc[i-1, "Stock Value"] + stock.loc[i -
                                                                                                1, "Shares Onhand"] * (stock.loc[i-1, "close"] - stock.loc[i, "close"])
                    elif stock.loc[i, "order"] == 1 and stock.loc[i-1, "order"] == -1:
                        stock.loc[i, "Shares Onhand"] = (stock.loc[i-1, "Stock Value"] + stock.loc[i-1, "Shares Onhand"] * (
                            stock.loc[i-1, "close"] - stock.loc[i, "close"]))/stock.loc[i, "close"]
                        stock.loc[i, "Stock Value"] = stock.loc[i-1, "Stock Value"] + stock.loc[i -
                                                                                                1, "Shares Onhand"] * (stock.loc[i-1, "close"] - stock.loc[i, "close"])
                        stock.loc[i, "After Money"] = 0
                    elif stock.loc[i, "order"] == -1 and stock.loc[i-1, "order"] == 1:
                        stock.loc[i, "Shares Onhand"] = stock.loc[i -
                                                                1, "Shares Onhand"]
                        stock.loc[i, "Stock Value"] = stock.loc[i-1, "Stock Value"]
                        stock.loc[i, "After Money"] = 0
                    else:
                        stock.loc[i, "Shares Onhand"] = 0
                        stock.loc[i, "Stock Value"] = 0
                        stock.loc[i, "After Money"] = stock.loc[i,
                                                                "Previous Money"]
                    # else:
                    #     stock.loc[i, "Shares Onhand"] = 0
                    #     stock.loc[i, "Stock Value"] = 0
                    #     stock.loc[i, "After Money"] = stock.loc[i, "Previous Money"]
                stock.loc[i, "Total Assets"] = stock.loc[i,
                                                        "After Money"] + stock.loc[i, "Stock Value"]

            import cufflinks as cf
            fig1, ax1 = plt.subplots(figsize=(18, 9))  # Adjust the size as needed
            ax1.plot(stock['date'], stock['Total Assets'],
                    drawstyle='steps-post')  # step line plot
            ax1.set_title("Total Assets Change")
            ax1.set_ylabel('Total Assets')
            ax1.grid(True)
            plt.show()  # Display the first plot

            # Create the second plot
            fig2, ax2 = plt.subplots(figsize=(18, 9))  # Adjust the size as needed
            ax2.plot(stock['date'], stock['order'],
                    drawstyle='steps-post')  # step line plot
            ax2.set_title("Order Detail")
            ax2.set_xlabel("Date")
            ax2.set_ylabel('Order')
            ax2.grid(True)
            plt.show()  # Display the second plot

            cf.set_config_file(offline=True)
            stock.set_index("date").loc[:, ["Total Assets", "order"]].iplot(
                secondary_y="order")
    except:
        # Check if the error file exists
        new_error = {ticker: variables}
        if os.path.exists("error_file"):
            # Read the existing error list
            with open("error_file", 'rb') as file:
                error_list = pickle.load(file)
        else:
            error_list = []

        # Append the new error to the list
        error_list.append(new_error)

        # Store the updated error list in the file
        with open("error_file", 'wb') as file:
            pickle.dump(error_list, file)
        return 0,0,0
