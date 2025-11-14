#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nöbetçi Öğretmen Yönetim Sistemi – Giriş Noktası
@author:
    Şenol Irmak
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QDate
from views.main_window import NobetSistemi
from db.database import engine, Base

def load_stylesheet():
    with open("ui/style/default.qss", "r", encoding="utf-8") as f:
        return f.read()

def main():
    """Ana PyQt5 uygulamasını başlatır."""
    app = QApplication(sys.argv)
    # Genel stil ayarları
    app.setStyle("Fusion")  # Qt’nin dahili modern stili
    app.setStyleSheet(load_stylesheet())
    
    try:
        # Veritabanı başlatma (tablo yoksa oluştur)
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        QMessageBox.critical(None, "Veritabanı Hatası", f"Veritabanı başlatılamadı:\n{str(e)}")
        sys.exit(1)
        
    window = NobetSistemi()

    if hasattr(window, "date_uygulama_tarihi"):
        window.date_uygulama_tarihi.setDate(QDate.currentDate())    

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

