
#!/bin/bash

# Initialize idx with 144
idx=624

# Loop until idx is less than or equal to 1000
while [ $idx -le 1104 ]
do
  # Run the python script with the current idx value
  python ticker_selecter_parallel.py --idx $idx
  
  # Increase idx by 96
  idx=$((idx + 96))
done

