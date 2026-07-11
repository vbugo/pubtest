import pandas as pd
import numpy as np

class DataManager:
    def __init__(self, data_file):
        self.data_file = data_file
        self.current_index = 0
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Загрузка данных из CSV в формате: <DATE>, <TIME>, <OPEN>, <HIGH>, <LOW>, <CLOSE>, <VOL>"""
        try:
            if self.data_file.endswith('.csv'):
                encodings = ['utf-8', 'latin1', 'cp1251', 'iso-8859-1']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(self.data_file, encoding=encoding)
                        print(f"Loaded CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    raise ValueError("Could not read CSV file")
            else:
                raise ValueError("Use CSV format only")
            
            # Удаляем угловые скобки из названий колонок
            df.columns = [col.strip('<>') for col in df.columns]
            
            # Проверяем наличие необходимых колонок
            required = ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'DATE', 'TIME']
            for col in required:
                if col not in df.columns:
                    raise ValueError(f"Missing column: {col}. Available: {list(df.columns)}")
            
            # Создаем timestamp из DATE и TIME
            df['TIMESTAMP'] = pd.to_datetime(df['DATE'].astype(str) + ' ' + df['TIME'].astype(str))
            
            # Добавляем VOL если нет
            if 'VOL' not in df.columns:
                df['VOL'] = 0
            
            # Конвертируем в числа
            for col in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOL']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Удаляем строки с NaN
            df = df.dropna(subset=['OPEN', 'HIGH', 'LOW', 'CLOSE'])
            
            # Сортируем по времени
            df = df.sort_values('TIMESTAMP')
            
            # Сбрасываем индекс
            df = df.reset_index(drop=True)
            
            self.data = df
            print(f"✓ Loaded {len(self.data)} candles")
            print(f"  Date range: {self.data['TIMESTAMP'].min()} to {self.data['TIMESTAMP'].max()}")
            print(f"  Price range: {self.data['LOW'].min():.2f} - {self.data['HIGH'].max():.2f}")
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_candles(self, count):
        """Get last N candles ending at current index"""
        if self.data is None or len(self.data) == 0:
            return pd.DataFrame()
        
        start = max(0, self.current_index - count + 1)
        end = self.current_index + 1
        return self.data.iloc[start:end].copy()
    
    def get_current_candle(self):
        """Get current candle"""
        if self.data is None or self.current_index >= len(self.data):
            return None
        return self.data.iloc[self.current_index]
    
    def prev_candle(self):
        """Move to previous candle"""
        if self.data is not None and self.current_index > 0:
            self.current_index -= 1
            return True
        return False
    
    def next_candle(self):
        """Move to next candle"""
        if self.data is not None and self.current_index < len(self.data) - 1:
            self.current_index += 1
            return True
        return False
    
    def reset(self):
        """Reset to first candle"""
        if self.data is not None:
            self.current_index = 0
    
    def go_to_end(self):
        """Go to last candle"""
        if self.data is not None:
            self.current_index = len(self.data) - 1
    
    def get_total_candles(self):
        return len(self.data) if self.data is not None else 0
    
    def get_progress(self):
        if self.data is None or len(self.data) == 0:
            return 0
        return (self.current_index + 1) / len(self.data) * 100