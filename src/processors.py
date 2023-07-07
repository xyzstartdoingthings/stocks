from collections import defaultdict
import pandas as pd


class subset_pipe_get_summary:
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
              try:
                secondLayer = full[key][sub_key.strip().split(' (', 1)[0]]
                for layerKey in ['raw', 'avg']: # duplicate with below dataframe
                  secondLayer = secondLayer[layerKey] if isinstance(secondLayer, dict) and layerKey in secondLayer else secondLayer

                subset[key][sub_key.strip().replace(" ","_").replace("(","").replace(")","")] = secondLayer
              
              except (KeyError, TypeError, AttributeError):
                subset[key][sub_key.strip().replace(" ","_").replace("(","").replace(")","")] = {}
                print("Key not found or error occurred while accessing the dictionary {} using key {}:{}.".format(full['symbol'],key,sub_key.strip().split(' (', 1)[0]))
              
        else:
            raise ValueError("only support nested one layer dictionary")
        
        # print("Done: {}".format(key_val[0]))
    
    return subset
  
  
  def convert_dict_to_df(self, data):
    '''
    data: dict we want to convert
    '''
    dict_concat = {}
    for firstKey, dic in data.items():
      # process first layer: e.g. defaultKeyStatistics, summaryProfile, symbol, ... etc.
      # print(firstKey)
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
  
  def pipeline(self, file_path:str, dict_act_smbl: dict, exist_symbols:list):
    if not file_path:
       file_path = "stock-v2-{}-keys.txt".format("get-summary")
    # read txt file into list
    items = self.read_txt_into_list(file_path) # stock-v2-get-summary-keys.txt

    action = "v2/get-summary" # for simplicity, just perform first action

    total = pd.DataFrame()
    for symbol in exist_symbols:
      full = dict_act_smbl[action][symbol]
    # symbol = "AMRN"
      subset_dict = self.take_subset(items, full)
      df = self.convert_dict_to_df(subset_dict)
      total = pd.concat([total, df])
    
    return total



class subset_pipe_get_financials:
  def __init__(self, keys_txt = None):
    pass
  def pipeline(self, file_path:str, dict_act_smbl: dict, exist_symbols:list = None):
    if not file_path:
       file_path = "stock-v2-{}-keys.txt".format("get-financials")
    try:
      with open(file_path, 'r') as file:
          content = file.read()
    except FileNotFoundError:
      print("File not found.")
    except IOError:
      print("An error occurred while reading the file.")

    items = content.split('\n\n')
    

    action = 'v2/get-financials'
    total = pd.DataFrame()
    for symbol in exist_symbols:
      full = dict_act_smbl[action][symbol]
    # symbol = "AAPL"
    # full = dict_act_smbl['v2/get-financials'][symbol]

      quarter_info = defaultdict(dict)
      for item in items:
          key_val = item.split(":")
          for quarter_id in range(4):
              subset = defaultdict(dict)
              for sub_key in key_val[3].split(","):
                  leafLayer = full[key_val[0].strip()][key_val[1].strip()][quarter_id][sub_key.strip()]
                  for layerKey in ['raw', 'avg']: # duplicate with below dataframe
                          leafLayer = leafLayer[layerKey] if isinstance(leafLayer, dict) and layerKey in leafLayer else leafLayer
                  subset[sub_key.strip()] = leafLayer

              quarter_info[quarter_id].update(subset)

      # Convert the flattened dictionary into a DataFrame
      df = pd.DataFrame.from_dict(quarter_info, orient='index')
      df = df.reset_index().rename(columns={'index': 'Category'})
      df['symbol'] = symbol
      new_col_order = ['symbol'] + [col for col in df.columns if col not in ['symbol']]
      df = df[new_col_order]

      total = pd.concat([total, df])
    
    return total

      
   
processors_mapping = {
    "get-summary": subset_pipe_get_summary(),
    "get-financials": subset_pipe_get_financials()
    }