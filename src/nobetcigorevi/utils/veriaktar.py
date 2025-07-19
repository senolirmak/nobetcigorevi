#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 20:48:16 2025

@author: senolirmak
"""

from nobetcigorevi.db.models import (NobetGorevi, NobetOgretmen,
                                     NobetDersProgrami,NobetPersonel, Base)

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
    
    def insert_or_update(self, session, model_class, filter_by_dict, update_data):
        obj = session.query(model_class).filter_by(**filter_by_dict).first()
        if obj:
            for key, value in update_data.items():
                setattr(obj, key, value)
            return 'updated'
        else:
            obj = model_class(**{**filter_by_dict, **update_data})
            session.add(obj)
            return 'inserted'
            
    def parse_time(self, t):
        if isinstance(t, str):
            return datetime.strptime(t, "%H:%M").time()
        elif isinstance(t, pd.Timestamp):
            return t.time()
        elif isinstance(t, datetime):
            return t.time()
        return t  # zaten time objesi
    
    def save_results_NobetPersonel(self, personel_df):
        status = {
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "status": "success",
            "message": ""
        }
    
        required_columns = ['adisoyadi', 'brans', 'kimlikno', 'gorev']
        missing = [col for col in required_columns if col not in personel_df.columns]
        if missing:
            return {
                "status": "error",
                "message": f"Eksik sütun(lar): {', '.join(missing)}",
                "inserted": 0,
                "updated": 0,
                "errors": 0
            }
    
        personel_df = personel_df.dropna(subset=['adisoyadi', 'brans', 'kimlikno'])
    
        try:
            with self.get_db_session() as session:
                for _, row in personel_df.iterrows():
                    try:
                        result = self.insert_or_update(
                            session,
                            NobetPersonel,
                            {"kimlikno": int(row["kimlikno"])},
                            {
                                "adi_soyadi": row["adisoyadi"],
                                "brans": row["brans"],
                                "gorev_tipi": row["gorev"]
                            }
                        )
                        status[result] += 1
    
                    except Exception as row_error:
                        status["errors"] += 1
                        continue  # satır hatası varsa devam
    
                session.commit()
    
            status["message"] = (
                f"Kayıt tamamlandı. {status['inserted']} yeni kayıt eklendi, "
                f"{status['updated']} kayıt güncellendi, {status['errors']} satırda hata oluştu."
            )
    
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Veritabanı hatası: {str(e)}"
            })
    
        return status

    def save_results_NobetOgretmen(self, personel_df):
        status = {
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "status": "success",
            "message": ""
        }
    
        required_columns = ['adi_soyadi', 'brans', 'nobeti_var', 'gorev_tipi']
        missing = [col for col in required_columns if col not in personel_df.columns]
        if missing:
            return {
                "status": "error",
                "message": f"Eksik sütun(lar): {', '.join(missing)}",
                "inserted": 0,
                "updated": 0,
                "errors": 0
            }
    
        personel_df = personel_df.dropna(subset=['adi_soyadi', 'brans', 'nobeti_var'])
    
        try:
            with self.get_db_session() as session:
                for _, row in personel_df.iterrows():
                    try:
                        result = self.insert_or_update(
                            session,
                            NobetOgretmen,
                            {"adi_soyadi": row["adi_soyadi"],
                             "brans": row["brans"]
                             },
                            {
                                "adi_soyadi": row["adi_soyadi"],
                                "brans": row["brans"],
                                'nobeti_var': row['nobeti_var'],
                                "gorev_tipi": row["gorev_tipi"]
                            }
                        )
                        status[result] += 1

                    except Exception as row_error:
                        status["errors"] += 1
                        continue  # satır hatası varsa devam
    
                session.commit()
    
            status["message"] = (
                f"Kayıt tamamlandı. {status['inserted']} yeni kayıt eklendi, "
                f"{status['updated']} kayıt güncellendi, {status['errors']} satırda hata oluştu."
            )
    
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Veritabanı hatası: {str(e)}"
            })
    
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
                            giris_saat = self.parse_time(row['giris_saat']),
                            cikis_saat = self.parse_time(row['cikis_saat']),
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
                        print(f"Uyarı: {row['ders_ogretmeni']} veritabanında bulunamadı.")
                    
        
                session.commit()
                status["message"] = (f"Kayıt Başarılı {status['record_count']} tane ders dağılımı kayıt edildi")
                
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
            # Log the error here if needed
        
        return status