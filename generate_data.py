import csv
import numpy as np
from datetime import datetime, timedelta

print("Generating sample data...")

start_date = datetime(2024, 1, 1)
num_candles = 1000
prices = [100.00]

np.random.seed(42)

for i in range(num_candles):
    change = np.random.normal(0, 0.5)
    new_price = max(prices[-1] + change, 50)
    prices.append(new_price)

with open('data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    for i in range(num_candles):
        timestamp = start_date + timedelta(minutes=i)
        open_price = prices[i]
        close_price = prices[i+1]
        high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.3))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.3))
        volume = np.random.randint(100, 10000)
        
        writer.writerow([
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            round(open_price, 4),
            round(high_price, 4),
            round(low_price, 4),
            round(close_price, 4),
            volume
        ])

print("✓ Generated data.csv with 1000 candles")