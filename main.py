#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut
from qt_modules.chart_widget import CandlestickChart
from qt_modules.data_manager import DataManager
from qt_modules.pattern_analyzer import PatternAnalyzer

class MainWindow(QMainWindow):
    def __init__(self, data_file):
        super().__init__()
        self.data_manager = DataManager(data_file)
        
        if self.data_manager.data is None:
            print("Failed to load data. Exiting.")
            sys.exit(1)
        
        self.pattern_analyzer = PatternAnalyzer(self.data_manager)
        self.initUI()
        self.update_charts()
        self.analyze_pattern()
    
    def initUI(self):
        self.setWindowTitle("Trading Tool - SBER Data")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("background-color: #000000;")
        
        # Создаем виджеты графиков
        self.chart_5 = CandlestickChart(self)
        self.chart_15 = CandlestickChart(self)
        
        # Правая панель с результатами
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Коэффициент
        coef_layout = QHBoxLayout()
        coef_label = QLabel("Coefficient (%):")
        coef_label.setStyleSheet("color: #aaaaaa;")
        self.coef_input = QLineEdit(str(self.pattern_analyzer.coefficient))
        self.coef_input.setStyleSheet("background-color: #2d2d2d; color: #00ff00; padding: 5px;")
        self.coef_input.textChanged.connect(self.on_coef_changed)
        coef_layout.addWidget(coef_label)
        coef_layout.addWidget(self.coef_input)
        coef_layout.addStretch()
        right_layout.addLayout(coef_layout)
        
        # Кнопки поиска
        search_layout = QHBoxLayout()
        self.search_forward_btn = QPushButton("Search Forward (F6)")
        self.search_backward_btn = QPushButton("Search Backward (F2)")
        self.search_forward_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        self.search_backward_btn.setStyleSheet("background-color: #ff9800; color: white; padding: 5px;")
        search_layout.addWidget(self.search_backward_btn)
        search_layout.addWidget(self.search_forward_btn)
        right_layout.addLayout(search_layout)
        
        # Текстовый виджет для результатов
        self.results_text = QTextEdit()
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #aaaaaa;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.results_text.setReadOnly(True)
        right_layout.addWidget(self.results_text)
        
        right_panel.setLayout(right_layout)
        
        # Layout
        central = QWidget()
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(self.chart_5)
        left_layout.addWidget(self.chart_15)
        
        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(right_panel, 1)
        
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        self.statusBar().setVisible(False)
        
        # Горячие клавиши
        QShortcut(Qt.Key.Key_Left, self).activated.connect(self.prev_candle)
        QShortcut(Qt.Key.Key_Right, self).activated.connect(self.next_candle)
        QShortcut(Qt.Key.Key_R, self).activated.connect(self.reset)
        QShortcut(Qt.Key.Key_Space, self).activated.connect(self.go_to_end)
        QShortcut(Qt.Key.Key_Q, self).activated.connect(self.close)
        QShortcut(Qt.Key.Key_PageUp, self).activated.connect(self.prev_hour)
        QShortcut(Qt.Key.Key_PageDown, self).activated.connect(self.next_hour)
        QShortcut(Qt.Key.Key_F6, self).activated.connect(self.search_forward)
        QShortcut(Qt.Key.Key_F2, self).activated.connect(self.search_backward)
        
        # Кнопки
        self.search_forward_btn.clicked.connect(self.search_forward)
        self.search_backward_btn.clicked.connect(self.search_backward)
    
    def on_coef_changed(self):
        """Сохранение коэффициента"""
        try:
            val = float(self.coef_input.text())
            self.pattern_analyzer.save_coefficient(val)
        except:
            pass
    
    def analyze_pattern(self):
        candles_7 = self.chart_5.last_data
        
        if candles_7 is None or len(candles_7) < 7:
            self.results_text.setText("Not enough data on chart")
            return
        
        neutral = candles_7.iloc[0]
        neutral_price = neutral['CLOSE']
        neutral_time = neutral['TIMESTAMP'].strftime('%H:%M')
        
        results_text = []
        results_text.append(f"C1 ({neutral_time}) Close = {neutral_price:.2f}")
        
        for i in range(1, 7):
            candle = candles_7.iloc[i]
            high = candle['HIGH']
            diff = high - neutral_price
            percent = (diff / neutral_price) * 100
            
            # Определяем тип свечи
            candle_type = ""
            if i == 6:
                candle_type = " [Sideway]"
            else:
                # Проверка на боковик (изменение < 0.05%)
                change = abs(candle['CLOSE'] - candle['OPEN']) / candle['OPEN'] * 100
                if change < 0.05:
                    candle_type = " [Sideway]"
            
            results_text.append(f"{high:.2f}  {diff:.2f} {percent:.3f}%{candle_type}")
        
        self.results_text.setText("\n".join(results_text))
    
    def search_forward(self):
        """Поиск паттерна вперед"""
        result = self.pattern_analyzer.search_forward(self.data_manager.current_index)
        if result:
            self.go_to_position(result['start_idx'])
            self.show_pattern_result(result)
        else:
            self.results_text.append("\n⚠ Pattern not found forward")
    
    def search_backward(self):
        """Поиск паттерна назад"""
        result = self.pattern_analyzer.search_backward(self.data_manager.current_index)
        if result:
            self.go_to_position(result['start_idx'])
            self.show_pattern_result(result)
        else:
            self.results_text.append("\n⚠ Pattern not found backward")
    
    def show_pattern_result(self, result):
        """Отображение результата паттерна"""
        neutral_price = result['neutral_price']
        results = result['results']
        
        # Получаем время для C1
        c1_time = self.data_manager.data.iloc[result['neutral_idx']]['TIMESTAMP'].strftime('%H:%M')
        
        text = [f"🎯 PATTERN FOUND ({result['direction'].upper()})"]
        text.append(f"C1 ({c1_time}) Close = {neutral_price:.2f}")
        text.append("-" * 50)
        
        for r in results:
            # Получаем время свечи
            if r['type'] == 'impulse':
                candle_idx = result['impulse_indices'][r['candle_num'] - 2]
            else:
                candle_idx = result['pullback_idx']
            
            time = self.data_manager.data.iloc[candle_idx]['TIMESTAMP'].strftime('%H:%M')
            suffix = " [Pullback]" if r['type'] == 'pullback' else ""
            
            text.append(f"{time}  {r['price']:.2f} - {neutral_price:.2f} = {r['diff']:.2f} ({r['percent']:+.3f}%){suffix}")
        
        text.append("-" * 50)
        text.append(f"Impulse candles: {result['impulse_candles_count']}")
        text.append(f"Total impulse: {result['impulse_percent']:.3f}%")
        
        self.results_text.setText("\n".join(text))
    
    def go_to_position(self, idx):
        """Переход к позиции"""
        self.data_manager.current_index = idx
        self.update_charts()
    
    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        
        # Растягиваем графики
        left_w = w * 2 // 3
        chart_h_top = int(h * 0.48)
        chart_h_bottom = h - chart_h_top
        
        self.chart_5.setGeometry(0, 0, left_w, chart_h_top)
        self.chart_15.setGeometry(0, chart_h_top, left_w, chart_h_bottom)
        
        super().resizeEvent(event)
    
    def next_hour(self):
        current_idx = self.data_manager.current_index
        new_idx = min(current_idx + 60, self.data_manager.get_total_candles() - 1)
        for _ in range(new_idx - current_idx):
            self.data_manager.next_candle()
        self.update_charts()
        self.analyze_pattern()

    def prev_hour(self):
        current_idx = self.data_manager.current_index
        new_idx = max(current_idx - 60, 0)
        for _ in range(current_idx - new_idx):
            self.data_manager.prev_candle()
        self.update_charts()
        self.analyze_pattern()
    
    def prev_candle(self):
        if self.data_manager.prev_candle():
            self.update_charts()
            self.analyze_pattern()

    def next_candle(self):
        if self.data_manager.next_candle():
            self.update_charts()
            self.analyze_pattern()

    def reset(self):
        self.data_manager.reset()
        self.update_charts()
        self.analyze_pattern()

    def go_to_end(self):
        self.data_manager.go_to_end()
        self.update_charts()
        self.analyze_pattern()
    
    def update_charts(self):
        candles_15 = self.data_manager.get_candles(15)
        self.chart_15.update_chart(candles_15)
        
        if len(candles_15) >= 15:
            candles_7 = candles_15.iloc[4:11].copy()
        elif len(candles_15) >= 7:
            candles_7 = candles_15.iloc[-7:].copy()
        else:
            candles_7 = self.data_manager.get_candles(7)
        
        self.chart_5.update_chart(candles_7)
        self.analyze_pattern()  # Анализируем после обновления

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <data.csv>")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    window = MainWindow(sys.argv[1])
    window.show()
    sys.exit(app.exec())