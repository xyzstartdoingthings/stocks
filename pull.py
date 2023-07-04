import requests
import argparse
import os
import random
import json
import pprint
from collections import defaultdict
import pandas as pd

import yaml

# set up headers, once in lifetime
headers = {
	"X-RapidAPI-Key": "551595c10emsh9ab76ccfb317820p1fa121jsnc738c9455698",
	"X-RapidAPI-Host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
}

# set up query string, only modify symbol in main function
querystring = {"symbol":"AMRN","region":"US","lang":"en-US", "range":"1d", "straddle":"true"}


def parse_args():
    parser = argparse.ArgumentParser(description="Pull data from yahoo finance")
    parser.add_argument(
      '--config', 
      type=str,
      default='config/basic.yaml', 
      help='configuration file'
    )
    parser.add_argument(
      '-s', "--section", 
      type=str,
      default='stock', 
      help="which section we pull data from (market)", 
      choices=['stock', 'market', 'news', 'screener', 'conversation', 'calendar']
    )
    args = parser.parse_args()
    return args

class subset_pipe:
  def __init__(self, keys_txt = None):
    # a list storing name of files containing subset keys, e.g. stock-v2-get-summary-keys.txt
    self.action_to_keys_file_name = []
    if keys_txt:
       self.action_to_keys_file_name.append(keys_txt)
  
  def append_file(self, keys_txt:str):
     self.action_to_keys_file_name.append(keys_txt)

  def read_txt_into_list(self, file_path:str):
    # e.g. file_path = "stock-v2-get-summary-keys.txt"
    # output: a list separate with comma: 
    '''
    [ 'defaultKeyStatistics: beta (5Y Monthly), bookValue (book value per share), earningsQuarterlyGrowth (Quarterly earnings growth year-over-year), enterpriseToEbitda, enterpriseToRevenue, enterpriseValue, forwardEps (forward means using forecast earning for next 12 month), forwardPE, heldPercentInsiders, heldPercentInstitutions,\nnetIncomeToCommon (income that could be given to common stockholders ttm), pegRatio, priceToBook, trailingEps (for recent past 12 month)',
      'summaryProfile: sector, industry',
      'price: averageDailyVolume10Day, averageDailyVolume3Month, marketCap',
      'symbol',
      'financialData: currentRatio (mrq), debtToEquity (mrq), ebitda (ttm), ebitdaMargins (ttm), freeCashflow (ttm), grossMargins (ttm), grossProfits (ttm), operatingCashflow (ttm), operatingMargins (ttm), profitMargins (ttm), quickRatio (mrq), returnOnAssets (ttm), returnOnEquity (ttm), revenueGrowth (quarterly revenue growth yoy), revenuePerShare (ttm)\ntotalCash (mrq), totalCashPerShare (mrq), totalDebt (mrq), totalRevenue (ttm)',
      'esgScores: environmentScore, esgPerformance, governanceScore, highestControversy, peerEnvironmentPerformance, peerEsgScorePerformance, peerGovernancePerformance, peerHighestControversyPerformance, peerSocialPerformance, socialScore, totalEsg',
      'summaryDetail: fiftyDayAverage, fiftyTwoWeekHigh, fiftyTwoWeekLow, twoHundredDayAverage, dividendRate, dividendYield, fiveYearAvgDividendYield, payoutRatio'
    ]
    '''
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except FileNotFoundError:
        print("File not found.")
    except IOError:
        print("An error occurred while reading the file.")

    # print(len(content.split('\n\n')))
    items = content.split('\n\n')
    return items
  
  def take_subset(self, items, full):
    '''
    items: keys to take subset
    full into for one symbol pulled from one action
    '''
    subset = defaultdict(dict)
    for item in items:
        key_val = item.split(":")
        if len(key_val) == 1:
            # extract whole part for this item, such as symbol
            key = key_val[0]
            subset[key] = full[key]
        elif len(key_val) == 2:
            key, val = key_val
            # for e.g. key = defaultKeyStatistics, val = ' beta (5Y Monthly), bookValue (book value per share), earningsQuarterlyGrowth...'
            for sub_key in val.split(","):
                # for e.g. sub_key = ' beta (5Y Monthly)' or ' bookValue (book value per share)' etc.
                # example 'beta_5Y_Monthly': {'fmt': '1.29', 'raw': 1.289436}
                # first trim the white space using .strip(), then remove the parenthesis when extracting from full dict using .split()
                secondLayer = full[key][sub_key.strip().split(' (', 1)[0]]

                for layerKey in ['raw', 'avg']: # duplicate with below dataframe
                    secondLayer = secondLayer[layerKey] if isinstance(secondLayer, dict) and layerKey in secondLayer else secondLayer

                subset[key][sub_key.strip().replace(" ","_").replace("(","").replace(")","")] = secondLayer
        else:
            raise ValueError("only support nested one layer dictionary")
        
        print("Done: {}".format(key_val[0]))
    
    return subset
  
  
  def convert_dict_to_df(self, data):
    '''
    data: dict we want to convert
    '''
    dict_concat = {}
    for firstKey, dic in data.items():
      # process first layer: e.g. defaultKeyStatistics, summaryProfile, symbol, ... etc.
      print(firstKey)
      if not isinstance(dic, dict):
          dict_concat[firstKey] = dic
          continue
      flat_data = {
          key: value
          for key, value in dic.items()
      }
      dict_concat.update(flat_data)
    
    df = pd.DataFrame([dict_concat])

    df.set_index('symbol', inplace=True)

    new_col_order = ['sector', 'industry'] + [col for col in df.columns if col not in ['sector', 'industry']]
    df = df[new_col_order]

    return df

def main():
  args = parse_args()
  # Read the YAML file
  with open(args.config, 'r') as file:
    yaml_data = yaml.safe_load(file)

  # set up url
  ### Extract the values from YAML get_actions and populate the list
  list_of_actions = []
  for action in yaml_data['get_action']:
    if isinstance(action, str):
      list_of_actions.append(action)
  
  base_url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com"
  section = args.section

  dict_act_smbl = {}
  for action in list_of_actions:
    action = list_of_actions[0] # for simplicity, just perform first action

    url = "{}/{}/{}".format(base_url, section, action)
    print("==== LOG: extract from url: {} ====".format(url))

    
    # pull all symbols from one action
    dict_oneact = {}
    for symbol in yaml_data['symbols']:
      if isinstance(symbol, str):
        querystring['symbol'] = symbol
        print("querystring: ", querystring)
        response = requests.get(url, headers=headers, params=querystring)

        dict_oneact[symbol] = response.json()
    
    # print(dict_oneact.keys())
    
    
  
    dict_act_smbl[action] = dict_oneact
  print(dict_act_smbl.keys())

  ## print long result
  # print("==== long result {} ====")
  # pprint.pprint(dict_act_smbl)


  # take subset using keys
  print("==== subset using keys {} ====".format("stock-v2-get-summary-keys.txt"))
  pipe_funcs = subset_pipe()

  # read txt file into list
  items = pipe_funcs.read_txt_into_list("stock-v2-get-summary-keys.txt")

  action = list_of_actions[0] # for simplicity, just perform first action

  total = pd.DataFrame()
  for symbol in yaml_data['symbols']:
  # symbol = "AMRN"
    full = dict_act_smbl[action][symbol]
    subset_dict = pipe_funcs.take_subset(items, full)
    df = pipe_funcs.convert_dict_to_df(subset_dict)
    total = pd.concat([total, df])

  total.to_csv("stock_get_summary_subset_keys.csv")

  # symbol = "AMRN" does not have environmentScore!


    
if __name__ == "__main__":
  main()