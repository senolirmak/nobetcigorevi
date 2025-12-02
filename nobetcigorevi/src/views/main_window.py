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

from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush
from PyQt5.uic import loadUi

from utils.DagitimMotoru import AdvancedNobetDagitim
from utils.nobetraporu import ExcelRaporOlusturucu
from utils.database_util import TeacherManager
from utils.tablemanager import TableManager, DataSelectionDialog
from utils.pencere_fonksiyon import PencereFonksiyon
from utils.veri_aktarimi_yonetici import VeriAktarimiYonetici
from db.models import (NobetGecmisi, NobetIstatistik,
                                     NobetGorevi, NobetDegisimKaydi,
                                     NobetOgretmen)

from db.database import SessionLocal
from sqlalchemy import select, and_, func
from PyQt5.QtCore import QTimer
import os
import shutil

class NobetSistemi(QMainWindow):
    data_updated = pyqtSignal(list)  # Veri değiştiğinde emit edilecek sinyal
    def __init__(self):
        super(NobetSistemi, self).__init__()
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'main_gui.ui')
        ui_path = os.path.abspath(ui_path)
        loadUi(ui_path, self)

        self.change_stack=None
        
        self.data = TeacherManager()
        self.nobet_dagitim = AdvancedNobetDagitim()
        self.table_manager = TableManager()
        self.pencere_fonksiyon = PencereFonksiyon()
        self.nbrapor=ExcelRaporOlusturucu()
        # UI elementlerini bağla
        self.setWindowTitle("Öğretmen Devamsızlık ve Nöbetçi Dağıtım Sistemi")
        self.setGeometry(100, 100, 1200, 800)
  
        # Veri yapıları
        self.modified_cells = {}
        self.secilen_gun = None

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

        self.gun_combobox.setCurrentIndex(-1)
        self.gun_combobox.currentIndexChanged.connect(self.on_selection_changed)
        bugun_index = datetime.today().weekday()  # Pazartesi=0, Pazar=6
        self.gun_combobox.setCurrentIndex(bugun_index)
        
        self.parametre_surgu.setMinimum(1)
        self.parametre_surgu.setMaximum(4)
        self.parametre_surgu.setValue(2)
        self.parametre_surgu.setTickPosition(QSlider.TicksBelow)
        self.parametre_surgu.setTickInterval(1)
        
        self.ayar_surgu.setMinimumSize(100, 28)
        self.ayar_surgu.setMaximumSize(100, 16777215)
        self.ayar_surgu.setMinimum(1)
        self.ayar_surgu.setMaximum(4)
        self.ayar_surgu.setValue(2)
        
        # Değer göstergesi
        self.slide_label.setText(f"{self.max_shifts}")
        values = {
            1: "Hız Öncelikli",
            2: "Denge",
            3: "Adalet Öncelikli", 
            4: "Manuel Ayar"
        }
        
        # Sinyal-slot bağlantısı
        self.parametre_surgu.valueChanged.connect(self.update_label)
        self.ayar_surgu.valueChanged.connect(self.update_slider_label)
        # Değer göstergesi
        self.ayar_label.setText(f"{values[self.ayar_surgu.value()]}")
        
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
        QTimer.singleShot(3000, self.haftalik_nobet_yeri_degistir)
        self.ogretmen_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.ogretmen_combobox.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.update_search_options()
        self.update_uygulama_tarihi_label()
       
        # Durum çubuğu
        self.statusBar().showMessage("Hazır")
        self.tabWidget_oto.setCurrentIndex(0)

        self.sayilari_guncelle_buton.clicked.connect(self.manuel_nobetsi_sayilari_goster)
        self.list_dagilimler.itemDoubleClicked.connect(self.on_list_item_double_clicked)

        self.table_manager.register_table(self.nobetci_schedule_manuel, "atama")
        self.table_manager.register_table(self.devamsiz_schedule, "devamsiz")

        self.table_manager.cell_data_changed.connect(self.on_table_cell_changed)
        self.nobetci_schedule_manuel.cellClicked.connect(self.on_nobetci_schedule_cell_clicked)
        self.pencere_fonksiyon.setup_devamsiz_ogretmen_table(self.devamsiz_schedule)
        
        self.btn_browse_ders_programi.clicked.connect(self.select_ders_programi)
        self.btn_browse_nobet_listesi.clicked.connect(self.select_nobet_listesi)
        self.btn_veri_yukle.clicked.connect(self.veri_yukle)
        
        # 🟢 QDateEdit ilk açıldığında bugünün tarihini göstersin
        self.date_uygulama_tarihi.setDate(QDate.currentDate())
        self.date_uygulama_tarihi.setDisplayFormat("dd.MM.yyyy")
        self.date_uygulama_tarihi.setCalendarPopup(True)
        
        #Nöbet Listesi Raporu
        self.haftalik_nobet_rapor.clicked.connect(self.rapor_olustur_haftalik_nobet)
    
    def verihazirla(self):
        """Nöbetçi listesini veritabanından yükler"""
        try:
            self.nobetci_listbox.clear()
            self.secilen_gun = self.secilen_gunu_al()
            self.populate_nobetci_listesi()
            self.list_dagilim_tarihleri()
            # 🟦 GUI tarihinden değil, veritabanındaki son kayıttan al
            self.update_uygulama_tarihi_label(from_gui=False)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Nöbet listesi yükleme hatası: {str(e)}")
        
    def get_gui_uygulama_tarihi(self):
        """
        GUI'deki QDateEdit'ten uygulama tarihini datetime olarak döndürür.
        """
        qdate = self.date_uygulama_tarihi.date()
        return datetime(qdate.year(), qdate.month(), qdate.day())

    def update_uygulama_tarihi_label(self, tarih=None, from_gui=False):
        """
        Uygulama tarihini belirler ve label'a yazar.
        - from_gui=True ise QDateEdit'ten alır.
        - from_gui=False ise veritabanından çeker.
        """
        if from_gui:
            # GUI’den alınacak (örneğin ilk veri yükleme sırasında)
            tarih = self.get_gui_uygulama_tarihi()
            self.uygulama_tarihi = tarih
        else:
            # Veritabanından çekilecek
            tarih = tarih or self.data.get_son_uygulama_tarihi()
            if tarih is None:
                self.label_uygulama_tarihi.setText("Uygulama Tarihi: Veri bulunamadı")
                self.label_uygulama_tarihi.setStyleSheet("color: red; font-weight: bold;")
                return
            self.uygulama_tarihi = tarih
    
        tarih_str = self.uygulama_tarihi.strftime("%d.%m.%Y %A")
        self.label_uygulama_tarihi.setText(f"Uygulama Tarihi: {tarih_str}")
        self.label_uygulama_tarihi.setStyleSheet("font-weight: bold; color: #003366; font-size: 10pt;")

    def on_list_item_double_clicked(self, item):
        dt = item.data(Qt.UserRole)
        self.load_dagilim_from_database(dt)

    def select_ders_programi(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Ders Programı Dosyasını Seç", "", "Excel Files (*.xls *.xlsx)")
        if file_path:
            self.txt_ders_programi.setText(file_path)
    
    def select_nobet_listesi(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Nöbet Listesi Dosyasını Seç", "", "Excel Files (*.xls *.xlsx)")
        if file_path:
            self.txt_nobet_listesi.setText(file_path)
    
    def veri_yukle(self):
        from pathlib import Path
        HOME_DATA = Path.home() / "NobetciVeri"
        VERI_DIR = HOME_DATA / "veri"
        HAZIRLIK_DIR = HOME_DATA / "hazirlik"
    
        VERI_DIR.mkdir(parents=True, exist_ok=True)
        HAZIRLIK_DIR.mkdir(parents=True, exist_ok=True)
    
        # GUI’den gelen yollar
        ders_path = self.txt_ders_programi.text().strip()
        nobet_path = self.txt_nobet_listesi.text().strip()
    
        tarih = self.date_uygulama_tarihi.date().toString("yyyy/MM/dd")
    
        if not ders_path or not nobet_path:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen her iki dosya yolunu da seçin!")
            return
    
        try:
            # Dosyaları GUI’den gelen path’ten alıp Home dizinine kopyalayalım
            ders_file = Path(ders_path)
            if ders_file.exists():
                hedef_ders = VERI_DIR / ders_file.name
                if ders_file != hedef_ders:
                    shutil.copy2(ders_file, hedef_ders)
            else:
                raise FileNotFoundError(f"Ders programı bulunamadı: {ders_path}")
    
            nobet_file = Path(nobet_path)
            if nobet_file.exists():
                hedef_nobet = VERI_DIR / nobet_file.name
                if nobet_file != hedef_nobet:
                    shutil.copy2(nobet_file, hedef_nobet)
            else:
                raise FileNotFoundError(f"Nöbet listesi bulunamadı: {nobet_path}")
    
            # personel.xlsx da aynı folder’da olmalı
            personel_excel = VERI_DIR / "personel.xlsx"
            if not personel_excel.exists():
                raise FileNotFoundError(f"Personel dosyası bulunamadı: {personel_excel}")
    
            from utils.dersprogrami_isleyici import DersProgramiIsleyici
            self.update_uygulama_tarihi_label(from_gui=True)
            
            sinif_bilgileri = {
                9: ['A','B','C','D','E','F'],
                10:['A','B','C','D','E','F','G','H','İ'],
                11:['A','B','C','D','E','F','G','H'],
                12:['A','B','C','D','E','F','G']
            }
    
            # 🟩 Tüm yollar artık HOME/NobetciVeri/veri altından okunuyor
            isleyici = DersProgramiIsleyici(
                file_path=hedef_ders.name,
                personel_path="personel.xlsx",
                file_path_nobet=hedef_nobet.name,
                uygulama_tarihi=tarih,
                sinif_bilgileri=sinif_bilgileri
            )
    
            isleyici.calistir()   # → @HOME/NobetciVeri/hazirlik içine yazar
    
            # Veri aktarımı için temel path artık Home dizini olmalı
            
            aktarim = VeriAktarimiYonetici(base_path=str(HOME_DATA))
            logs = aktarim.run()
    
            QMessageBox.information(self, "Başarılı", "\n".join(logs))
            self.lbl_yukleme_durum.setText("✅ Veri başarıyla işlendi ve kaydedildi.")

        except Exception as e:
            self.lbl_yukleme_durum.setText(f"❌ Hata: {e}")
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata oluştu:\n{e}")


    
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
        self.ayar_label.setText(f"{values[self.ayar_surgu.value()]}")
        self.nobet_dagitim.penalty_weights = self.pencere_fonksiyon.get_optimization_weights(self.ayar_surgu.value())
                  
    def manuel_nobetsi_sayilari_goster(self):
        stats = self.pencere_fonksiyon.nobet_atamalarini_say(self.nobetci_schedule_manuel)
        self.pencere_fonksiyon.nobet_atama_sayisi_tabloda_goster(self.table_nobetsayisi, stats)
    
    def on_nobetci_schedule_cell_clicked(self, row, column):
        """Dağıtımdan sonra nöbetçi tablosunda manuel müdahale fonksiyonu"""
        if column == 0:
            QMessageBox.information(self, "Bilgi", "Öğretmen sütunu değiştirilemez!")
            return
    
        # 🔹 Öğretmen kimliği al
        ogretmen_item = self.nobetci_schedule_manuel.item(row, 0)
        
        if not ogretmen_item:
            return
        ogretmen_adi = ogretmen_item.text().split(" - ")[0].strip()
        ogretmen_id = self.data.get_ogretmen_id(ogretmen_adi)
        
        """
        # 🔸 Pasif nöbetçi kontrolü
        if hasattr(self, "pasif_nobetciler") and ogretmen_id in self.pasif_nobetciler:
            QMessageBox.warning(self, "Uyarı", f"{ogretmen_adi} pasif durumda, ders atanamaz!")
            return
        """
        
        # 🔸 Kilitli hücre kontrolü
        item = self.nobetci_schedule_manuel.item(row, column)
        if item and item.background().color() == self.locked_color:
            QMessageBox.information(self, "Bilgi", "Bu hücre değiştirilemez!")
            return
    
        # 🔸 Devamsızlardan uygun dersleri topla
        column_data = []
        items_info = []
        for r in range(self.devamsiz_schedule.rowCount()):
            dev_item = self.devamsiz_schedule.item(r, column)
            if dev_item and dev_item.text():
                if dev_item.background().color() == self.yellow_color:
                    continue
                column_data.append(dev_item.text())
                items_info.append((r, dev_item))
    
        # 🔸 Eğer seçim yoksa, silme işlemi teklif et
        if not column_data:
            current_item = self.nobetci_schedule_manuel.item(row, column)
            current_value = current_item.text() if current_item else ""
    
            if current_value:
                reply = QMessageBox.question(
                    self, "Onay", f"'{current_value}' değerini silmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    current_item.setText("")
                    current_item.setBackground(self.black_color)
                    # 🔸 self.sonuc'tan kaydı kaldır
                    self.remove_assignment_from_sonuc(ogretmen_id, column)
                    # Devamsız tablosunda rengi geri al
                    for r in range(self.devamsiz_schedule.rowCount()):
                        dev_item = self.devamsiz_schedule.item(r, column)
                        if dev_item and dev_item.text() == current_value:
                            dev_item.setBackground(self.initial_colors[column])
                            break
            return
    
        # 🔸 Devamsız ders seçimi
        dialog = DataSelectionDialog(column_data, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_value = dialog.selected_data()
            previous_item = self.nobetci_schedule_manuel.item(row, column)
            previous_value = previous_item.text() if previous_item else ""
    
            # 🔸 Görsel tabloyu güncelle
            new_item = QTableWidgetItem(selected_value)
            new_item.setBackground(self.yellow_color)
            new_item.setForeground(QBrush(self.black_color))
            new_item.setData(Qt.UserRole, {'class': selected_value, 'hour': column})
            self.nobetci_schedule_manuel.setItem(row, column, new_item)
    
            # 🔸 Devamsız tablosunda seçilen hücreyi sarı yap
            for r, dev_item in items_info:
                if dev_item.text() == selected_value:
                    dev_item.setBackground(self.yellow_color)
                    dev_item.setForeground(QBrush(self.black_color))
                    break
    
            # 🔸 self.sonuc'a işle
            self.update_sonuc_after_manual_change(
                ogretmen_id=ogretmen_id,
                hour=column,
                class_name=selected_value
            )
    
            # 🔸 Eğer eski değer farklıysa, eski atamayı kaldır
            if previous_value and previous_value != selected_value:
                self.remove_assignment_from_sonuc(ogretmen_id, column)
                
    # yardımcı Fonksiyonlar
    def update_sonuc_after_manual_change(self, ogretmen_id, hour, class_name):
        """Manuel atama yapıldığında self.sonuc yapısını günceller."""
        if not self.sonuc:
            self.sonuc = {"assignments": [], "unassigned": [], "teacher_counts": {}, "teacher_schedule": {}, "penalty": 0}
    
        # 🔹 Devamsız öğretmeni tespit et (sınıf ve saat üzerinden)
        absent_teacher_id = None
        for r in range(self.devamsiz_schedule.rowCount()):
            dev_item = self.devamsiz_schedule.item(r, hour)
            if dev_item and dev_item.text() == class_name:
                teacher_item = self.devamsiz_schedule.item(r, 0)
                if teacher_item:
                    absent_teacher_id = teacher_item.data(Qt.UserRole)
                    break
    
        # 🔹 Eğer öğretmen zaten bu saatte görevliyse, güncelle
        existing = next((a for a in self.sonuc["assignments"]
                         if a["teacher_id"] == ogretmen_id and a["hour"] == hour), None)
    
        if existing:
            existing["class"] = class_name
            existing["absent_teacher_id"] = absent_teacher_id
        else:
            self.sonuc["assignments"].append({
                "hour": hour,
                "class": class_name,
                "teacher_id": ogretmen_id,
                "absent_teacher_id": absent_teacher_id
            })
    
        # 🔹 Sayaç ve saat listesi güncelle
        self.sonuc["teacher_counts"][ogretmen_id] = self.sonuc["teacher_counts"].get(ogretmen_id, 0) + 1
        self.sonuc["teacher_schedule"].setdefault(ogretmen_id, []).append(hour)

        
    def remove_assignment_from_sonuc(self, ogretmen_id, hour):
        """Bir hücre boşaltıldığında self.sonuc listesinden kaydı kaldırır"""
        if not self.sonuc:
            return
    
        # 🔹 assignments listesinden çıkar
        self.sonuc["assignments"] = [a for a in self.sonuc["assignments"]
                                     if not (a["teacher_id"] == ogretmen_id and a["hour"] == hour)]
    
        # 🔹 sayaç azalt
        if ogretmen_id in self.sonuc["teacher_counts"]:
            self.sonuc["teacher_counts"][ogretmen_id] = max(0, self.sonuc["teacher_counts"][ogretmen_id] - 1)

    
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
            item.setData(Qt.UserRole, nobet_gorevi.ogretmen_id)#item.setData(Qt.UserRole, nobet_gorevi.nobetci_ogretmen_id)
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
        self.list_dagilim_tarihleri()

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
            self.hazirla_istatistik_verisi()
            nobetci_dersleri = self.get_nobetci_dersleri()
            devamsiz_dersleri = self.pencere_fonksiyon.read_ogretmen_dersleri_from_table(self.devamsiz_schedule)
            
            self.sonuc = self.nobet_dagitim.optimize(nobetci_dersleri, devamsiz_dersleri)
                 
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
            self.devamsiz_schedule.clear()
            self.devamsiz_schedule.setRowCount(0)
            self.devamsiz_schedule.setColumnCount(0)
            
            self.nobetci_schedule_manuel.clear()
            self.nobetci_schedule_manuel.setRowCount(0)
            self.nobetci_schedule_manuel.setColumnCount(0)
     
            self.dagitilamayan_table.clear()
            self.dagitilamayan_table.setRowCount(0)
            self.dagitilamayan_table.setColumnCount(0)
            
            self.table_nobetsayisi.clear()
            self.table_nobetsayisi.setRowCount(0)
            self.table_nobetsayisi.setColumnCount(0)
            
            #self.pencere_fonksiyon.setup_devamsiz_ogretmen_table(self.devamsiz_schedule)
            self.statusBar().showMessage("Liste temizlendi", 3000)

    def rapor_olustur(self):

        try:
            self.nbrapor.create_excel_report(self.sonuc)
            QMessageBox.information(self, "Rapor", "Excel raporu güncel tablo verileriyle oluşturuldu.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor oluşturulamadı:\n{str(e)}")
        
    def rapor_olustur_haftalik_nobet(self):

        try:
            
            self.nbrapor.raporla_nobet_gorevi_excel()
            QMessageBox.information(self, "Rapor", "Nöbet Listesi güncel tablo verileriyle oluşturuldu.")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"Rapor oluşturulamadı:\n{str(e)}"
            )
         
    def hazirla_istatistik_verisi(self):
        """
        Ana penceredeki nöbetçi öğretmenlerin (nobetci_listbox içindekilerin)
        NobetIstatistik verilerini çekip AdvancedNobetDagitim yapısına aktarır.
        """
        try:

            from db.database import SessionLocal
    
            # 🔹 1️⃣ Liste kutusundaki nöbetçi öğretmen ID'lerini al
            nobetci_ids = []
            for i in range(self.nobetci_listbox.count()):
                item = self.nobetci_listbox.item(i)
                teacher_id = item.data(Qt.UserRole)
                if teacher_id:
                    nobetci_ids.append(teacher_id)
    
            if not nobetci_ids:
                print("⚠️ Nöbetçi listesi boş, istatistik hazırlanmadı.")
                return
    
            session = SessionLocal()
    
            # 🔹 2️⃣ Sadece bu öğretmenler için NobetIstatistik kayıtlarını çek
            stmt = select(NobetIstatistik).where(NobetIstatistik.ogretmen_id.in_(nobetci_ids))
            records = session.execute(stmt).scalars().all()
    
            # 🔹 3️⃣ İstatistik sözlüğü oluştur
            istatistik_dict = {}
    
            for rec in records:
                istatistik_dict[rec.ogretmen_id] = {
                    "haftalik_ortalama": rec.haftalik_ortalama or 0.0,
                    "agirlikli_puan": rec.agirlikli_puan or 1.0,
                    "toplam_nobet": rec.toplam_nobet or 0,
                    "hafta_sayisi": rec.hafta_sayisi or 0,
                    "son_nobet_tarihi": rec.son_nobet_tarihi,
                    "son_nobet_yeri": getattr(rec, "son_nobet_yeri", None),
                }
    
            # 🔹 4️⃣ Eksik öğretmenler için varsayılan değer ekle
            for tid in nobetci_ids:
                if tid not in istatistik_dict:
                    istatistik_dict[tid] = {
                        "haftalik_ortalama": 0.0,
                        "agirlikli_puan": 1.0,
                        "toplam_nobet": 0,
                        "hafta_sayisi": 0,
                        "son_nobet_tarihi": None,
                        "son_nobet_yeri": None,
                    }
    
            # 🔹 5️⃣ Dağıtım motoruna aktar
            self.nobet_dagitim.set_teacher_statistics(istatistik_dict)
            print(f"✅ {len(istatistik_dict)} nöbetçi öğretmen için istatistik verisi hazırlandı.")
    
        except Exception as e:
            print(f"❌ İstatistik hazırlama hatası: {str(e)}")
    
        finally:
            session.close()

    
    def sonuclari_kaydet(self):
        """Nöbet dağılımı ve atanamayan kayıtlarını tek tarih ile kaydeder"""
        
        sonuc = self.sonuc
        kayit_tarihi = datetime.now().replace(microsecond=0)  # ortak timestamp
    
        if sonuc.get("assignments"):
            kayit_sonucu = self.data.save_results_NobetGecmisi(sonuc, substitution_date=kayit_tarihi)
            if kayit_sonucu["status"] == "success":
                print(f"✅ {kayit_sonucu['message']}")
                self.list_dagilim_tarihleri()
                ist_sonucu = self.data.istatistik_save_NobetIstatistik(sonuc)
                print(f"✅ {ist_sonucu['message']}")
                
            else:
                print(f"⚠️ HATA: {kayit_sonucu['message']}")
    
        if sonuc.get("unassigned"):
            kayit_sonucu = self.data.save_results_NobetAtanamayan(sonuc, substitution_date=kayit_tarihi)
            if kayit_sonucu["status"] == "success":
                print(f"✅ {kayit_sonucu['message']}")
            else:
                print(f"⚠️ HATA: {kayit_sonucu['message']}")
    
        self.statusBar().showMessage(
            f"Dağılım {kayit_tarihi.strftime('%d.%m.%Y %H:%M')} tarihinde kaydedildi.",
            5000
        )
     
    def list_dagilim_tarihleri(self):
        """
        NobetGecmisi için:
          - Seçili haftanın gününe göre filtrele
          - Aynı takvim gününü gruplandır (YYYY-MM-DD)
          - Her gün için en SON kaydın tam datetime'ını (hh:mm:ss.000000) getir
          - Son 5 günü listele
        """
        try:
            session = SessionLocal()
            self.list_dagilimler.clear()
    
            # 1) Gün belirle (combobox seçimi veya mevcut seçim)
            bugun_gun = self.secilen_gun or self.secilen_gunu_al()
            if not bugun_gun:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce bir gün seçin.")
                return
    
            en2num = {
                "Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3,
                "Thursday": 4, "Friday": 5, "Saturday": 6
            }
            en2tr = {
                "Sunday": "Pazar", "Monday": "Pazartesi", "Tuesday": "Salı",
                "Wednesday": "Çarşamba", "Thursday": "Perşembe",
                "Friday": "Cuma", "Saturday": "Cumartesi"
            }
    
            gun_num = en2num.get(bugun_gun, int(datetime.now().strftime('%w')))
            gun_etiket = en2tr.get(bugun_gun, bugun_gun)
    
            # 2) Grupla: gün bazında (YYYY-MM-DD), her grup için SON datetime'ı al
            #    Not: SQLite için func.strftime kullanıyoruz.
            q = (
                session.query(
                    func.strftime('%Y-%m-%d', NobetGecmisi.tarih).label('gun'),
                    func.max(NobetGecmisi.tarih).label('son_dt')
                )
                .filter(func.strftime('%w', NobetGecmisi.tarih) == str(gun_num))
                .group_by('gun')
                .order_by(func.max(NobetGecmisi.tarih).desc())
                .limit(5)
            )
            rows = q.all()
    
            if not rows:
                self.statusBar().showMessage(f"{gun_etiket} günü için kayıtlı nöbet dağılımı bulunamadı.", 4000)
                return
    
            # 3) Listeyi doldur (etikette saat/dakika/saniye göster; UserRole'e tam datetime koy)
            for _, son_dt in rows:
                # son_dt: datetime (mikrosaniye dahil)
                item_text = f"{gun_etiket} - {son_dt.strftime('%d.%m.%Y %H:%M:%S')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, son_dt)  # tam datetime sakla
                self.list_dagilimler.addItem(item)
    
            self.statusBar().showMessage(
                f"{gun_etiket} günü için son {len(rows)} farklı gün listelendi.", 4000
            )
    
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tarih listesi alınamadı:\n{str(e)}")
        finally:
            session.close()

    def load_dagilim_from_database(self, selected_datetime):
        """
        Verilen tarihe ait nöbet dağılımını yükler.
        - Atanan dersler: NobetGecmisi
        - Atanamayan dersler: NobetAtanamayan
        - Devamsız öğretmenler: ilgili öğretmenlerin ders programından yüklenir
        """
        from db.models import NobetGecmisi, NobetAtanamayan
        from db.database import SessionLocal
    
        try:
            session = SessionLocal()
    
            # 🔹 1. Atanan nöbetler (NobetGecmisi)
            assigned_records = (
                session.query(NobetGecmisi)
                .filter(NobetGecmisi.tarih == selected_datetime)
                .all()
            )
    
            # 🔹 2. Atanamayan dersler (NobetAtanamayan)
            unassigned_records = (
                session.query(NobetAtanamayan)
                .filter(NobetAtanamayan.tarih == selected_datetime)
                .all()
            )
    
            if not assigned_records and not unassigned_records:
                QMessageBox.information(self, "Bilgi", "Seçilen tarihe ait kayıt bulunamadı.")
                return
    
            sonuc = {
                "assignments": [],
                "unassigned": [],
                "teacher_counts": {},
                "teacher_schedule": {},
                "penalty": 0
            }
    
            # 🔹 Devamsız öğretmenleri topla (atanan ve atanamayanlardan)
            devamsiz_ids = {r.devamsiz for r in assigned_records if r.devamsiz} | \
                           {r.ogretmen_id for r in unassigned_records if r.ogretmen_id}
    
            # 🔹 Devamsız tabloyu temizle
            self.devamsiz_schedule.clear()
            self.devamsiz_schedule.setRowCount(0)
            self.devamsiz_schedule.setColumnCount(0)
    
            # 🔹 Gün kontrolü (seçilmemişse varsayılan olarak Monday)
            if not self.secilen_gun:
                self.secilen_gun = "Monday"
    
            # 🔹 Her devamsız öğretmeni tabloya geri yükle
            
            for dev_id in devamsiz_ids:
                try:
                    ders_prog = self.data.get_ogretmen_programi(dev_id, self.secilen_gun, ayrinti=False)
                    if not ders_prog or not ders_prog.get("dersleri"):
                        print(f"⚠️ Öğretmen {dev_id} için ders programı bulunamadı.")
                        continue
                    sorted_lessons = dict(sorted(ders_prog["dersleri"].items()))
                    self.pencere_fonksiyon.add_devamsiz_ogretmen_scheduler(
                        self.devamsiz_schedule,
                        {"ogretmen_id": dev_id, "dersleri": sorted_lessons}
                    )
                except Exception as inner_e:
                    print(f"⚠️ Devamsız öğretmen {dev_id} yüklenirken hata: {inner_e}")
                    continue
    
            # 🔹 Atanan nöbetleri işle
            for rec in assigned_records:
                sonuc["assignments"].append({
                    "hour": rec.saat,
                    "class": rec.sinif,
                    "teacher_id": rec.ogretmen_id,
                    "absent_teacher_id": rec.devamsiz
                })
                sonuc["teacher_counts"][rec.ogretmen_id] = (
                    sonuc["teacher_counts"].get(rec.ogretmen_id, 0) + 1
                )
                sonuc["teacher_schedule"].setdefault(rec.ogretmen_id, []).append(rec.saat)
    
            # 🔹 Atanamayan dersleri işle
            for rec in unassigned_records:
                sonuc["unassigned"].append({
                    "hour": rec.saat,
                    "class": rec.sinif,
                    "absent_teacher_id": rec.ogretmen_id  # burada ogretmen_id = devamsız öğretmen
                })

            self.sonuc = sonuc
    
            # 🔹 Tabloları güncelle
            nobetci_dersleri = self.get_nobetci_dersleri()
            self.pencere_fonksiyon.nobet_sonuclari_tabloda_goster(
                self.dagitilamayan_table, self.sonuc["unassigned"], False
            )
            self.pencere_fonksiyon.nobet_atama_sayisi_tabloda_goster(
                self.table_nobetsayisi, self.sonuc["teacher_counts"]
            )
            self.pencere_fonksiyon.atama_sonuc_tablosu_yukle(
                self.nobetci_schedule_manuel,
                self.devamsiz_schedule,
                nobetci_dersleri,
                self.sonuc
            )
    
            # 🔹 Bilgi mesajı
            toplam_devamsiz = len(devamsiz_ids)
            toplam_atama = len(sonuc["assignments"])
            toplam_bos = len(sonuc["unassigned"])
    
            QMessageBox.information(
                self, "Yüklendi",
                f"{selected_datetime.strftime('%d.%m.%Y %H:%M')} tarihli dağılım yüklendi.\n"
                f"{toplam_devamsiz} devamsız öğretmen, {toplam_atama} atama, {toplam_bos} atanamayan ders bulundu."
            )
    
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata oluştu:\n{str(e)}")
        finally:
            session.close()
       
        
    def haftalik_nobet_yeri_degistir(self):
        """
        Haftalık nöbet yerleri kontrol edilir:
        Eğer mevcut haftanın Pazar günü (uygulama_bitis) geçmişse ve o hafta için
        değişim kaydı yoksa nöbet yerleri güncellenir.
        Ancak belirli öğretmenler (ör. 'AYSAN KESKİN') sabit tutulur.
        """
        SABIT_OGRETMENLER = ["AYSAN KESKİN"]
        from datetime import datetime, timedelta
    
        try:
            session = SessionLocal()
    
            # 🔹 En son nöbet haftasını bul
            latest_record = (
                session.query(NobetGorevi.uygulama_tarihi)
                .order_by(NobetGorevi.uygulama_tarihi.desc())
                .first()
            )
            if not latest_record:
                self.statusBar().showMessage("Henüz nöbet kaydı bulunamadı.", 5000)
                return
    
            uygulama_baslangic = latest_record[0]
            uygulama_bitis = uygulama_baslangic + timedelta(days=6)
            bugun = datetime.now()
    
            # 🔸 Henüz hafta bitmemişse değişim yapılmaz
            if bugun.date() <= uygulama_bitis.date():
                kalan = (uygulama_bitis.date() - bugun.date()).days
                self.statusBar().showMessage(
                    f"Hafta bitimine {kalan} gün kaldı, nöbet değişimi yapılmayacak.", 5000
                )
                return
    
            # 🔹 Aynı hafta için zaten değişim yapılmış mı?
            mevcut_degisim = (
                session.query(NobetDegisimKaydi)
                .filter(
                    and_(
                        func.date(NobetDegisimKaydi.uygulama_baslangic) == func.date(uygulama_baslangic),
                        func.date(NobetDegisimKaydi.uygulama_bitis) == func.date(uygulama_bitis),
                    )
                )
                .first()
            )
            if mevcut_degisim:
                self.statusBar().showMessage(
                    f"{uygulama_baslangic.strftime('%d.%m.%Y')} haftası için değişim zaten yapılmış.", 6000
                )
                return
    
            # 🔹 O haftanın nöbet kayıtlarını al
            gorevler = (
                session.query(NobetGorevi)
                .join(NobetOgretmen)
                .filter(NobetGorevi.uygulama_tarihi == uygulama_baslangic)
                .add_columns(NobetOgretmen.adi_soyadi)
                .all()
            )
    
            if not gorevler:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    f"{uygulama_baslangic.strftime('%d.%m.%Y')} haftasına ait nöbet kaydı bulunamadı.",
                )
                return
    
            # 🔁 Aynı gün nöbetçileri arasında yer rotasyonu
            grouped_by_day = {}
            for gorev, ogretmen_adi in gorevler:
                grouped_by_day.setdefault(gorev.nobet_gun, []).append((gorev, ogretmen_adi))
    
            degisen_sayisi = 0
    
            for gun, grup in grouped_by_day.items():
                # "AYSAN KESKİN" sabit kalsın
                sabit_ogretmenler = [g for g in grup if g[1] in SABIT_OGRETMENLER]
                degisebilirler = [g for g in grup if g[1] not in sabit_ogretmenler]
    
                if len(degisebilirler) > 1:
                    # Sadece sabit olmayanlar arasında rotasyon
                    yerler = [x[0].nobet_yeri for x in degisebilirler]
                    yerler_rotated = yerler[1:] + yerler[:1]
    
                    for (kayit, ogretmen_adi), yeni_yer in zip(degisebilirler, yerler_rotated):
                        kayit.nobet_yeri = yeni_yer
                        degisen_sayisi += 1
    
            # 🔹 Değişiklik kaydını logla
            degisim_log = NobetDegisimKaydi(
                uygulama_baslangic=uygulama_baslangic,
                uygulama_bitis=uygulama_bitis,
                degisim_tarihi=bugun,
                aciklama=(
                    f"{uygulama_baslangic.strftime('%d.%m.%Y')} haftasının nöbet yerleri "
                    f"{bugun.strftime('%d.%m.%Y')} tarihinde güncellendi."
                ),
            )
            session.add(degisim_log)
            session.commit()
    
            # 🔸 Kullanıcı bilgilendirmesi
            self.statusBar().showMessage(
                f"✅ {degisen_sayisi} nöbet yerinde değişiklik yapıldı (sabit öğretmenler hariç).",
                6000,
            )
            QMessageBox.information(
                self,
                "Nöbet Rotasyonu Tamamlandı",
                f"{degisen_sayisi} nöbet yerinde değişiklik yapıldı.\n"
                f"Hafta: {uygulama_baslangic.strftime('%d.%m.%Y')} - {uygulama_bitis.strftime('%d.%m.%Y')}\n"
                f"Sabit öğretmen(ler): {', '.join(SABIT_OGRETMENLER)}",
            )
    
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Hata", f"Nöbet yerleri değiştirilemedi:\n{str(e)}")
        finally:
            session.close()
