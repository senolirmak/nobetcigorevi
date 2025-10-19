#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 14 21:38:07 2025

@author: senolirmak
"""

from nobetcigorevi.db.models import (NobetGorevi, NobetOgretmen,NobetPersonel,
                             NobetDersProgrami, NobetGecmisi, NobetAtanamayan,
                             Base)
from sqlalchemy import select, and_, exists
from contextlib import contextmanager
from nobetcigorevi.db.database import SessionLocal, engine
from datetime import date, datetime
from typing import Dict, Optional

import pandas as pd

class DatabaseManager:
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

    def get_ogretmen_by_id(self, teacher_id):
        """Get teacher by ID"""
        with self.get_db_session() as session:
            return session.get(NobetOgretmen, teacher_id)

    def get_ogretmen_schedule(self, teacher_id, day):
        """Get teacher's schedule for a specific day"""
        with self.get_db_session() as session:
            stmt = select(NobetDersProgrami).where(
                (NobetDersProgrami.gun == day) &
                (NobetDersProgrami.ogretmen_id == teacher_id)
            )
            programs = session.execute(stmt).scalars().all()
            return {"ogretmen_id":teacher_id,'dersleri':{program.ders_saati: program.subeadi for program in programs}}

    def get_ogretmen_for_day(self, day):
        """Get all teachers scheduled for a specific day (without nobeti_var check)"""
        with self.get_db_session() as session:
            stmt = select(NobetOgretmen).where(
                exists().where(
                    and_(
                        NobetDersProgrami.ogretmen_id == NobetOgretmen.id,
                        NobetDersProgrami.gun == day
                    )
                )
            )
            teachers = session.execute(stmt).scalars().all()
            return {t.id: f"{t.adi_soyadi} ({t.brans})" for t in teachers}

    def get_duty_teachers(self, day):
        """Get teachers assigned to duty for a specific day"""
        with self.get_db_session() as session:
            stmt = (
                select(NobetGorevi, NobetOgretmen)
                .join(NobetOgretmen, NobetGorevi.ogretmen_id == NobetOgretmen.id)
                .where(NobetGorevi.nobet_gun == day)
            )
            results = session.execute(stmt).all()
            return [(nobet_gorevi, ogretmen) for nobet_gorevi, ogretmen in results]
    
    def save_results_NobetGecmisi(
        self,
        substitution_data: Dict,
        substitution_date: Optional[date] = None) -> Dict[str, str]:

        if substitution_date is None:
            substitution_date = datetime.now()

        status = {
            "assigned_count": 0,
            "status": "success",
            "message": ""
        }

        try:
            with self.get_db_session() as session:
                # Save assigned substitutions
                for assignment in substitution_data.get('assignments', []):
                    record = NobetGecmisi(
                        saat=assignment['hour'],
                        sinif=assignment['class'],
                        devamsiz=assignment['absent_teacher_id'],
                        nobetgecmisi_ogretmen_id=assignment['teacher_id'],
                        atandi=1,
                        tarih=substitution_date
                    )
                    session.add(record)
                    status["assigned_count"] += 1

                session.commit()
                status["message"] = (f"Successfully saved {status['assigned_count']} assignments records")
                
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
            # Log the error here if needed
        
        return status
    
    def save_results_NobetAtanamayan(
        self,
        substitution_data: Dict,
        substitution_date: Optional[date] = None) -> Dict[str, str]:

        if substitution_date is None:
            substitution_date = datetime.now()

        status = {
            "unassigned_count": 0,
            "status": "success",
            "message": ""
        }

        try:
            with self.get_db_session() as session:
                # Save unassigned substitutions
                for unassigned in substitution_data.get('unassigned', []):
                    record = NobetAtanamayan(
                        saat=unassigned['hour'],
                        sinif=unassigned['class'],
                        devamsiz=unassigned['absent_teacher_id'],
                        atandi=0,
                        tarih=substitution_date
                    )
                    session.add(record)
                    status["unassigned_count"] += 1

                session.commit()
                status["message"] = (f"Successfully saved  {status['unassigned_count']} unassigned records")
                
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
            # Log the error here if needed
        
        return status


