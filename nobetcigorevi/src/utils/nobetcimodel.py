#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 22:44:13 2025

@author: senolirmak
"""

from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt5.QtGui import QColor, QBrush
from utils.database_util import TeacherManager

class TeacherScheduleModel(QAbstractTableModel):
    def __init__(self, data=None, teacher_db=None):
        super().__init__()
        self._initial_data = data or []
        self._nob_data = TeacherManager()
        self._data = [row.copy() for row in self._initial_data]
        self._modified_cells = set()
        
        self.teacher_db = {ogr['ogretmen_id']: self._nob_data.get_ogretmen_adi(ogr['ogretmen_id']) for ogr in self._initial_data}
        self.headers = ["Nöbetçi Öğretmen"] + [f"{i}.Ders" for i in range(1, 9)]
        
        self.column_colors = {
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
        self.modified_color = QColor(255, 255, 0)  # Sarı
        self.empty_color = QColor(0, 0, 0)         # Siyah
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                teacher_id = self._data[row]["ogretmen_id"]
                return self.teacher_db.get(teacher_id, f"Bilinmeyen ({teacher_id})")
            else:
                return self._data[row]["dersleri"].get(col, "")
        
        elif role == Qt.BackgroundRole:
            if (row, col) in self._modified_cells:
                return QBrush(self.modified_color)
            elif col == 0:
                return QBrush(self.column_colors.get(col))
            elif not self._initial_data[row]["dersleri"].get(col) and not self._data[row]["dersleri"].get(col):
                return QBrush(self.empty_color)
            else:
                return QBrush(self.column_colors.get(col))
        
        elif role == Qt.TextColorRole:
            if col > 0 and not self._data[row]["dersleri"].get(col) and not self._initial_data[row]["dersleri"].get(col):
                return QColor(255, 255, 255)
        
        elif role == Qt.UserRole:
            if col == 0:
                return self._data[row]["ogretmen_id"]
            else:
                return (row, col) in self._modified_cells
        
        elif role == Qt.EditRole:
            if col == 0:
                return self._data[row]["ogretmen_id"]
            else:
                return self._data[row]["dersleri"].get(col, "")
        
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            
            if col == 0:
                return False
                
            # Sadece orijinalde boş olan veya değiştirilmiş hücreler düzenlenebilir
            if not self._initial_data[row]["dersleri"].get(col) or (row, col) in self._modified_cells:
                if value:
                    self._data[row]["dersleri"][col] = value
                elif col in self._data[row]["dersleri"]:
                    del self._data[row]["dersleri"][col]
                
                if value:
                    self._modified_cells.add((row, col))
                else:
                    self._modified_cells.discard((row, col))
                
                self.dataChanged.emit(index, index)
                return True
        return False
    
    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
            
        col = index.column()
        row = index.row()
        
        if col == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        # Sadece orijinalde boş olan veya değiştirilmiş hücreler düzenlenebilir
        if not self._initial_data[row]["dersleri"].get(col) or (row, col) in self._modified_cells:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None
    
    def addTeacher(self):
        teacher_ids = list(self.teacher_db.keys())
        teacher_names = [self.teacher_db[tid] for tid in teacher_ids]
        
        teacher, ok = QInputDialog.getItem(
            None, "Öğretmen Seç", "Öğretmen:",
            teacher_names, 0, False
        )
        
        if ok and teacher:
            teacher_id = teacher_ids[teacher_names.index(teacher)]
            self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
            self._data.append({"ogretmen_id": teacher_id, "dersleri": {}})
            self._initial_data.append({"ogretmen_id": teacher_id, "dersleri": {}})
            self.endInsertRows()
    
    def getData(self):
        return self._data
    
    def getTeacherName(self, teacher_id):
        return self.teacher_db.get(teacher_id, f"Bilinmeyen ({teacher_id})")