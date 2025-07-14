#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 10 16:57:20 2025

@author: senolirmak
"""

# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 1. Yol belirleme
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / "data" / "okul_veritabani.db"

# 2. Dizin yoksa oluştur
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# 3. SQLAlchemy bağlantısı
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()