#!/bin/bash

# Initialize idx with 144
idx=144

# Loop until idx is less than or equal to 1000
while [ $idx -le 624 ]
do
  # Run the python script with the current idx value
  python ticker_selecter_parallel.py --idx $idx
  
  # Increase idx by 96
  idx=$((idx + 96))
done

