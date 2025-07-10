#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 22 20:49:35 2025

@author: senolirmak
"""


from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, 
                            QTableWidgetItem, QDialog, 
                            QToolBar)

from PyQt5.QtGui import QKeySequence

from PyQt5.QtWidgets import ( QComboBox, QMessageBox,
                             QCompleter,
                             QListWidgetItem, QSlider)

from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush
from PyQt5.uic import loadUi

from nobet.utils.DagitimMotoru import AdvancedNobetDagitim
from nobet.utils.rapor import create_excel_report
from nobet.utils.database_util import TeacherManager
from nobet.utils.tablemanager import TableManager, DataSelectionDialog
from nobet.utils.pencere_fonksiyon import PencereFonksiyon
from nobet.utils.nobetcimodel import TeacherScheduleModel

class NobetSistemi(QMainWindow):
    data_updated = pyqtSignal(list)  # Veri değiştiğinde emit edilecek sinyal
    def __init__(self):
        super(NobetSistemi, self).__init__()
        loadUi('./ui/main_gui.ui', self)
        self.change_stack=None
        
        self.data = TeacherManager()
        self.nobet_dagitim = AdvancedNobetDagitim()
        self.table_manager = TableManager()
        self.pencere_fonksiyon = PencereFonksiyon()
        # UI elementlerini bağla
        self.setWindowTitle("Öğretmen Devamsızlık ve Nöbetçi Dağıtım Sistemi")
        self.setGeometry(100, 100, 1200, 800)
  
        # Veri yapıları
        self.modified_cells = {}
        self.secilen_gun = None
        #self.devamsiz_ogretmen_data = {}
        self.max_shifts = 2
        self.sonuc = None
        
        # Renk tanımlamaları
        self.black_color = QColor(0, 0, 0)       # Siyah
        self.white_color = QColor(255, 255, 255) # Beyaz
        self.green_color = QColor(0, 255, 0)     # Yeşil
        
        # Renk tanımları
        self.yellow_color = QColor(255, 255, 0)    #Sarı
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
        
        # İlk verileri yükle
        self.create_toolbar()
        self.gunleri_yukle()
        self.initUI()

    
    def initUI(self):

        self.lbl_tarih.setText(QDate.currentDate().toString("dddd - dd.MM.yyyy"))
        self.lbl_tarih.setStyleSheet("font-size: 10pt;")
    
        self.devamsizlik_ekle_button.setStyleSheet("font-size: 10pt; padding: 5px;")
        self.devamsizlik_ekle_button.clicked.connect(self.devamsizlik_ekle)

        self.dagit_button.setStyleSheet("font-size: 10pt; padding: 5px; ")
        self.dagit_button.clicked.connect(self.dersleri_dagit)

        self.nobetci_listbox.setStyleSheet("font-size: 10pt;")
        self.nobetci_listbox.setAlternatingRowColors(True)
        self.nobetci_listbox.itemDoubleClicked.connect(self.nobetci_ogretmen_cikar)
        
        self.temizle_button.setStyleSheet("font-size: 10pt; padding: 5px;")
        self.temizle_button.clicked.connect(self.listeyi_temizle)
        
        self.excel_raporu_yaz_btn.clicked.connect(self.rapor_olustur)
        self.data_yaz_btn.clicked.connect(self.sonuclari_kaydet)
        self.denekButton.clicked.connect(self.tablo_veri_al)
        
        self.tbl_sonuc.setSortingEnabled(True) 

        self.gun_combobox.setCurrentIndex(-1)
        self.gun_combobox.currentIndexChanged.connect(self.on_selection_changed)
        bugun_index = datetime.today().weekday()  # Pazartesi=0, Pazar=6
        self.gun_combobox.setCurrentIndex(bugun_index)
        
        self.slide_parametre.setMinimum(1)
        self.slide_parametre.setMaximum(4)
        self.slide_parametre.setValue(2)
        self.slide_parametre.setTickPosition(QSlider.TicksBelow)
        self.slide_parametre.setTickInterval(1)
        
        self.ayar_Slider.setMinimumSize(100, 28)
        self.ayar_Slider.setMaximumSize(100, 16777215)
        self.ayar_Slider.setMinimum(1)
        self.ayar_Slider.setMaximum(4)
        self.ayar_Slider.setValue(2)
        
        # Değer göstergesi
        self.slide_label.setText(f"{self.max_shifts}")
        values = {
            1: "Hız Öncelikli",
            2: "Denge",
            3: "Adalet Öncelikli", 
            4: "Manuel Ayar"
        }
        
        # Sinyal-slot bağlantısı
        self.slide_parametre.valueChanged.connect(self.update_label)
        self.ayar_Slider.valueChanged.connect(self.update_slider_label)
        # Değer göstergesi
        self.ayar_label.setText(f"{values[self.ayar_Slider.value()]}")
        
        self.devamsiz_schedule.setMouseTracking(True)
        self.devamsiz_schedule.cellDoubleClicked.connect(self.delete_teacher_row)
        
        self.ogretmen_combobox.setEditable(True)
        self.ogretmen_combobox.lineEdit().setPlaceholderText("Arama yapın...")
        self.ogretmen_combobox.lineEdit().setStyleSheet("""
            QLineEdit {
                color: #666;
                font-style: italic;
                padding: 5px;
            }
        """)
        self.ogretmen_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.ogretmen_combobox.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.update_search_options()
       
        # Durum çubuğu
        self.statusBar().showMessage("Hazır")
        self.tabWidget_oto.setCurrentIndex(0)

        self.sayilari_guncelle_buton.clicked.connect(self.manuel_nobetsi_sayilari_goster)

        self.table_manager.register_table(self.nobetci_schedule_manuel, "atama")
        self.table_manager.register_table(self.devamsiz_schedule, "devamsiz")

        self.table_manager.cell_data_changed.connect(self.on_table_cell_changed)
        self.nobetci_schedule_manuel.cellClicked.connect(self.on_nobetci_schedule_cell_clicked)
        self.pencere_fonksiyon.setup_devamsiz_ogretmen_table(self.devamsiz_schedule)
    
    def tablo_veri_al(self, tablo):
        data=self.pencere_fonksiyon.read_ogretmen_dersleri_from_table(self.nobetci_schedule_manuel)
        print(f"data={data}")
        

    def update_label(self, value):
        self.slide_label.setText(f"{value}")
        self.nobet_dagitim.max_shifts = value
        
    def update_slider_label(self):
        """Update slider label text based on value"""
        values = {
            1: "Hız Öncelikli",
            2: "Denge",
            3: "Adalet Öncelikli", 
            4: "Manuel Ayar"
        }
        self.ayar_label.setText(f"{values[self.ayar_Slider.value()]}")
        self.nobet_dagitim.penalty_weights = self.pencere_fonksiyon.get_optimization_weights(self.ayar_Slider.value())
                  
    def manuel_nobetsi_sayilari_goster(self):
        stats = self.pencere_fonksiyon.nobet_atamalarini_say(self.nobetci_schedule_manuel)
        self.pencere_fonksiyon.nobet_atama_sayisi_tabloda_goster(self.table_nobetsayisi, stats)
        
    def on_nobetci_schedule_cell_clicked(self, row, column):
        """Nöbetçi tablosunda hücre tıklandığında çalışan fonksiyon"""
        
        # Öğretmen adı sütunu (0. sütun) değiştirilemez
        if column == 0:
            QMessageBox.information(self, "Bilgi", "Öğretmen sütunu değiştirilemez!")
            return
        
        item = self.nobetci_schedule_manuel.item(row, column)
        
        # Kilitli (gri) hücreler değiştirilemez
        if item and item.background().color() == self.locked_color:
            QMessageBox.information(self, "Bilgi", "Bu hücre değiştirilemez!")
            return
        
        # Devamsız tablosundaki ilgili sütundaki verileri topla
        column_data = []
        items_info = []
        
        for r in range(self.devamsiz_schedule.rowCount()):
            dev_item = self.devamsiz_schedule.item(r, column)
            if dev_item and dev_item.text() and dev_item.background().color() != self.yellow_color:
                column_data.append(dev_item.text())
                items_info.append((r, dev_item))
        
        # Eğer seçilebilecek veri yoksa
        if not column_data:
            current_item = self.nobetci_schedule_manuel.item(row, column)
            current_value = current_item.text() if current_item else ""
            
            # Eğer hücrede değer varsa silmeyi onayla
            if current_value:
                reply = QMessageBox.question(
                    self, 'Onay',
                    f"'{current_value}' değerini silmek istediğinizden emin misiniz?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Nöbetçi tablosundan hücreyi temizle
                    current_item.setText("")
                    current_item.setBackground(self.black_color)
                    
                    # Devamsız tablosunda eski değeri orijinal rengine döndür
                    for r in range(self.devamsiz_schedule.rowCount()):
                        dev_item = self.devamsiz_schedule.item(r, column)
                        if dev_item and dev_item.text() == current_value:
                            dev_item.setBackground(self.initial_colors[column]) #r % len(self.initial_colors)])
                            break
                    
            else:
                QMessageBox.information(self, "Bilgi", "Bu hücre zaten boş!")
            return
        
        # Seçim dialogunu göster
        dialog = DataSelectionDialog(column_data, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_value = dialog.selected_data()
            
            # Önceki değeri al
            previous_item = self.nobetci_schedule_manuel.item(row, column)
            previous_value = previous_item.text() if previous_item else ""
            
            # Yeni değeri ayarla
            new_item = QTableWidgetItem(selected_value)
            new_item.setBackground(self.yellow_color)
            new_item.setForeground(QBrush(self.black_color))
            new_item.setData(Qt.UserRole, {'class': selected_value, 'hour': column})
            self.nobetci_schedule_manuel.setItem(row, column, new_item)
            
            # Devamsız tablosunda seçilen değeri sarı yap
            for r, dev_item in items_info:
                if dev_item.text() == selected_value:
                    dev_item.setBackground(self.yellow_color)
                    dev_item.setForeground(QBrush(self.black_color))
                    break
            
            # Önceki değer varsa ve farklıysa, eski rengine döndür
            if previous_value and previous_value != selected_value:
                for r in range(self.devamsiz_schedule.rowCount()):
                    dev_item = self.devamsiz_schedule.item(r, column)
                    if dev_item and dev_item.text() == previous_value:
                        dev_item.setBackground(self.initial_colors[r % len(self.initial_colors)])
                        break
    
    def on_devamsiz_table_cell_changed(self,change):
        print(f"\nTablo: {change.table_id.upper()}, Hücre: [{change.row}, {change.col}]")
        print(f"Eski Değer: {change.old_value}")
        print(f"Yeni Değer: {change.new_value}")
        
        # Değişikliği kaydet
        self.table_manager.record_change(change)
        
        # Tabloya özel validasyonlar
        if change.table_id == "atama":
            table = self.nobetci_schedule_manuel
        if change.table_id == "devamsiz":
            table = self.devamsiz_schedule

        item = table.item(change.row, change.col)
        item.setText(change.old_value)
        
    
    def on_table_cell_changed(self, change): #row, column, table_id
        """Hücre değişikliği olduğunda çalışan fonksiyon"""
        
        # Değişikliği kaydet
        self.table_manager.record_change(change)
        
        # Hangi tablo olduğunu belirle
        if change.table_id == "atama":
            table = self.nobetci_schedule_manuel
        elif change.table_id == "devamsiz":
            table = self.devamsiz_schedule
        else:
            return
        
        item = table.item(change.row, change.col)
        if not item:
            return
        
        # Eğer hücre boşsa siyah yap
        if not item.text().strip():
            item.setBackground(self.black_color)
            item.setForeground(QBrush(self.white_color))
            
            # Eğer bu bir atama tablosuysa ve ders saati sütunundaysa
            if change.table_id == "atama" and change.col > 0:
                # Devamsız tablosunda bu değeri arayıp rengini düzelt
                for r in range(self.devamsiz_schedule.rowCount()):
                    dev_item = self.devamsiz_schedule.item(r, change.col)
                    if dev_item and dev_item.text() == item.text():
                        dev_item.setBackground(self.initial_colors[r % len(self.initial_colors)])
                        break
        else:
            # Hücre doluysa ve sarı değilse (yeni atama değilse) gri yap
            if item.background().color() != self.yellow_color:
                item.setBackground(self.locked_color)
                item.setForeground(QBrush(self.black_color))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)     
    
    def onCellChanged(self, row, col):
        if col == 0:  # Teacher column is not editable
            return
            
        # Get the new value
        new_value = self.table.item(row, col).text()
        
        # Update our data structure
        if new_value:
            self.modified_cells.add((row, col))
        else:
            self.modified_cells.discard((row, col))
        
    
    def create_toolbar(self):
        toolbar = QToolBar("Araç Çubuğu")
        self.addToolBar(toolbar)
        
        undo_action = toolbar.addAction("Geri Al (Ctrl+Z)")
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo_last_change)
    
    def undo_last_change(self):
        if self.table_manager.undo_change():
            print("Son değişiklik geri alındı")
        else:
            print("Geri alınacak değişiklik yok")
            
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++
    def devamsizlik_ekle(self):
        if self.nobetci_listbox.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Önce Nöbetçi Öğretmen yükleyin!")
            return
        #devamsiz_ogretmenler = self.get_devamsiz_dersleri()
        #devamsiz_ogretmenler = []
        data = {}
        ogretmen_id = None
        index = self.ogretmen_combobox.currentIndex()
        if index >= 0:
            item = self.model.item(index)
            if item:
                item = self.model.item(index)
                ogretmen_id = item.data(Qt.UserRole)
                
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir öğretmen seçin!")
            return

        data['ogretmen_id'] = ogretmen_id
        ders_programi = self.data.get_ogretmen_programi(ogretmen_id, self.secilen_gun, ayrinti=False)
        sorted_lessons = dict(sorted(ders_programi['dersleri'].items()))
        data['dersleri'] = sorted_lessons
        name = self.data.get_ogretmen_adi(ogretmen_id)
        if ogretmen_id in self.get_nobetci_ogretmenler_nobetci_listbox():
            name = self.data.get_ogretmen_adi(ogretmen_id)
            cevap = QMessageBox.question(
                self,
                "Onay",
                f"{name} nöbetçi öğretmen. Devamsız olarak işaretlemek istediğinize emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if cevap == QMessageBox.StandardButton.Yes:
                # Nöbetçi bulup silme
                self.delete_by_id_nobetci_listbox(ogretmen_id)
                self.statusBar().showMessage(f"{name} nöbetçi listesinden çıkarıldı ve devamsız olarak işaretlendi", 3000)

        self.pencere_fonksiyon.add_devamsiz_ogretmen_scheduler(self.devamsiz_schedule, data)
        self.statusBar().showMessage(f"Toplam {len(data)} öğretmen eklendi", 3000)
    
    def update_search_options(self):
        self.ogretmen_list = self.data.get_gunun_ogretmenleri(self.secilen_gun)
        self.model = QStandardItemModel()
        
        # Öğretmenleri modele ekle
        for ogretmen_id, ad in self.ogretmen_list.items():
            item = QStandardItem(ad)
            item.setData(ogretmen_id, role=Qt.UserRole)
            self.model.appendRow(item)
            
        self.ogretmen_combobox.setModel(self.model)
        self.ogretmen_combobox.setCurrentIndex(-1)
        self.ogretmen_combobox.setCurrentText("")
        
    def populate_nobetci_listesi(self,):
        """QListWidget'i Günün nöbetçileriyle doldurur"""
        self.nobetci_listbox.clear()  # Önceki verileri temizle
        results = self.data.get_duty_teachers(self.secilen_gun)
        

        for nobet_gorevi, ogretmen in results:
            # Yeni bir QListWidgetItem oluştur
            item = QListWidgetItem(f"{ogretmen.adi_soyadi} - ({nobet_gorevi.nobet_yeri})")
            # Öğretmen ID'sini sakla (Qt.UserRole olarak)
            item.setData(Qt.UserRole, nobet_gorevi.nobetci_ogretmen_id)
            # Listeye ekle
            self.nobetci_listbox.addItem(item)
                
    def get_nobetci_ogretmenler_nobetci_listbox(self):
        """QListWidget'taki verilerden dönüşüm listesi üretir"""
        nobetci_ogretmenler_id = []
    
        for i in range(self.nobetci_listbox.count()):
            item = self.nobetci_listbox.item(i)
            nobetci_ogretmen = item.data(Qt.UserRole)
            nobetci_ogretmenler_id.append(nobetci_ogretmen)
    
        return nobetci_ogretmenler_id
    
    def delete_by_id_nobetci_listbox(self, ogretmen_id):
        """Öğretmen ID'sine göre satır silme"""
        for i in range(self.nobetci_listbox.count()):
            item = self.nobetci_listbox.item(i)
            if item.data(Qt.UserRole) == ogretmen_id:
                self.nobetci_listbox.takeItem(i)
                return
                 
    def verihazirla(self):
        """Nöbetçi listesini veritabanından yükler"""
        try:
            self.nobetci_listbox.clear()
            self.secilen_gun = self.secilen_gunu_al()
            self.populate_nobetci_listesi()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Nöbet listesi yükleme hatası: {str(e)}")
  
    def yeni_devamsizlik_ekle(self):
        pass
    
    # Ana uygulamada kullanım örneği
    def devamsizlik_ekle_ve_dagit(self):
        pass
    
    def gunleri_yukle(self):
        """Günleri combobox'a yükler"""
        gunler = {
                "Pazartesi": "Monday",
                "Salı": "Tuesday",
                "Çarşamba": "Wednesday",
                "Perşembe": "Thursday",
                "Cuma": "Friday"
            }

        for turkce, ingilizce in gunler.items():
            self.gun_combobox.addItem(turkce, ingilizce)
            
    def secilen_gunu_al(self):
        """Seçilen günü İngilizce ismiyle döndürür"""
        return self.gun_combobox.currentData()
    
    def on_selection_changed(self, index):
        self.verihazirla()
        self.update_search_options()

    def nobetci_ogretmen_cikar(self, item):
        row = self.nobetci_listbox.row(item)
        ogretmen_id = item.data(Qt.UserRole)
        name = self.data.get_ogretmen_adi(ogretmen_id)
        self.nobetci_listbox.takeItem(row)
        self.statusBar().showMessage(f"Nöbetçi {name} listeden çıkarıldı", 3000)
    
    def get_nobetci_dersleri(self):
        """Nöbetçi Öğretmenleri ve derslerini getirir"""
        nobetci_ogretmenler = []
        tarih = self.secilen_gun
        for i in range(self.nobetci_listbox.count()):
            nobetci_id = self.nobetci_listbox.item(i).data(Qt.UserRole)
            ders_dict = self.data.get_ogretmen_programi(nobetci_id,tarih, ayrinti=False)
            nobetci_ogretmenler.append(ders_dict)
        return nobetci_ogretmenler    

    def dersleri_dagit(self):
        """Dersleri nöbetçilere dağıt"""

        try:
            # Mevcut nöbetçileri ve Devamsız öğetmenleri tablolardan al
            nobetci_dersleri = self.get_nobetci_dersleri()
            devamsiz_dersleri = self.pencere_fonksiyon.read_ogretmen_dersleri_from_table(self.devamsiz_schedule)
            
            self.sonuc = self.nobet_dagitim.optimize(nobetci_dersleri, devamsiz_dersleri)
            
            self.pencere_fonksiyon.nobet_sonuclari_tabloda_goster(self.tbl_sonuc,
                                                                  self.sonuc['assignments'])
            
            self.pencere_fonksiyon.nobet_sonuclari_tabloda_goster(self.dagitilamayan_table,
                                                                  self.sonuc['unassigned'], False)
            
            self.pencere_fonksiyon.nobet_atama_sayisi_tabloda_goster(self.table_nobetsayisi,
                                                                     self.sonuc['teacher_counts'])
            
            ogretmen_data_orjinal = nobetci_dersleri.copy()
        
            self.pencere_fonksiyon.atama_sonuc_tablosu_yukle(self.nobetci_schedule_manuel,
                                                             self.devamsiz_schedule,
                                                             ogretmen_data_orjinal, self.sonuc)
            

            QMessageBox.information(self, 'Başarılı', 'Nöbet dağıtımı tamamlandı!')
 
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Dağıtım hatası: {str(e)}')
    
       
    def closeEvent(self, event):
        """Pencere kapatıldığında bağlantıyı kapat"""
        #self.db.close()
        event.accept()
 
    def delete_teacher_row(self, row, col):
        # Sadece öğretmen adı sütununda çift tıklamada silme yap
        if col != 0:
            return
            
        teacher_item = self.devamsiz_schedule.item(row, 0)
        if not teacher_item:
            return
            
        #teacher_id = teacher_item.data(Qt.UserRole)
        teacher_name = teacher_item.text()
        
        # Onay dialogu
        reply = QMessageBox.question(
            self, 'Devamsız Öğretmen Silme', 
            f"{teacher_name} öğretmenini silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Öğretmeni veri yapısından sil
            #if teacher_id in self.devamsiz_ogretmen_data:
            #    del self.devamsiz_ogretmen_data[teacher_id]
                
            self.devamsiz_schedule.removeRow(row)
            self.statusBar().showMessage(f"Devamsız {teacher_name} listeden çıkarıldı", 3000)
      
    def listeyi_temizle(self):
        if self.devamsiz_schedule.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "Liste zaten boş!")
            return
            
        cevap = QMessageBox.question(self, "Onay", "Tüm devamsız öğretmen listesini temizlemek istediğinize emin misiniz?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if cevap == QMessageBox.StandardButton.Yes:
            #self.devamsiz_ogretmen_data = {}
            self.devamsiz_schedule.clear()
            self.devamsiz_schedule.setRowCount(0)
            self.devamsiz_schedule.setColumnCount(0)
            
            self.nobetci_schedule_manuel.clear()
            self.nobetci_schedule_manuel.setRowCount(0)
            self.nobetci_schedule_manuel.setColumnCount(0)
            
            self.tbl_sonuc.clear()
            self.tbl_sonuc.setRowCount(0)
            self.tbl_sonuc.setColumnCount(0)
            
            self.dagitilamayan_table.clear()
            self.dagitilamayan_table.setRowCount(0)
            self.dagitilamayan_table.setColumnCount(0)
            
            self.table_nobetsayisi.clear()
            self.table_nobetsayisi.setRowCount(0)
            self.table_nobetsayisi.setColumnCount(0)
            
            self.pencere_fonksiyon.setup_devamsiz_ogretmen_table(self.devamsiz_schedule)
            self.statusBar().showMessage("Liste temizlendi", 3000)

    def rapor_olustur(self):
        create_excel_report(self.sonuc)
    
    def sonuclari_kaydet(self):
        sonuc = self.sonuc
        if sonuc['assignments']:
            kayit_sonucu = self.data.data_save_NobetGecmisi(sonuc)
            if kayit_sonucu["status"] == "success":
                print(kayit_sonucu["message"])
            else:
                print(f"HATA: {kayit_sonucu['mesaj']}")
                
        if sonuc['unassigned']:
            kayit_sonucu = self.data.data_sava_NobetAtanamayan(sonuc)
            if kayit_sonucu["status"] == "success":
                print(kayit_sonucu["message"])
            else:
                print(f"HATA: {kayit_sonucu['mesaj']}")
    
  