class TeacherManager(DatabaseManager):
    """Handles teacher-specific operations, inheriting from DatabaseManager"""
    def __init__(self):
        super().__init__()
        self.teacher_id_to_name = {}

    def get_ogretmen(self,teacher_id):
        teacher = self.get_ogretmen_by_id(teacher_id)
        if teacher_id not in self.teacher_id_to_name:
            if teacher:
                self.teacher_id_to_name[teacher_id] = teacher.adi_soyadi
        return teacher

    def get_ogretmen_adi(self, teacher_id):
        """Get teacher's name by ID with caching"""
        if teacher_id not in self.teacher_id_to_name:
            teacher = self.get_ogretmen_by_id(teacher_id)
            if teacher:
                self.teacher_id_to_name[teacher_id] = teacher.adi_soyadi
        return self.teacher_id_to_name.get(teacher_id, "Unknown Teacher")

    def get_ogretmen_programi(self, teacher_id, day, ayrinti=False):
        #Get formatted schedule summary for a teacher
        schedule = self.get_ogretmen_schedule(teacher_id, day)
        if ayrinti:
            teacher = self.get_ogretmen_by_id(teacher_id)
            teacher_data = {
                    #'ogretmen_id': teacher.id,
                    'adi_soyadi': teacher.adi_soyadi,
                    'brans': teacher.brans,
                    #'dersler': schedule['dersler']
            }
            schedule.update(teacher_data)
            return schedule
            
        return schedule

    def get_gunun_nobetcileri(self, day):
        nobetciler = self.get_duty_teachers(day)
        return nobetciler
    
    def get_gunun_ogretmenleri(self, day):
        teachers = self.get_ogretmen_for_day(day)
        return teachers
    
    def data_save_NobetGecmisi(self, sonuc):
        status = self.save_results_NobetGecmisi(sonuc)
        return status
    
    def data_sava_NobetAtanamayan(self,sonuc):
        status = self.save_results_NobetAtanamayan(sonuc)
        return status

