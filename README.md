# stocks

## Pull data from yahoo finance
 - [Rapid API](https://rapidapi.com/apidojo/api/yahoo-finance1)


### Examples
python command
```
python pull.py \
    --config=config/basic.yaml \
    -s stock \
    > res.txt
```
or `python pull.py` for short.

 - modify `config/basic.yaml` for more symbols. add `python pull.py -as` for use symbols from `All_stock.csv`.
 - Since each action require different processing pipeline, each `python pull.py` run just perform one action.
 - Not yet robust, certain actions only applied to vertain symbols. For e.g. `stock/v4/get-statistics` cannot extract AAPL, AMRN, ESLA, etc.
