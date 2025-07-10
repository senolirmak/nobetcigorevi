#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  3 22:03:50 2025

@author: senolirmak
"""

# models.py

from sqlalchemy import (Column, Integer, String, Boolean, Date,
                        Time, ForeignKey, Float, DateTime)
from sqlalchemy.orm import relationship
from nobet.db.database import Base

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class NobetOgretmen(BaseModel):
    __tablename__ = 'nobet_ogretmen'
    
    adi_soyadi = Column(String(100), nullable=False, unique=True)
    brans = Column(String(50), nullable=False)
    nobeti_var = Column(Boolean, nullable=False)
    gorev_tipi = Column(String(50))
    
    # Relationships
    dersler = relationship("NobetDersProgrami", back_populates="ogretmen")
    nobetler = relationship("NobetGorevi", back_populates="ogretmen")
    gecmis = relationship("NobetGecmisi", back_populates="ogretmen")
    devamsizliklar = relationship("Devamsizlik", back_populates="ogretmen")
    istatistikler = relationship("NobetIstatistik", back_populates="ogretmen")
    atanamayan = relationship("NobetAtanamayan", back_populates="ogretmen")

class NobetDersProgrami(BaseModel):
    __tablename__ = 'nobet_dersprogrami'
    
    gun = Column(String(10), nullable=False)
    giris_saat = Column(Time, nullable=False)
    cikis_saat = Column(Time, nullable=False)
    ders_adi = Column(String(100), nullable=False)
    sinif = Column(Integer, nullable=False)
    sube = Column(String(5), nullable=False)
    subeadi = Column(String(10), nullable=False)
    ders_saati = Column(Integer, nullable=False)
    ders_saati_adi = Column(String(10), nullable=False)
    uygulama_tarihi = Column(Date, nullable=False, default="2025-04-21 13:00:00")
    ders_ogretmeni_id = Column(Integer, ForeignKey('nobet_ogretmen.id'), nullable=False)
    
    # Relationships
    ogretmen = relationship("NobetOgretmen", back_populates="dersler")

class NobetGorevi(BaseModel):
    __tablename__ = 'nobet_nobetgorevi'
    
    nobet_gun = Column(String(10), nullable=False)
    nobet_yeri = Column(String(100), nullable=False)
    nobetci_ogretmen_id = Column(Integer, ForeignKey('nobet_ogretmen.id'), nullable=False)
    uygulama_tarihi = Column(Date, nullable=False, default="2025-04-21 13:00:00")
    # Relationships
    ogretmen = relationship("NobetOgretmen", back_populates="nobetler")

class NobetGecmisi(BaseModel):
    __tablename__ = 'nobet_nobetgecmisi'
    
    saat = Column(Integer)
    sinif = Column(String)
    devamsiz = Column(Integer)
    tarih = Column(DateTime)
    atandi = Column(Integer, default=1)
    nobetgecmisi_ogretmen_id = Column(Integer, ForeignKey('nobet_ogretmen.id'), nullable=False)
    
    # Relationships
    ogretmen = relationship("NobetOgretmen", back_populates="gecmis")

class NobetAtanamayan(BaseModel):
    __tablename__ = 'nobet_atanamayan'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    saat = Column(Integer)
    sinif = Column(String)
    devamsiz = Column(Integer, ForeignKey('nobet_ogretmen.id'), nullable=False)
    tarih = Column(DateTime)
    atandi = Column(Integer, default=0)

    # Relationships
    ogretmen = relationship("NobetOgretmen", back_populates="atanamayan")

class Devamsizlik(Base):
    __tablename__ = 'devamsizliklar'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ogretmen_id = Column(Integer, ForeignKey('nobet_ogretmen.id'), nullable=False)
    baslangic_tarihi = Column(Date, nullable=False)
    bitis_tarihi = Column(Date, nullable=True)  # None ise tek günlük devamsızlık
    aciklama = Column(String(200))
    
    ogretmen = relationship("NobetOgretmen", back_populates="devamsizliklar")

class NobetIstatistik(BaseModel):
    __tablename__ = 'nobet_nobetistatistik'
    
    id = Column(Integer, primary_key=True)
    toplam_nobet = Column(Integer, default=0)  # Toplam nöbet sayısı
    atanmayan_nobet = Column(Integer, default=0)  # Atanamayan nöbet sayısı
    haftalik_ortalama = Column(Float, default=0.0)  # Haftalık ortalama nöbet sayısı
    hafta_sayisi = Column(Integer, default=0)  # İstatistiğin tutulduğu hafta sayısı
    son_nobet_tarihi = Column(Date)  # Son nöbet tarihi
    agirlikli_puan = Column(Float, default=1.0)  # Dağıtım öncelik puanı
    nobetistatistik_ogretmen_id = Column(Integer, ForeignKey('nobet_ogretmen.id'), nullable=False, unique=True)
    
    # Relationships
    ogretmen = relationship("NobetOgretmen", back_populates="istatistikler")


