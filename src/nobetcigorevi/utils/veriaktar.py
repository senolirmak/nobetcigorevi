#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 20:48:16 2025

@author: senolirmak
"""

from nobetcigorevi.db.models import NobetGorevi, NobetOgretmen,NobetDersProgrami, Base
from nobetcigorevi.db.database import SessionLocal, engine
from contextlib import contextmanager
from datetime import datetime
import pandas as pd

class VeriAktar:
    def __init__(self):
        super().__init__()
        Base.metadata.create_all(bind=engine)
        
    """Handles all database operations"""
    @contextmanager
    def get_db_session(self):
        """Database session context manager"""
        session = SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def save_results_NobetOgretmen(self, personel_df):
        personel_df = personel_df.dropna(subset=['adi_soyadi'])
        status = {
            "record_count": 0,
            "status": "success",
            "message": ""
        }
        try:
            with self.get_db_session() as session:
                # Save assigned substitutions
                for _, row in personel_df.iterrows():
                    ogretmen = NobetOgretmen(
                        adi_soyadi=row['adi_soyadi'],
                        brans=row['brans'],
                        nobeti_var=row['nobeti_var'],
                        gorev_tipi=row['gorev_tipi']  # opsiyonel
                    )
                    session.add(ogretmen)
                    status["record_count"] += 1
        
                session.commit()
                status["message"] = (f"Kayıt Başarılı {status['record_count']} tane personel kayıt edildi")
                
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
            # Log the error here if needed
        
        return status

    def save_results_NobetGorevi(self, nobet_df):
        nobet_df = nobet_df.dropna(subset=['nobetci'])
        status = {
            "record_count": 0,
            "status": "success",
            "message": ""
        }
        try:
            with self.get_db_session() as session:
                # Save assigned substitutions
                for _, row in nobet_df.iterrows():
                    # Öğretmeni bul
                    ogretmen = session.query(NobetOgretmen).filter_by(adi_soyadi=row['nobetci']).first()
                    if ogretmen is not None:
                        nobet = NobetGorevi(
                            nobet_gun=row['nobet_gun'],
                            nobet_yeri=row['nobet_yeri'],
                            nobetci_ogretmen_id=ogretmen.id,
                            uygulama_tarihi=pd.to_datetime(row['uygulama_tarihi']).date(),
                        )
                        session.add(nobet)
                        status["record_count"] += 1
                    else:
                        print(f"Uyarı: {row['nobetci']} veritabanında bulunamadı.")
                    
        
                session.commit()
                status["message"] = (f"Kayıt Başarılı {status['record_count']} tane Nöbetçi kayıt edildi")
                
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
            # Log the error here if needed
        
        return status

    def save_results_NobetDersProgrami(self, program_df):
        program_df = program_df.dropna(subset=['ders_ogretmeni'])
        status = {
            "record_count": 0,
            "status": "success",
            "message": ""
        }
        try:
            with self.get_db_session() as session:
                # Save assigned substitutions
                for _, row in program_df.iterrows():
                    # Öğretmeni bul
                    ogretmen = session.query(NobetOgretmen).filter_by(adi_soyadi=row['ders_ogretmeni']).first()
                    if ogretmen is not None:
                        program = NobetDersProgrami(
                            gun=row['gun'],
                            giris_saat=datetime.strptime(row['giris_saat'], "%H:%M").time(),
                            cikis_saat=datetime.strptime(row['cikis_saat'], "%H:%M").time(),
                            ders_adi =row['ders_adi'],
                            sinif=row['sinif'],
                            sube=row['sube'],
                            subeadi=row['subeadi'],
                            ders_saati=row['ders_saati'],
                            ders_saati_adi=row['ders_saati_adi'],
                            uygulama_tarihi=pd.to_datetime(row['uygulama_tarihi']).date(),
                            ders_ogretmeni_id=ogretmen.id
                        )
                        session.add(program)
                        status["record_count"] += 1
                    else:
                        print(f"Uyarı: {row['nobetci']} veritabanında bulunamadı.")
                    
        
                session.commit()
                status["message"] = (f"Kayıt Başarılı {status['record_count']} tane ders dağılımı kayıt edildi")
                
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
            # Log the error here if needed
        
        return status