class EOkulVeriAktar:
    def __init__(self):
        # Veritabanı şeması yoksa otomatik oluştur
        Base.metadata.create_all(bind=engine)

    @contextmanager
    def get_db_session(self):
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

    # ------------------ PERSONEL ------------------
    def save_yeni_veri_NobetPersonel(self, personel_df):
        status = {"inserted": 0, "updated": 0, "errors": 0, "status": "success", "message": ""}
        required_columns = ['adisoyadi', 'brans', 'kimlikno', 'gorev']
        missing = [col for col in required_columns if col not in personel_df.columns]
        if missing:
            return {"status": "error", "message": f"Eksik sütun(lar): {', '.join(missing)}", **status}

        personel_df = personel_df.dropna(subset=['adisoyadi', 'brans', 'kimlikno'])
        try:
            with self.get_db_session() as session:
                for _, row in personel_df.iterrows():
                    try:
                        result = self.insert_or_update(
                            session, NobetPersonel,
                            {"kimlikno": str(row["kimlikno"])},
                            {"adi_soyadi": row["adisoyadi"], "brans": row["brans"], "gorev_tipi": row["gorev"]}
                        )
                        status[result] += 1
                    except Exception:
                        status["errors"] += 1
                session.commit()
            status["message"] = f"{status['inserted']} eklendi, {status['updated']} güncellendi, {status['errors']} hata."
        except Exception as e:
            status.update({"status": "error", "message": f"Veritabanı hatası: {str(e)}"})
        return status

    # ------------------ ÖĞRETMEN ------------------
    def save_yeni_veri_NobetOgretmen(self, personel_df):
        status = {"inserted": 0, "updated": 0, "errors": 0, "status": "success", "message": ""}
        required_columns = ['adi_soyadi', 'brans', 'nobeti_var', 'gorev_tipi']
        missing = [col for col in required_columns if col not in personel_df.columns]
        if missing:
            return {"status": "error", "message": f"Eksik sütun(lar): {', '.join(missing)}", **status}

        personel_df = personel_df.dropna(subset=['adi_soyadi', 'brans', 'nobeti_var'])
        try:
            with self.get_db_session() as session:
                for _, row in personel_df.iterrows():
                    try:
                        result = self.insert_or_update(
                            session, NobetOgretmen,
                            {"adi_soyadi": row["adi_soyadi"], "brans": row["brans"]},
                            {
                                "adi_soyadi": row["adi_soyadi"],
                                "brans": row["brans"],
                                "nobeti_var": bool(row["nobeti_var"]),
                                "gorev_tipi": row["gorev_tipi"]
                            }
                        )
                        status[result] += 1
                    except Exception:
                        status["errors"] += 1
                session.commit()
            status["message"] = f"{status['inserted']} eklendi, {status['updated']} güncellendi, {status['errors']} hata."
        except Exception as e:
            status.update({"status": "error", "message": f"Veritabanı hatası: {str(e)}"})
        return status

    # ------------------ NÖBET GÖREVİ ------------------
    def save_yeni_veri_NobetGorevi(self, nobet_df):
        nobet_df = nobet_df.dropna(subset=['nobetci'])
        status = {"record_count": 0, "status": "success", "message": ""}
        try:
            with self.get_db_session() as session:
                for _, row in nobet_df.iterrows():
                    ogretmen = session.query(NobetOgretmen).filter_by(adi_soyadi=row['nobetci']).first()
                    if ogretmen:
                        nobet = NobetGorevi(
                            nobet_gun=row['nobet_gun'],
                            nobet_yeri=row['nobet_yeri'],
                            ogretmen_id=ogretmen.id,
                            uygulama_tarihi=pd.to_datetime(row['uygulama_tarihi']).date(),
                        )
                        session.add(nobet)
                        status["record_count"] += 1
                    else:
                        print(f"⚠️ {row['nobetci']} veritabanında bulunamadı.")
                session.commit()
                status["message"] = f"{status['record_count']} nöbet kaydı eklendi."
        except Exception as e:
            status.update({"status": "error", "message": f"Database error: {str(e)}"})
        return status

    # ------------------ DERS PROGRAMI ------------------
    def save_yeni_veri_NobetDersProgrami(self, program_df):
        program_df = program_df.dropna(subset=['ders_ogretmeni'])
        status = {"record_count": 0, "status": "success", "message": ""}
        try:
            with self.get_db_session() as session:
                for _, row in program_df.iterrows():
                    ogretmen = session.query(NobetOgretmen).filter_by(adi_soyadi=row['ders_ogretmeni']).first()
                    if ogretmen:
                        program = NobetDersProgrami(
                            gun=row['gun'],
                            giris_saat=self.parse_time(row['giris_saat']),
                            cikis_saat=self.parse_time(row['cikis_saat']),
                            ders_adi=row['ders_adi'],
                            sinif=row['sinif'],
                            sube=row['sube'],
                            subeadi = row['subeadi'],
                            ders_saati=int(row['ders_saati']),
                            uygulama_tarihi=pd.to_datetime(row['uygulama_tarihi']).date(),
                            ogretmen_id=ogretmen.id  # ✅ artık doğru sütun
                        )
                        session.add(program)
                        status["record_count"] += 1
                    else:
                        print(f"⚠️ {row['ders_ogretmeni']} veritabanında bulunamadı.")
                session.commit()
                status["message"] = f"{status['record_count']} ders programı eklendi."
        except Exception as e:
            status.update({"status": "error", "message": f"Database error: {str(e)}"})
        return status