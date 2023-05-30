import requests
import argparse
import os
import random
import json
import pprint

import yaml

headers = {
    "X-RapidAPI-Key": "551595c10emsh9ab76ccfb317820p1fa121jsnc738c9455698",
    "X-RapidAPI-Host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
  }

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
      '-v', "--version", 
      type=str,
      default='v3', 
      help="which version we use for pull", 
      choices=['v2', 'v3', 'v4']
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
    version = args.version

    action = list_of_actions[0] # for simplicity, just perform first action

    url = "{}/{}/{}/{}".format(base_url, section, version, action)
    print("==== LOG: extract from url: {} ====".format(url))

    # set up query string
    ### Extract the values from YAML get_actions and populate the list
    querystring = {"symbol":"AMRN","region":"US","lang":"en-US", "range":"1d", "straddle":"true"}
    str_of_symbols = ""
    for symbol in yaml_data['symbols']:
      if isinstance(symbol, str):
        str_of_symbols += "{},".format(symbol)
    
    # querystring = {'symbol': 'AMRN', 'region': 'US', 'lang': 'en-US', 'range': '1d', 'straddle': 'true'}



    response = requests.get(url, headers=headers, params=querystring)

    pprint.pprint(response.json())


    
if __name__ == "__main__":
  main()