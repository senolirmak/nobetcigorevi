#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database.py — Veritabanı:
$HOME/NobetciVeri/data/okul_veritabani.db
konumunda oluşturulur veya şablondan kopyalanır.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import shutil

# ---------------------------------------------------------
# Kullanıcı dizini
# ---------------------------------------------------------
BASE_USER_DIR = Path.home() / "NobetciVeri"
DATA_DIR = BASE_USER_DIR / "data"

# Klasörleri oluştur
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Veritabanı yolu
DATABASE_PATH = DATA_DIR / "okul_veritabani.db"

# ---------------------------------------------------------
# Şablon veritabanı (opt altındaki proje içinde)
# (/opt/Nobetci/nobetcigorevi/src/data/okul_veritabani.db)
# ---------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[1]               # .../nobetcigorevi/src
TEMPLATE_DB = SRC_DIR / "data" / "okul_veritabani.db"

# ---------------------------------------------------------
# Veritabanı yoksa otomatik oluştur veya şablondan kopyala
# ---------------------------------------------------------
if not DATABASE_PATH.exists():
    if TEMPLATE_DB.exists():
        print(f"📁 Şablon veritabanı bulundu. Kopyalanıyor → {DATABASE_PATH}")
        shutil.copy2(TEMPLATE_DB, DATABASE_PATH)
    else:
        print(f"🆕 Şablon bulunamadı. Yeni veritabanı oluşturulacak → {DATABASE_PATH}")
        # SQLAlchemy create_all ile tablo oluşturulacak

# ---------------------------------------------------------
# SQLAlchemy bağlantısı
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # SQL çıktısını görmek istersen True yap
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """Veritabanı oturumu üretir."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
