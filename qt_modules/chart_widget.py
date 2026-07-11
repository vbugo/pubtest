from PyQt6.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('dark_background')

class CandlestickChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(facecolor='black', dpi=100)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.last_data = None  # Добавить эту строку
        self.setup_style()
    
    def setup_style(self):
        self.ax.set_facecolor('black')
        self.ax.set_title('')
        self.ax.set_xlabel('')
        self.ax.set_ylabel('')
        self.ax.tick_params(colors='#888888', labelsize=9)
        self.ax.grid(True, alpha=0.1, color='#333333')
        
        for spine in self.ax.spines.values():
            spine.set_color('#333333')
        
        self.fig.subplots_adjust(left=0.12, bottom=0.12, top=0.95)

    def update_chart(self, data):
        self.last_data = data  # Сохраняем данные
        self.ax.clear()
        self.setup_style()
    
        if data is None or len(data) == 0:
            self.draw()
            return
        
        # Рисуем свечи
        width = 0.6
        for i in range(len(data)):
            row = data.iloc[i]
            o = row['OPEN']
            h = row['HIGH']
            l = row['LOW']
            c = row['CLOSE']
            
            color = '#00ff00' if c >= o else '#ff3333'
            
            # Фитиль
            self.ax.plot([i, i], [l, h], color=color, linewidth=1.5, alpha=0.8)
            
            # Тело свечи
            body_h = abs(c - o)
            body_bottom = min(o, c)
            rect = plt.Rectangle((i - width/2, body_bottom), width, body_h,
                                facecolor=color, edgecolor=color, alpha=0.9, linewidth=1)
            self.ax.add_patch(rect)
        
        # Границы с отступом
        price_min = data['LOW'].min()
        price_max = data['HIGH'].max()
        margin = (price_max - price_min) * 0.1
        
        self.ax.set_xlim(-0.7, len(data) - 0.3)
        self.ax.set_ylim(price_min - margin, price_max + margin)
        
        # Время на оси X
        if 'TIMESTAMP' in data.columns:
            times = []
            for t in data['TIMESTAMP']:
                if hasattr(t, 'strftime'):
                    times.append(t.strftime('%H:%M'))
                else:
                    times.append(str(t)[-8:-3] if len(str(t)) > 5 else str(t))
            
            self.ax.set_xticks(range(len(data)))
            self.ax.set_xticklabels(times, ha='center', fontsize=8, rotation=0)
            
            for label in self.ax.get_xticklabels():
                label.set_color('#aaaaaa')
        
        # Настройка Y оси
        from matplotlib.ticker import FormatStrFormatter, MaxNLocator
        
        self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        self.ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        
        for label in self.ax.get_yticklabels():
            label.set_color('#aaaaaa')
            label.set_fontsize(9)
        
        self.ax.tick_params(axis='y', pad=8)
        self.ax.grid(True, alpha=0.1, color='#333333', linestyle='-', linewidth=0.5)
        
        self.draw()