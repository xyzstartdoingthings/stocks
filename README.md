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

 - modify `config/basic.yaml` for more get_actions and symbols. 
 - Not yet robust, certain actions only applied to vertain symbols. For e.g. `stock/v4/get-statistics` cannot extract AAPL, AMRN, ESLA, etc.
 - Now pull one symbol with one action at a time.
