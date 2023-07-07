import requests
import argparse
import os
import random
import json
import pprint
from collections import defaultdict
import pandas as pd

from src.processors import processors_mapping

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
    parser.add_argument(
      '-as', "--all_symbol", 
      default=False, 
      help="whether use all symbol", 
      action='store_true'
    )
    
    args = parser.parse_args()
    return args


def main():
  args = parse_args()
  # Read the YAML file
  with open(args.config, 'r') as file:
    yaml_data = yaml.safe_load(file)


  # print("===", type(args.all_symbol))
  if args.all_symbol:
    all_stock = pd.read_csv("All_Stock.csv")
    sampled_df = all_stock['Symbol'].sample(frac=1, random_state=42)
    yaml_data['symbols'] = sampled_df[:100]
  
  # print("===zhuoyan", yaml_data['symbols'])
  # assert(False)
    
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
    exist_symbols = []
    for symbol in yaml_data['symbols']:
      if isinstance(symbol, str):
        querystring['symbol'] = symbol
        print("querystring: ", querystring)
        response = requests.get(url, headers=headers, params=querystring)

        if response.json():
          dict_oneact[symbol] = response.json()
          exist_symbols.append(symbol)
    
    # print(dict_oneact.keys())
    
    
  
    dict_act_smbl[action] = dict_oneact
  print(dict_act_smbl.keys())

  ## print long result
  # print("==== long result {} ====")
  # pprint.pprint(dict_act_smbl)


  # take subset using keys
  print("==== subset using keys {} ====".format("stock-v2-\{\}-keys.txt"))
  
  # for simplicity, just use one action
  action_key = yaml_data['get_action'][0].split("/")[1]  # v2/get-summary  --> get-summary
  pipe_funcs = processors_mapping[action_key]

  
  # ==== below I wrap into pipe_funcs.pipeline ====
  # read txt file into list
  # items = pipe_funcs.read_txt_into_list("stock-v2-{}-keys.txt".format(action_key)) # stock-v2-get-summary-keys.txt
  # action = list_of_actions[0] # for simplicity, just perform first action
  # total = pd.DataFrame()
  # for symbol in exist_symbols:
  #   full = dict_act_smbl[action][symbol]
  #   subset_dict = pipe_funcs.take_subset(items, full)
  #   df = pipe_funcs.convert_dict_to_df(subset_dict)
  #   total = pd.concat([total, df])
  
  total = pipe_funcs.pipeline("stock-v2-{}-keys.txt".format(action_key), dict_act_smbl, exist_symbols)

  # pprint.pprint(total)
  save_index = True
  if action == "v2/get-financials":
    save_index = False
  total.to_csv("stock_{}_subset_keys_random.csv".format(action_key), index=save_index)

    
if __name__ == "__main__":
  main()