# Define the starting number and the limit
start_number = 144
limit = 1973

# Open a text file in write mode
with open("sequence.txt", "w") as file:
    current_number = start_number
    # Iterate until the current number exceeds the limit
    while current_number <= limit:
        # Write the current number to the file
        file.write(str(current_number) + "\n")
        # Increment the current number by 96, but don't exceed the limit
        current_number = current_number + 96

