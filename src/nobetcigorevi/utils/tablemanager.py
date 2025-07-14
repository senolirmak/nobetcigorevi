#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 24 10:30:18 2025

@author: senolirmak
"""
from PyQt5.QtWidgets import (QDialog, QListWidget,QStyledItemDelegate, 
                             QLineEdit,QVBoxLayout,QPushButton, QMessageBox)

from PyQt5.QtGui import  QDoubleValidator
from PyQt5.QtCore import Qt, pyqtSignal, QObject

class ChangeRecord:
    def __init__(self, table_id, row, col, old_value, new_value):
        self.table_id = table_id
        self.row = row
        self.col = col
        self.old_value = old_value
        self.new_value = new_value

class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, table_id=None):
        super().__init__(parent)
        self.table_id = table_id
        self.old_value = ""
    
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        item = index.model().data(index, Qt.DisplayRole)
        self.old_value = item if item is not None else ""
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setText(str(value if value is not None else ""))
    
    def setModelData(self, editor, model, index):
        old_value = self.old_value
        new_value = editor.text()
        
        if old_value != new_value:
            if hasattr(self.parent(), 'cell_data_changed'):
                change = ChangeRecord(
                    self.table_id,
                    index.row(),
                    index.column(),
                    old_value,
                    new_value
                )
                self.parent().cell_data_changed.emit(change)
        
        model.setData(index, new_value, Qt.EditRole)

class NumericDelegate(CustomDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator())
        item = index.model().data(index, Qt.DisplayRole)
        self.old_value = item if item is not None else ""
        return editor

class TableManager(QObject):
    cell_data_changed = pyqtSignal(object)  # ChangeRecord nesnesi gönderir
    
    def __init__(self):
        super().__init__()
        self.tables = {}
        self.change_stack = []
        self.current_change_index = -1
    
    def register_table(self, table_widget, table_id):
        self.tables[table_id] = table_widget
        self.setup_delegate(table_widget, table_id)
    
    def setup_delegate(self, table, table_id):
        delegate = CustomDelegate(table, table_id)
        table.setItemDelegate(delegate)
        delegate.parent = lambda: self
    
    def record_change(self, change):
        # Gelecekteki değişiklikleri sil (yeni bir dal oluşturuldu)
        if self.current_change_index < len(self.change_stack) - 1:
            self.change_stack = self.change_stack[:self.current_change_index + 1]
        
        self.change_stack.append(change)
        self.current_change_index = len(self.change_stack) - 1
    
    def undo_change(self):
        if self.current_change_index >= 0:
            change = self.change_stack[self.current_change_index]
            table = self.tables[change.table_id]
            item = table.item(change.row, change.col)
            
            if item:
                item.setText(change.old_value)
            
            self.current_change_index -= 1
            return True
        return False
    
    def get_change_history(self):
        """Değişiklik geçmişini döndürür"""
        return self.change_stack

class DataSelectionDialog(QDialog):
    def __init__(self, data_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Veri Seçimi")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        self.list_widget.addItems(data_list)
        layout.addWidget(self.list_widget)
        
        select_button = QPushButton("Seç")
        select_button.clicked.connect(self.accept_selection)
        layout.addWidget(select_button)
        
        self.setLayout(layout)
    
    def accept_selection(self):
        if not self.list_widget.selectedItems():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir veri seçin!")
            return
        self.accept()
    
    def selected_data(self):
        return self.list_widget.currentItem().text()