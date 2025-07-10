#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 14 21:38:07 2025

@author: senolirmak
"""

from nobet.db.models import (NobetGorevi, NobetOgretmen,
                             NobetDersProgrami, NobetGecmisi, NobetAtanamayan)
from sqlalchemy import select, and_, exists
from contextlib import contextmanager
from nobet.db.database import SessionLocal
from datetime import date, datetime
from typing import Dict, Optional

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
                (NobetDersProgrami.ders_ogretmeni_id == teacher_id)
            )
            programs = session.execute(stmt).scalars().all()
            return {"ogretmen_id":teacher_id,'dersleri':{program.ders_saati: program.subeadi for program in programs}}

    def get_ogretmen_for_day(self, day):
        """Get all teachers scheduled for a specific day (without nobeti_var check)"""
        with self.get_db_session() as session:
            stmt = select(NobetOgretmen).where(
                exists().where(
                    and_(
                        NobetDersProgrami.ders_ogretmeni_id == NobetOgretmen.id,
                        NobetDersProgrami.gun == day
                    )
                )
            )
            teachers = session.execute(stmt).scalars().all()
            return {t.id: f"{t.adi_soyadi} ({t.brans})" for t in teachers}

    def get_duty_teachers(self, day):
        """Get teachers assigned to duty for a specific day"""
        with self.get_db_session() as session:
            stmt = select(NobetGorevi, NobetOgretmen).join(
                NobetOgretmen, NobetGorevi.nobetci_ogretmen_id == NobetOgretmen.id
            ).where(NobetGorevi.nobet_gun == day)
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
        