#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  4 14:48:51 2025

@author: senolirmak
"""

import sys
from PyQt5.QtWidgets import QApplication
from nobetcigorevi.views.main_window import NobetSistemi
from nobetcigorevi.db.database import engine
from nobetcigorevi.db.models import Base

# Tabloları oluştur(sadece bir kere çalıştırılmalı)
Base.metadata.create_all(bind=engine)

def main():
    app = QApplication(sys.argv)
    
    # Genel stil ayarları
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QListWidget, QTableView {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        QLabel {
            font-weight: bold;
        }
        QComboBox {
            min-height: 30px;
        }
        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        QTabBar::tab {
            padding: 8px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #3498db;
        }
    """)
    
    ana_pencere = NobetSistemi()
    ana_pencere.show()
    sys.exit(app.exec())