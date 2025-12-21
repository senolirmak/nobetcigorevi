#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLAlchemy ORM modelleri - Nöbetçi Görevi Sistemi
@author: Ş.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class NobetPersonel(BaseModel):
    __tablename__ = 'nobet_personel'

    adi_soyadi = Column(String(100), nullable=False)
    brans = Column(String(50), nullable=False)
    kimlikno = Column(String(11), nullable=False, unique=True)
    gorev_tipi = Column(String(50))
    #cinsiyet: 1=ERKEK, 0=KADIN
    cinsiyet = Column(Integer, nullable=True)

class NobetOgretmen(BaseModel):
    __tablename__ = "nobet_ogretmen"

    adi_soyadi = Column(String(100), nullable=False, unique=True)
    brans = Column(String(50), nullable=False)
    nobeti_var = Column(Boolean, default=True)
    gorev_tipi = Column(String(50))
    uygulama_tarihi = Column(DateTime, default=datetime.now)
    #cinsiyet: 1=ERKEK, 0=KADIN
    cinsiyet = Column(Integer, nullable=True)

    dersler = relationship("NobetDersProgrami", back_populates="ogretmen", cascade="all, delete-orphan")
    nobetler = relationship("NobetGorevi", back_populates="ogretmen", cascade="all, delete-orphan")
    devamsizliklar = relationship("Devamsizlik", back_populates="ogretmen", cascade="all, delete-orphan")
    istatistikler = relationship("NobetIstatistik", back_populates="ogretmen", cascade="all, delete-orphan", uselist=False)
    atanamayan = relationship("NobetAtanamayan", back_populates="ogretmen", cascade="all, delete-orphan")
    gecmis = relationship("NobetGecmisi", back_populates="ogretmen")  # cascade kaldırıldı


class NobetDersProgrami(BaseModel):
    __tablename__ = "nobet_dersprogrami"

    gun = Column(String(10), nullable=False)
    giris_saat = Column(Time, nullable=False)
    cikis_saat = Column(Time, nullable=False)
    ders_adi = Column(String(100), nullable=False)
    sinif = Column(String(10), nullable=False)
    sube = Column(String(10), nullable=False)
    subeadi = Column(String(10), nullable=False)
    ders_saati = Column(Integer, nullable=False)
    uygulama_tarihi = Column(DateTime, default=datetime.now)
    ogretmen_id = Column(Integer, ForeignKey("nobet_ogretmen.id"), nullable=False)

    ogretmen = relationship("NobetOgretmen", back_populates="dersler")


class NobetGorevi(BaseModel):
    __tablename__ = "nobet_gorevi"

    nobet_gun = Column(String(10), nullable=False)
    nobet_yeri = Column(String(100), nullable=False)
    uygulama_tarihi = Column(DateTime, default=datetime.now)
    ogretmen_id = Column(Integer, ForeignKey("nobet_ogretmen.id"), nullable=False)

    ogretmen = relationship("NobetOgretmen", back_populates="nobetler")


class Devamsizlik(BaseModel):
    __tablename__ = "nobet_devamsizlik"

    baslangic_tarihi = Column(DateTime, nullable=False)
    bitis_tarihi = Column(DateTime)
    aciklama = Column(String(200))
    ogretmen_id = Column(Integer, ForeignKey("nobet_ogretmen.id"), nullable=False)

    ogretmen = relationship("NobetOgretmen", back_populates="devamsizliklar")


class NobetGecmisi(BaseModel):
    __tablename__ = "nobet_gecmis"

    saat = Column(Integer)
    sinif = Column(String)
    devamsiz = Column(Integer)
    tarih = Column(DateTime, default=datetime.now)
    atandi = Column(Integer, default=1)
    ogretmen_id = Column(Integer, ForeignKey("nobet_ogretmen.id"), nullable=False)

    ogretmen = relationship("NobetOgretmen", back_populates="gecmis")


class NobetAtanamayan(BaseModel):
    __tablename__ = "nobet_atanamayan"

    saat = Column(Integer)
    sinif = Column(String)
    tarih = Column(DateTime, default=datetime.now)
    atandi = Column(Integer, default=0)
    ogretmen_id = Column(Integer, ForeignKey("nobet_ogretmen.id"), nullable=False)

    ogretmen = relationship("NobetOgretmen", back_populates="atanamayan")

    
class NobetIstatistik(BaseModel):
    __tablename__ = "nobet_istatistik"

    toplam_nobet = Column(Integer, default=0)
    atanmayan_nobet = Column(Integer, default=0)
    haftalik_ortalama = Column(Float, default=0.0)
    hafta_sayisi = Column(Integer, default=0)
    son_nobet_tarihi = Column(DateTime)
    agirlikli_puan = Column(Float, default=1.0)
    son_nobet_yeri = Column(String(100))  # 🆕 Yeni alan eklendi
    ogretmen_id = Column(Integer, ForeignKey("nobet_ogretmen.id"), nullable=False, unique=True)

    ogretmen = relationship("NobetOgretmen", back_populates="istatistikler")

class NobetDegisimKaydi(BaseModel):
    __tablename__ = "nobet_degisim_kaydi"

    degisim_tarihi = Column(DateTime, default=datetime.now)  # değişiklik zamanı
    uygulama_baslangic = Column(DateTime, nullable=False)    # haftanın başlangıcı
    uygulama_bitis = Column(DateTime, nullable=False)        # haftanın bitişi
    aciklama = Column(String(200), default="Haftalık nöbet rotasyonu uygulandı")


