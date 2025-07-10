#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4 19:35:28 2025

@author: senolirmak
"""

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QWidget, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QColor, QBrush

import traceback  # Bu satırı dosyanın en üstündeki import bölümüne ekleyin
from nobet.utils.database_util import TeacherManager

class PencereFonksiyon:
    def __init__(self):
        super().__init__()
        self.data = TeacherManager()
        # Renk tanımlamaları
        self.black_color = QColor(0, 0, 0)       # Siyah
        self.green_color = QColor(0, 255, 0)      # Yeşil
        self.white_color = QColor(255, 255, 255)  # Beyaz
        # Renk tanımları
        self.yellow_color = QColor(255, 255, 0)     #Sarı
        self.locked_color = QColor(240, 240, 240)  # Kilitli hücre rengi
        self.initial_colors = {
            0: QColor(173, 216, 230),   # Light blue for teachers
            1: QColor(144, 238, 144),   # Light green
            2: QColor(255, 182, 193),    # Light pink
            3: QColor(220, 220, 220),    # Light gray
            4: QColor(255, 218, 185),    # Peach
            5: QColor(221, 160, 221),    # Plum
            6: QColor(152, 251, 152),    # Pale green
            7: QColor(175, 238, 238),    # Pale turquoise
            8: QColor(255, 228, 196)     # Bisque
        }
        
        # Column colors
        column_colors = {
            0: QColor(173, 216, 230),   # Light blue for teachers
            1: QColor(144, 238, 144),   # Light green
            2: QColor(255, 182, 193),   # Light pink
            3: QColor(220, 220, 220),   # Light gray
            4: QColor(255, 218, 185),   # Peach
            5: QColor(221, 160, 221),   # Plum
            6: QColor(152, 251, 152),   # Pale green
            7: QColor(175, 238, 238),  # Pale turquoise
            8: QColor(255, 228, 196)    # Bisque
        }
    
    def get_optimization_weights(self, mode):
        """Get optimization weights based on slider mode"""
        presets = {
            1: {'overload': 50, 'inequality': 100, 'unassigned': 200, 'no_duty': 150, 'conflict': 1000},
            2: {'overload': 100, 'inequality': 200, 'unassigned': 220, 'no_duty': 300, 'conflict': 1000},
            3: {'overload': 150, 'inequality': 300, 'unassigned': 200, 'no_duty': 100, 'conflict': 1000},
            4: {'overload': 200, 'inequality': 400, 'unassigned': 100, 'no_duty': 50, 'conflict': 1000}
        }
        return presets.get(mode)
        
    def setup_devamsiz_ogretmen_table(self, table_widget):
        """Tabloyu başlıklarla birlikte kurar"""
        headers = ["Devamsız Öğretmen"] + [f"{i}.Ders" for i in range(1, 9)]
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        # Sütun genişliklerini ayarla
        table_widget.resizeColumnsToContents()
        # Alternatif satır renklendirme
        table_widget.setAlternatingRowColors(False)  # Kendi renklerimizi kullanıyoruz        

    def add_devamsiz_ogretmen_scheduler(self, table_widget, teacher_data):
        """
        Öğretmen ders programını tabloya ekler
        :param table_widget: QTableWidget nesnesi
        :param teacher_data: {ogretmen_id: int, dersleri: {ders_saati: sinif}} formatında veri
        """
    
        teacher_info = teacher_data.copy()
        
        teacher_id = teacher_info['ogretmen_id']
        teacher_name = self.data.get_ogretmen_adi(teacher_id)
        lessons = teacher_info['dersleri']
        
        # Öğretmen ID kontrolü
        if table_widget.rowCount() != 0:
            for row in range(table_widget.rowCount()):
                if table_widget.item(row, 0).data(Qt.UserRole) == teacher_id:
                    QMessageBox.warning(None, "Uyarı", 
                                      f"Devamsız Öğretmen {teacher_name} tabloda mevcut!")
                    return
        
        # Yeni satır ekle
        row = table_widget.rowCount()
        table_widget.insertRow(row)
        
        # Öğretmen ismini ekle (UserRole olarak ID'yi sakla)
        teacher_item = QTableWidgetItem(teacher_name)
        teacher_item.setData(Qt.UserRole, teacher_id)
        teacher_item.setFlags(teacher_item.flags() & ~Qt.ItemIsEditable)
        table_widget.setItem(row, 0, teacher_item)
        # Tüm ders saatleri için hücre oluştur
        for hour in range(1, 9):
            col = hour
            class_info = lessons.get(hour, "")
            item = QTableWidgetItem(class_info)
            item.setData(Qt.UserRole, {'hour': hour, 'class': class_info})
            
            # Hücre stilini ayarla
            if not class_info:
                # Boş hücreleri siyah yap
                item.setBackground(QBrush(self.black_color))
                item.setForeground(QBrush(self.white_color))  # Yazı rengi beyaz
            else:
                # Dolu hücreler
                item.setBackground(self.initial_colors[col])  # Sütun rengi
                item.setForeground(QBrush(self.black_color))
            
            table_widget.setItem(row, col, item)
        
        # Sütun genişliklerini ayarla
        table_widget.resizeColumnsToContents()
        # Alternatif satır renklendirme
        table_widget.setAlternatingRowColors(False)  # Kendi renklerimizi kullanıyoruz
       
    def nobet_atamalarini_say(self, main_table):
        """
        Nöbetçi öğretmenlerin yeni atamalarını sayar ve istatistik tablosunu oluşturur
        param main_table: Nöbetçi öğretmen ders dağıtım tablosu (QTableWidget)
        """
        # Öğretmen ID'lerini ve yeni atama sayılarını topla
        stats = {}
        
        for row in range(main_table.rowCount()):
            teacher_id_item = main_table.item(row, 0)
            if teacher_id_item:
                teacher_id = teacher_id_item.data(Qt.UserRole)
                new_assignments = 0
                
                # Ders sütunlarını kontrol et (1-8)
                for col in range(1, 9):
                    item = main_table.item(row, col)
                    if item is None:
                        continue
                    if item.background() == self.yellow_color:  # Sarı olanlar yeni atamalar
                        new_assignments += 1
                
                stats[teacher_id] = new_assignments
                
        return stats
    
    def atama_sonuc_tablosu_yukle(self, table_atama, table_devamsiz, ogretmen_data, dagilim_sonuc=None):
        if not ogretmen_data:
            print("Veri Boş")
            return
        table_atama.clear()
        # Sütun başlıkları (Öğretmen + 8 ders saati)
        headers = ["Nöbetçi Öğretmen"] + [f"{i}.Ders" for i in range(1, 9)]
        
        # Sütun ve satır sayısını ayarla
        table_atama.setColumnCount(len(headers))
        table_atama.setRowCount(len(ogretmen_data))
        # Başlıkları ayarla
        table_atama.setHorizontalHeaderLabels(headers)
        
        # Başlık stilleri
        header = table_atama.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #f0f0f0; }")
        # Verileri tabloya ekle
        for row, teacher_data in enumerate(ogretmen_data):
            # Öğretmen adını ekle (gösterim için)
            teacher_id = teacher_data['ogretmen_id']
            teacher_name = self.data.get_ogretmen_adi(teacher_id)
            teacher_item = QTableWidgetItem(teacher_name)
            teacher_item.setData(Qt.UserRole, teacher_id)  # ID'yi sakla
            teacher_item.setFlags(teacher_item.flags() & ~Qt.ItemIsEditable)
            teacher_item.setBackground(self.initial_colors[0])  # Öğretmen rengi
            #teacher_item.setBackground(QBrush(self.white_color))
            table_atama.setItem(row, 0, teacher_item)
            
            # Tüm ders saatleri için hücre oluştur
            for hour in range(1, 9):
                col = hour
                class_info = teacher_data['dersleri'].get(hour, "")
                
                # Hücre stilini ayarla
                if not class_info:
                    # Boş hücreleri siyah yap
                    item = QTableWidgetItem(class_info)
                    item.setBackground(QBrush(self.black_color))
                    item.setForeground(QBrush(self.white_color))  # Yazı rengi beyaz
                else:
                    # Dolu hücreler
                    item = QTableWidgetItem(class_info)
                    item.setData(Qt.UserRole, {'hour': hour, 'class': class_info})
                    item.setBackground(self.locked_color)  # Sütun rengi
                    item.setForeground(QBrush(self.black_color))
                
                table_atama.setItem(row, col, item)
        
        # Dağıtım sonuçlarına göre yeni atamaları işaretle assignment['absent_teacher_id']
        if dagilim_sonuc:
            
            for assignment in dagilim_sonuc['assignments']:
                teacher_id = assignment['teacher_id']
                devamsiz_id = assignment['absent_teacher_id']
                hour = assignment['hour']
                class_name = assignment['class']
                
                # Öğretmenin satırını bul
                for row in range(table_atama.rowCount()):
                    if table_atama.item(row, 0).data(Qt.UserRole) == teacher_id:
                        # Ders saatine karşılık gelen hücreyi bul veya oluştur
                        item = table_atama.item(row, hour)
                        if item is None:
                            item = QTableWidgetItem()
                            item.setTextAlignment(Qt.AlignCenter)
                            table_atama.setItem(row, hour, item)
                        
                        # Hücreyi güncelle ve beyaz yap
                        item.setText(class_name)
                        item.setBackground(Qt.white)
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                        item.setForeground(QBrush(self.black_color))  # Yazı rengi siyah
                        item.setBackground(self.yellow_color) #Zemmin rengi sarı
                        
                        # Hücreye ek bilgi ekle (opsiyonel)
                        item.setToolTip(f"Nöbetçi ataması\nDers: {hour}. saat\nSınıf: {class_name}")
                        break
                for satir in range(table_devamsiz.rowCount()):
                    if table_devamsiz.item(satir, 0).data(Qt.UserRole) == devamsiz_id:
                        # Ders saatine karşılık gelen hücreyi bul veya oluştur
                        
                        item = table_devamsiz.item(satir, hour)
                        if item is not None:
                            item.setBackground(self.yellow_color)
                        break

        # Sütun genişliklerini ayarla
        table_atama.resizeColumnsToContents()
        
        # Alternatif satır renklendirme
        table_atama.setAlternatingRowColors(False)  # Kendi renklerimizi kullanıyoruz
        # Hücre değişikliklerini izleme
 
        
    def nobet_sonuclari_tabloda_goster(self, table_widget, atama_verileri, atandi=True):
        """
        Geliştirilmiş nöbet sonuçlarını gösterme fonksiyonu
        
        Args:
            table_widget: Verilerin gösterileceği QTableWidget
            atama_verileri: Gösterilecek atama verileri listesi
            atandi: Atanmış (True) veya atanamamış (False) veriler için flag
        """
        try:
            # Tabloyu temizle ve temel ayarları yap
            table_widget.clear()
            table_widget.setRowCount(0)
            table_widget.setColumnCount(0)
            
            # Sütun başlıklarını belirle
            headers = ["Devamsız Öğretmen", "Saat", "Sınıf", "Nöbetçi Öğretmen"] if atandi else \
                     ["Devamsız Öğretmen", "Saat", "Sınıf", "Sebep"]
            
            table_widget.setColumnCount(len(headers))
            table_widget.setHorizontalHeaderLabels(headers)
            
            # Satır sayısını ayarla
            table_widget.setRowCount(len(atama_verileri))
            
            # Hücre stilleri için renk tanımlamaları
            bg_color = QColor(240, 248, 255)  # Açık mavi arkaplan
            header_color = QColor(70, 130, 180)  # SteelBlue başlık rengi
            text_color = QColor(0, 0, 0)  # Siyah metin
            
            # Başlık stilleri
            header = table_widget.horizontalHeader()
            header.setStyleSheet(f"QHeaderView::section {{ background-color: {header_color.name()}; "
                               f"color: white; font-weight: bold; }}")
            
            # Verileri tabloya ekle
            for row, assignment in enumerate(atama_verileri):
                # Devamsız öğretmen
                absent_teacher_item = QTableWidgetItem(
                    self.data.get_ogretmen_adi(assignment['absent_teacher_id']))
                absent_teacher_item.setData(Qt.UserRole, assignment['absent_teacher_id'])
                
                # Ders saati
                hour_item = QTableWidgetItem(f"{assignment['hour']}. Ders")
                hour_item.setTextAlignment(Qt.AlignCenter)
                
                # Sınıf
                class_item = QTableWidgetItem(assignment['class'])
                class_item.setTextAlignment(Qt.AlignCenter)
                
                # Nöbetçi öğretmen veya sebep
                if atandi:
                    teacher_item = QTableWidgetItem(
                        self.data.get_ogretmen_adi(assignment['teacher_id']))
                    teacher_item.setData(Qt.UserRole, assignment['teacher_id'])
                else:
                    reason_item = QTableWidgetItem(assignment.get('reason', 'Atanamadı'))
                    reason_item.setForeground(QColor(255, 0, 0))  # Kırmızı renk
                
                # Hücreleri tabloya ekle
                table_widget.setItem(row, 0, absent_teacher_item)
                table_widget.setItem(row, 1, hour_item)
                table_widget.setItem(row, 2, class_item)
                
                if atandi:
                    table_widget.setItem(row, 3, teacher_item)
                else:
                    table_widget.setItem(row, 3, reason_item)
                
                # Satır renklendirme
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item:
                        item.setBackground(bg_color)
                        item.setForeground(text_color)
                        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        
                        # Manuel düzenleme için özel ayarlar
                        if atandi and col == 3:  # Nöbetçi öğretmen sütunu
                            item.setFlags(item.flags() | Qt.ItemIsEditable)
                            item.setToolTip("Nöbetçiyi değiştirmek için çift tıklayın")
            
            # Sütun genişliklerini optimize et
            table_widget.resizeColumnsToContents()
            
            # Alternatif satır renklendirme
            table_widget.setAlternatingRowColors(True)
            
            # Sıralama özelliği
            table_widget.setSortingEnabled(True)
            
            # Hücre değişikliklerini dinle (manuel düzenleme için)
            """
            if atandi:
                table_widget.cellChanged.connect(
                    lambda row, col: self.handle_manual_assignment_change(table_widget, row, col))
            """
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tablo oluşturma hatası: {str(e)}")
            print(f"Hata: {traceback.format_exc()}")
    
    def nobet_atama_sayisi_tabloda_goster(self, table_widget, atama_verileri):
        table_widget.clear()
        table_widget.setRowCount(0)
        table_widget.setColumnCount(0)

        # Tablo başlıklarını ayarla
        basliklar = ["Nöbetçi Öğretmen", "Atanan"]
        table_widget.setColumnCount(len(basliklar))
        table_widget.setHorizontalHeaderLabels(basliklar)
        
        # Satır sayısını ayarla
        table_widget.setRowCount(len(atama_verileri)) 
        
        # Verileri tabloya ekle
        for row, (ogretmen_id, count) in enumerate(atama_verileri.items()):
            table_widget.setItem(row, 0, QTableWidgetItem(self.data.get_ogretmen_adi(ogretmen_id)))
            table_widget.setItem(row, 1, QTableWidgetItem(str(count)))
        
        # Sütun genişliklerini ayarla
        table_widget.resizeColumnsToContents()
        table_widget.verticalHeader().setVisible(False)
        #Alternatif: Belirli sütun genişlikleri
        table_widget.setColumnWidth(0, 170)  # Nöbetçi Öğretmen
        table_widget.setColumnWidth(1, 50)   # Atama Sayısı

        # Sıralama özelliği ekle
        table_widget.setSortingEnabled(True)
        
    def read_ogretmen_dersleri_from_table(self, table_widget):
        """
        QTableWidget'ten devamsızlık verilerini okur ve orijinal formata dönüştürür
        
        :param table_widget: Verilerin okunacağı QTableWidget nesnesi
        :return: Orijinal devamsiz_dersleri formatında liste
        """
        _dersleri = []
        
        for row in range(table_widget.rowCount()):
            # Öğretmen ID'sini al (ilk sütunda ve UserRole'de saklanmış olmalı)
            teacher_id_item = table_widget.item(row, 0)
            if not teacher_id_item:
                continue
                
            teacher_id = teacher_id_item.data(Qt.UserRole)
            if not teacher_id:
                continue
                
            # Dersleri topla
            lessons = {}
            for col in range(1, table_widget.columnCount()):
                item = table_widget.item(row, col)
                if item and item.text().strip():  # Boş olmayan hücreleri işle
                    # Sütun başlığından ders saatini al (örn: "1.Ders" -> 1)
                    header = table_widget.horizontalHeaderItem(col).text()
                    try:
                        hour = int(header.split('.')[0])
                        lessons[hour] = item.text()
                    except (ValueError, IndexError, AttributeError):
                        continue
            
            # Sadece dersi olan öğretmenleri ekle
            if lessons:
                _dersleri.append({
                    'ogretmen_id': teacher_id,
                    'dersleri': lessons
                })
        
        return _dersleri
    
    def read_teacher_assignments_from_table(self, table_widget):
    
        #QTableWidget'ten öğretmen atamalarını okuyarak sözlük yapısında döndürür.
 
        teacher_data = {}
        
        for row in range(table_widget.rowCount()):
            # Öğretmen adı ve ID'sini al (ilk sütun)
            teacher_item = table_widget.item(row, 0)
            if not teacher_item:
                continue  # Boş satırı atla
            
            teacher_id = teacher_item.data(Qt.UserRole)  # Arka planda saklanan ID
            
            # Öğretmenin ders saatlerini oku (sütun 1'den 8'e kadar)
            assignments = {}
            for hour in range(1, 9):
                col = hour  # Sütun indeksi (1=1.Ders, 2=2.Ders, ...)
                hour_item = table_widget.item(row, col)
                
                if hour_item:
                    data = hour_item.data(Qt.UserRole)
                    if data is not None:
                        assignments[col]=data['class']
                    
            teacher_data[teacher_id] = {
                #"name": data,
                "assignments": assignments
            }
        
        return teacher_data
    
    def handle_manual_assignment_change(self, table_widget, row, col):
        """
        Manuel olarak değiştirilen nöbetçi atamalarını işler
        
        Args:
            table_widget: Değişiklik yapılan tablo
            row: Değişiklik yapılan satır
            col: Değişiklik yapılan sütun
        """
        if col != 3:  # Sadece nöbetçi öğretmen sütunu için
            return
            
        try:
            # Mevcut değeri al
            new_teacher_name = table_widget.item(row, col).text()
            absent_teacher_id = table_widget.item(row, 0).data(Qt.UserRole)
            hour = int(table_widget.item(row, 1).text().split('.')[0])
            class_name = table_widget.item(row, 2).text()
            
            # Yeni öğretmenin ID'sini bul
            new_teacher_id = None
            for teacher_id, name in self.ogretmen_list.items():
                if name == new_teacher_name:
                    new_teacher_id = teacher_id
                    break
                    
            if not new_teacher_id:
                QMessageBox.warning(self, "Uyarı", "Geçersiz öğretmen adı!")
                return
                
            # Veri yapısını güncelle
            for assignment in self.sonuc['assignments']:
                if (assignment['absent_teacher_id'] == absent_teacher_id and
                    assignment['hour'] == hour and
                    assignment['class'] == class_name):
                    assignment['teacher_id'] = new_teacher_id
                    break
                    
            # Görsel geri bildirim
            table_widget.item(row, col).setBackground(QColor(144, 238, 0))  # Light green
            QMessageBox.information(self, "Başarılı", "Nöbetçi başarıyla güncellendi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Atama güncelleme hatası: {str(e)}")
            print(f"Hata: {traceback.format_exc()}")
            
class DersDoldurmaTablosu(QWidget):
    def __init__(self, table:QWidget, parent=None):
        # Initial data
        self.table = table
        self.data = TeacherManager()
        self.initial_data = None
        self.teacher_db = {ogr['ogretmen_id']: self.data.get_ogretmen_adi(ogr['ogretmen_id']) for ogr in self.initial_data}
        # Working copy of data
        self.current_data = [row.copy() for row in self.initial_data]
        self.modified_cells = set()  # Tracks modified cells (row, col)
        
    def populateTable(self, nobetci_programi=None, atama_dersler=None, ):
        self.initial_data = nobetci_programi
        self.table.setRowCount(len(self.current_data))
        self.teacher_db = {ogr['ogretmen_id']: self.data.get_ogretmen_adi(ogr['ogretmen_id']) for ogr in self.initial_data}
        # Column colors
        column_colors = {
            0: QColor(173, 216, 230),   # Light blue for teachers
            1: QColor(144, 238, 144),   # Light green
            2: QColor(255, 182, 193),   # Light pink
            3: QColor(220, 220, 220),   # Light gray
            4: QColor(255, 218, 185),   # Peach
            5: QColor(221, 160, 221),   # Plum
            6: QColor(152, 251, 152),   # Pale green
            7: QColor(175, 238, 238),  # Pale turquoise
            8: QColor(255, 228, 196)    # Bisque
        }
        
        # Disable cell change signals while populating
        self.table.blockSignals(True)
        
        for row in range(len(self.current_data)):
            teacher_id = self.current_data[row]["ogretmen_id"]
            
            # Teacher name column (0)
            teacher_item = QTableWidgetItem(self.teacher_db.get(teacher_id, f"Bilinmeyen ({teacher_id})"))
            teacher_item.setFlags(teacher_item.flags() & ~Qt.ItemIsEditable)
            teacher_item.setBackground(column_colors[0])
            self.table.setItem(row, 0, teacher_item)
            
            # Lesson columns (1-8)
            for col in range(1, 9):
                cell_value = self.current_data[row]["dersleri"].get(col, "")
                item = QTableWidgetItem(cell_value)
                
                # Set editable only if cell was empty in initial data or has been modified
                is_editable = (col not in self.initial_data[row]["dersleri"]) or ((row, col) in self.modified_cells)
                
                if is_editable:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                # Set background color
                if (row, col) in self.modified_cells:
                    item.setBackground(QColor(255, 255, 0))  # Yellow for modified
                    #item.setForeground(QColor(0, 0, 0))  # Siyah text
                elif not cell_value:
                    item.setBackground(QColor(0, 0, 0))      # Black for empty
                    item.setForeground(QColor(255, 255, 255))  # White text
                else:
                    item.setBackground(column_colors[col])
                
                self.table.setItem(row, col, item)
        
        self.table.blockSignals(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def onCellChanged(self, row, col):
        if col == 0:  # Teacher column is not editable
            return
            
        # Get the new value
        new_value = self.table.item(row, col).text()
        
        # Update our data structure
        if new_value:
            self.current_data[row]["dersleri"][col] = new_value
            self.modified_cells.add((row, col))
        else:
            if col in self.current_data[row]["dersleri"]:
                del self.current_data[row]["dersleri"][col]
            self.modified_cells.discard((row, col))
        
        # Update cell appearance
        item = self.table.item(row, col)
        if new_value:
            if (row, col) in self.modified_cells:
                item.setBackground(QColor(255, 255, 0))  # Yellow
                item.setForeground(QColor(0, 0, 0))  # Siyah text
            else:
                item.setBackground(QColor(0, 0, 0))      # Black
                item.setForeground(QColor(255, 255, 255))  # White text
        else:
            item.setBackground(QColor(0, 0, 0))          # Black
            item.setForeground(QColor(255, 255, 255))    # White text
    
    def addTeacher(self, data):
        
        self.initial_data.append(data.copy())
        self.current_data.append(data.copy())
        
        # Update table
        self.populateTable()
            
    
    def showData(self):
        message = "ORİJİNAL VERİLER:\n"
        
        for entry in self.initial_data:
            teacher_name = self.teacher_db.get(entry["ogretmen_id"], f"Bilinmeyen ({entry['ogretmen_id']})")
            lessons = ", ".join([f"{k}.Ders: {v}" for k,v in entry["dersleri"].items()])
            message += f"{teacher_name} (ID: {entry['ogretmen_id']}) - {lessons}\n"
        
        message += "\nGÜNCEL VERİLER:\n"
        for entry in self.current_data:
            teacher_name = self.teacher_db.get(entry["ogretmen_id"], f"Bilinmeyen ({entry['ogretmen_id']})")
            lessons = ", ".join([f"{k}.Ders: {v}" for k,v in entry["dersleri"].items()])
            message += f"{teacher_name} (ID: {entry['ogretmen_id']}) - {lessons}\n"
        
        QMessageBox.information(self, "Kayıtlı Veriler", message)        