#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTableWidget tabanlı pencere yardımcı sınıfları
@author: senolirmak
"""

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from utils.database_util import TeacherManager


class PencereFonksiyon:
    def __init__(self):
        super().__init__()
        self.data = TeacherManager()

        # Renk tanımlamaları
        self.black_color = QColor(0, 0, 0)
        self.white_color = QColor(255, 255, 255)
        self.yellow_color = QColor(255, 255, 0)
        self.locked_color = QColor(240, 240, 240)
        self.initial_colors = {
            0: QColor(173, 216, 230),   # Light blue
            1: QColor(144, 238, 144),   # Light green
            2: QColor(255, 182, 193),   # Light pink
            3: QColor(220, 220, 220),   # Light gray
            4: QColor(255, 218, 185),   # Peach
            5: QColor(221, 160, 221),   # Plum
            6: QColor(152, 251, 152),   # Pale green
            7: QColor(175, 238, 238),   # Pale turquoise
            8: QColor(255, 228, 196)    # Bisque
        }

    # ------------------------------------------------------------------
    def setup_devamsiz_ogretmen_table(self, table_widget):
        """Devamsız öğretmen tablosunu başlıklarla kurar"""
        headers = ["Devamsız Öğretmen"] + [f"{i}.Ders" for i in range(1, 9)]
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        table_widget.setAlternatingRowColors(False)
        table_widget.clearContents()
        table_widget.setRowCount(0)
    
    # ------------------------------------------------------------------
    def add_devamsiz_ogretmen_scheduler(self, table, data):
        """
        Devamsız öğretmeni tabloya ekler.
        data = {"ogretmen_id": X, "dersleri": {1: "9/A", 2: "9/B", ...}}
        """
        try:
            ogretmen_id = data.get("ogretmen_id")
            dersler = data.get("dersleri", {})
    
            if ogretmen_id is None:
                print("⚠️ ogretmen_id None geldi, eklenmedi.")
                return
    
            teacher_name = self.data.get_ogretmen_adi(ogretmen_id)
            if not teacher_name:
                teacher_name = f"ID:{ogretmen_id}"
    
            # 🔹 Tablo sütun sayısını ayarla
            required_columns = 9  # 1 öğretmen sütunu + 8 ders sütunu
            if table.columnCount() < required_columns:
                table.setColumnCount(required_columns)
                headers = ["Öğretmen"] + [f"{i}. Ders" for i in range(1, 9)]
                table.setHorizontalHeaderLabels(headers)
    
            # 🔹 Yeni satır ekle
            row = table.rowCount()
            table.insertRow(row)
    
            # 🔹 Öğretmen hücresi
            teacher_item = QTableWidgetItem(teacher_name)
            teacher_item.setData(Qt.UserRole, ogretmen_id)
            teacher_item.setBackground(QColor("#e6f7ff"))
            teacher_item.setForeground(QBrush(QColor("#000000")))
            teacher_item.setFlags(teacher_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, teacher_item)
    
            # 🔹 Ders hücreleri
            for i in range(1, 9):
                sube_adi = dersler.get(i, "")
                item = QTableWidgetItem(sube_adi)
    
                if sube_adi:
                    item.setBackground(QBrush(self.initial_colors[i]))
                    item.setForeground(QBrush(QColor(0, 0, 0)))
                else:
                    item.setBackground(QBrush(self.black_color))
                    item.setForeground(QBrush(self.white_color))
    
                table.setItem(row, i, item)
    
            table.resizeColumnsToContents()
    
        except Exception as e:
            print(f"⚠️ add_devamsiz_ogretmen_scheduler hatası: {e}")

    
    # ------------------------------------------------------------------
    def read_ogretmen_dersleri_from_table(self, table_widget):
        """QTableWidget'ten devamsız dersleri okur"""
        ders_listesi = []
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, 0)
            if not item:
                continue
            teacher_id = item.data(Qt.UserRole)
            dersleri = {}
            for col in range(1, table_widget.columnCount()):
                cell = table_widget.item(row, col)
                if cell and cell.text().strip():
                    dersleri[col] = cell.text().strip()
            if dersleri:
                ders_listesi.append({"ogretmen_id": teacher_id, "dersleri": dersleri})
        return ders_listesi

    # ------------------------------------------------------------------
    def nobet_sonuclari_tabloda_goster(self, table_widget, atama_verileri, atandi=True):
        """Nöbet sonuçlarını QTableWidget'te gösterir"""
        table_widget.clear()
        if atandi:
            headers = ["Devamsız Öğretmen", "Saat", "Sınıf", "Nöbetçi Öğretmen"]
        else:
            headers = ["Devamsız Öğretmen", "Saat", "Sınıf", "Sebep"]

        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        table_widget.setRowCount(len(atama_verileri))

        for row, data in enumerate(atama_verileri):
            devamsiz_adi = self.data.get_ogretmen_adi(data["absent_teacher_id"])
            table_widget.setItem(row, 0, QTableWidgetItem(devamsiz_adi))
            table_widget.setItem(row, 1, QTableWidgetItem(f"{data['hour']}. Ders"))
            table_widget.setItem(row, 2, QTableWidgetItem(data["class"]))
            if atandi:
                nobetci_adi = self.data.get_ogretmen_adi(data["teacher_id"])
                table_widget.setItem(row, 3, QTableWidgetItem(nobetci_adi))
            else:
                item = QTableWidgetItem("Atanamadı")
                item.setForeground(QBrush(QColor(255, 0, 0)))
                table_widget.setItem(row, 3, item)

        table_widget.resizeColumnsToContents()

    # ------------------------------------------------------------------
    def nobet_atama_sayisi_tabloda_goster(self, table_widget, atama_verileri):
        """Nöbet atama sayısını tabloya yazar"""
        table_widget.clear()
        table_widget.setColumnCount(2)
        table_widget.setHorizontalHeaderLabels(["Nöbetçi Öğretmen", "Atanan"])
        table_widget.setRowCount(len(atama_verileri))

        for row, (tid, count) in enumerate(atama_verileri.items()):
            table_widget.setItem(row, 0, QTableWidgetItem(self.data.get_ogretmen_adi(tid)))
            table_widget.setItem(row, 1, QTableWidgetItem(str(count)))

        table_widget.resizeColumnsToContents()

    # ------------------------------------------------------------------
    def atama_sonuc_tablosu_yukle(self, table_atama, table_devamsiz, ogretmen_data, dagilim_sonuc=None):
        """Atama sonuçlarını tabloya uygular"""
        table_atama.clear()
        headers = ["Nöbetçi Öğretmen"] + [f"{i}.Ders" for i in range(1, 9)]
        table_atama.setColumnCount(len(headers))
        table_atama.setHorizontalHeaderLabels(headers)
        table_atama.setRowCount(len(ogretmen_data))

        for row, ogr in enumerate(ogretmen_data):
            teacher_id = ogr["ogretmen_id"]
            teacher_name = self.data.get_ogretmen_adi(teacher_id)
            name_item = QTableWidgetItem(teacher_name)
            name_item.setData(Qt.UserRole, teacher_id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            table_atama.setItem(row, 0, name_item)

            for hour in range(1, 9):
                class_info = ogr["dersleri"].get(hour, "")
                cell = QTableWidgetItem(class_info)
                if not class_info:
                    cell.setBackground(QBrush(self.black_color))
                    cell.setForeground(QBrush(self.white_color))
                else:
                    cell.setBackground(QBrush(self.locked_color))
                    cell.setForeground(QBrush(QColor(0, 0, 0)))
                table_atama.setItem(row, hour, cell)

        # Yeni atamalar varsa sarıya boya
        if dagilim_sonuc and "assignments" in dagilim_sonuc:
            for a in dagilim_sonuc["assignments"]:
                tid, hour, cls = a["teacher_id"], a["hour"], a["class"]
                for r in range(table_atama.rowCount()):
                    if table_atama.item(r, 0).data(Qt.UserRole) == tid:
                        cell = table_atama.item(r, hour)
                        if cell is None:
                            cell = QTableWidgetItem()
                            table_atama.setItem(r, hour, cell)
                        cell.setText(cls)
                        cell.setBackground(QBrush(self.yellow_color))
                        cell.setForeground(QBrush(QColor(0, 0, 0)))

                # Devamsız tablosunda da aynı hücreyi sarı yap
                for r in range(table_devamsiz.rowCount()):
                    if table_devamsiz.item(r, 0).data(Qt.UserRole) == a["absent_teacher_id"]:
                        c = table_devamsiz.item(r, hour)
                        if c:
                            c.setBackground(QBrush(self.yellow_color))
                            c.setForeground(QBrush(QColor(0, 0, 0)))

        table_atama.resizeColumnsToContents()

    # ------------------------------------------------------------------
    def nobet_atamalarini_say(self, main_table):
        """
        Nöbetçi öğretmenlerin yeni atamalarını sayar ve istatistik sözlüğü döner.
        (Sarı renkle işaretli hücreler "atanmış" kabul edilir.)

        Args:
            main_table (QTableWidget): Nöbetçi öğretmen ders dağıtım tablosu

        Returns:
            dict: {ogretmen_id: atama_sayisi}
        """
        stats = {}

        for row in range(main_table.rowCount()):
            teacher_item = main_table.item(row, 0)
            if not teacher_item:
                continue

            teacher_id = teacher_item.data(Qt.UserRole)
            atama_sayisi = 0

            # Ders sütunlarını dolaş
            for col in range(1, main_table.columnCount()):
                cell = main_table.item(row, col)
                if not cell:
                    continue

                # Hücre sarıysa (yeni atama) say
                bg_color = cell.background().color()
                if (bg_color.red(), bg_color.green(), bg_color.blue()) == (255, 255, 0):
                    atama_sayisi += 1

            stats[teacher_id] = atama_sayisi

        return stats
    
    # --------------------------------------------------------------------
    def get_optimization_weights(self, mode: int):
        """
        Optimizasyon ağırlıklarını (penalty weights) döndürür.
        Slider değeri (1-4) -> mod seçimi yapar.
    
        1: Hız Öncelikli (daha gevşek cezalar)
        2: Denge (orta seviyede cezalar)
        3: Adalet Öncelikli (yüksek cezalar)
        4: Manuel Ayar (kullanıcı tarafından belirlenebilir)
        """
    
        presets = {
            1: {
                'overload': 100,       # aşırı yüklenme
                'inequality': 200,     # eşitsiz dağılım
                'unassigned': 1000,     # atanamayan ders
                'no_duty': 400,        # hiç nöbeti olmayan
                'conflict': 1000,      # çakışan nöbet
                'unfair': 500,         # istatistiksel adaletsizlik
                'same_location': 600   # aynı nöbet yerinde ardışık atama cezası
            },
            2: {
                'overload': 400,       # aşırı yüklenme
                'inequality': 1000,     # eşitsiz dağılım
                'unassigned': 1000,     # atanamayan ders
                'no_duty': 400,        # hiç nöbeti olmayan
                'conflict': 1000,      # çakışan nöbet
                'unfair': 800,         # istatistiksel adaletsizlik
                'same_location': 600   # aynı nöbet yerinde ardışık atama cezası
            },
            3: {
                'overload': 400,       # aşırı yüklenme
                'inequality': 400,     # eşitsiz dağılım
                'unassigned': 1000,     # atanamayan ders
                'no_duty': 500,        # hiç nöbeti olmayan
                'conflict': 1000,      # çakışan nöbet
                'unfair': 900,         # istatistiksel adaletsizlik
                'same_location': 600   # aynı nöbet yerinde ardışık atama cezası
            },
            4: {
                'overload': 100,       # aşırı yüklenme
                'inequality': 300,     # eşitsiz dağılım
                'unassigned': 1000,     # atanamayan ders
                'no_duty': 400,        # hiç nöbeti olmayan
                'conflict': 1000,      # çakışan nöbet
                'unfair': 1000,         # istatistiksel adaletsizlik
                'same_location': 600   # aynı nöbet yerinde ardışık atama cezası
            },
        }
    
        # Eğer geçersiz bir mod gelirse 2 (denge) döndür
        return presets.get(mode, presets[2])
