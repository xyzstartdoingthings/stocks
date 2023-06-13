import requests
import argparse
import os
import random
import json
import pprint

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
      # action = list_of_actions[0] # for simplicity, just perform first action

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
    print("==== long result {} ====")
    pprint.pprint(dict_act_smbl)


    
if __name__ == "__main__":
  main()