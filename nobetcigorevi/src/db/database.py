#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 10 16:57:20 2025

@author: senolirmak
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# ---------------------------------------------------------
# Dosya ve dizin ayarları
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]  # proje kök dizini
DATABASE_PATH = BASE_DIR / "src" / "data" / "okul_veritabani.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# SQLAlchemy bağlantı yapısı
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # True -> SQL çıktısını terminale yazdırır
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ---------------------------------------------------------
# Yardımcı fonksiyon (bağlantı yönetimi)
# ---------------------------------------------------------
def get_db():
    """
    Her işlem için yeni bir Session açar ve işlem bitince kapatır.
    Kullanım örneği:
        with next(get_db()) as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
