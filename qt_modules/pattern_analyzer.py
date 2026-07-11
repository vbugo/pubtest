import pandas as pd
import numpy as np

class PatternAnalyzer:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.neutral_idx = None
        self.pullback_idx = None
        self.coefficient = 0.5
        self.load_coefficient()
    
    def load_coefficient(self):
        try:
            with open('pattern_coefficient.txt', 'r') as f:
                self.coefficient = float(f.read().strip())
                print(f"Loaded coefficient: {self.coefficient}%")
        except:
            print(f"Using default coefficient: {self.coefficient}%")
    
    def save_coefficient(self, value):
        with open('pattern_coefficient.txt', 'w') as f:
            f.write(str(value))
        self.coefficient = value
    
    def find_neutral_impulse_pullback(self, start_idx, direction='up'):
        data = self.data_manager.data
        if data is None:
            return None
        
        if direction == 'up':
            get_progress = lambda high, neutral: ((high - neutral) / neutral) * 100
        else:
            get_progress = lambda low, neutral: abs(((low - neutral) / neutral) * 100)
        
        for idx in range(start_idx, min(start_idx + 100, len(data) - 7)):
            c1 = data.iloc[idx]
            if abs(c1['CLOSE'] - c1['OPEN']) / c1['OPEN'] * 100 > 0.15:
                continue
            
            neutral_price = c1['CLOSE']
            
            # Ищем импульс
            impulse_indices = []
            for j in range(idx + 1, min(idx + 6, len(data))):
                candle = data.iloc[j]
                if direction == 'up':
                    if candle['CLOSE'] > candle['OPEN']:
                        impulse_indices.append(j)
                    else:
                        break
                else:
                    if candle['CLOSE'] < candle['OPEN']:
                        impulse_indices.append(j)
                    else:
                        break
            
            if len(impulse_indices) < 1:
                continue
            
            # Pullback
            pullback_idx = impulse_indices[-1] + 1
            if pullback_idx >= len(data):
                continue
            
            # Расчеты
            results = []
            for imp_idx in impulse_indices:
                candle = data.iloc[imp_idx]
                if direction == 'up':
                    high = candle['HIGH']
                    diff = high - neutral_price
                    percent = get_progress(high, neutral_price)
                else:
                    low = candle['LOW']
                    diff = neutral_price - low
                    percent = get_progress(low, neutral_price)
                
                results.append({
                    'type': 'impulse',
                    'candle_num': imp_idx - idx + 1,
                    'price': high if direction == 'up' else low,
                    'diff': diff,
                    'percent': percent
                })
            
            # Pullback расчет
            pullback = data.iloc[pullback_idx]
            if direction == 'up':
                high = pullback['HIGH']
                diff = high - neutral_price
                percent = get_progress(high, neutral_price)
            else:
                low = pullback['LOW']
                diff = neutral_price - low
                percent = get_progress(low, neutral_price)
            
            results.append({
                'type': 'pullback',
                'candle_num': pullback_idx - idx + 1,
                'price': high if direction == 'up' else low,
                'diff': diff,
                'percent': percent
            })
            
            # Общий процент
            if direction == 'up':
                peak = max(data.iloc[impulse_indices]['HIGH'])
                impulse_percent = get_progress(peak, neutral_price)
            else:
                trough = min(data.iloc[impulse_indices]['LOW'])
                impulse_percent = get_progress(trough, neutral_price)
            
            if impulse_percent >= self.coefficient:
                return {
                    'start_idx': idx,
                    'neutral_idx': idx,
                    'neutral_price': neutral_price,
                    'impulse_indices': impulse_indices,
                    'pullback_idx': pullback_idx,
                    'direction': direction,
                    'results': results,
                    'impulse_candles_count': len(impulse_indices),
                    'impulse_percent': impulse_percent
                }
        
        return None
    
    def search_forward(self, start_idx=None):
        if start_idx is None:
            start_idx = self.data_manager.current_index
        
        result_up = self.find_neutral_impulse_pullback(start_idx, 'up')
        if result_up:
            return result_up
        
        result_down = self.find_neutral_impulse_pullback(start_idx, 'down')
        return result_down
    
    def search_backward(self, start_idx=None):
        if start_idx is None:
            start_idx = self.data_manager.current_index
        
        for idx in range(start_idx, -1, -1):
            result_up = self.find_neutral_impulse_pullback(idx, 'up')
            if result_up:
                return result_up
            result_down = self.find_neutral_impulse_pullback(idx, 'down')
            if result_down:
                return result_down
        
        return None