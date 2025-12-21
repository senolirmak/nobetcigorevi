#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 14 21:38:07 2025

@author: senolirmak
"""

from db.models import (NobetGorevi, NobetOgretmen,NobetPersonel,
                             NobetDersProgrami, NobetGecmisi, NobetAtanamayan,
                             Base, NobetIstatistik)
from sqlalchemy import select, and_, exists, func, desc
from contextlib import contextmanager
from db.database import SessionLocal, engine
from datetime import date, datetime
from typing import Dict, Optional
from PyQt5.QtWidgets import QMessageBox
          

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
            
    def get_son_uygulama_tarihi(self):
        """
        NobetDersProgrami tablosundaki en son (en yeni) uygulama tarihini döndürür.
        Eğer veri yoksa None döner.
        """    
        with self.get_db_session() as session:
            result = session.query(func.max(NobetDersProgrami.uygulama_tarihi)).scalar()
            return result
        
    # ---------------------------------------------------------------------
    # 1️⃣ En güncel tarih bulucu
    # ---------------------------------------------------------------------
    def get_latest_date(self, model_class, date_column="uygulama_tarihi"):
        """İlgili modeldeki en son tarih değerini döndürür"""
        with self.get_db_session() as session:
            result = (
                session.query(getattr(model_class, date_column))
                .order_by(getattr(model_class, date_column).desc())
                .first()
            )
            return result[0] if result else None

    def get_ogretmen_by_id_old(self, teacher_id):
        """Get teacher by ID"""
        with self.get_db_session() as session:
            return session.get(NobetOgretmen, teacher_id)
        
    def get_ogretmen_by_id(self, teacher_id):
        """
        ID ile öğretmeni getirir.
        - Öncelikle, öğretmen son uygulama tarihindeki verilerde geçiyor mu kontrol eder.
        - Eğer o tarihte geçmiyorsa, temel NobetOgretmen tablosundan döner.
        """
        with self.get_db_session() as session:
            try:
                # 🔹 Önce en güncel uygulama tarihini bul
                latest_program_date = self.get_latest_date(NobetDersProgrami)
                latest_duty_date = self.get_latest_date(NobetGorevi)
    
                # 🔹 En güncel tarihlerden biri varsa, öğretmen o tarihte aktif mi kontrol et
                if latest_program_date:
                    exists_in_program = session.query(NobetDersProgrami).filter(
                        NobetDersProgrami.ogretmen_id == teacher_id,
                        NobetDersProgrami.uygulama_tarihi == latest_program_date
                    ).first()
                    if exists_in_program:
                        return session.get(NobetOgretmen, teacher_id)
    
                if latest_duty_date:
                    exists_in_duty = session.query(NobetGorevi).filter(
                        NobetGorevi.ogretmen_id == teacher_id,
                        NobetGorevi.uygulama_tarihi == latest_duty_date
                    ).first()
                    if exists_in_duty:
                        return session.get(NobetOgretmen, teacher_id)
    
                # 🔹 Eğer öğretmen o tarihlerde görünmüyorsa, yine de temel tablodan getir
                teacher = session.get(NobetOgretmen, teacher_id)
                return teacher
    
            except Exception as e:
                print(f"⚠️ get_ogretmen_by_id hata: {e}")
                return None

    def get_ogretmen_schedule(self, teacher_id, day):
        """Get teacher's schedule for a specific day"""
        with self.get_db_session() as session:
            latest_date = self.get_latest_date(NobetDersProgrami)
            if not latest_date:
                return {"ogretmen_id": teacher_id, "dersleri": {}}
            
            stmt = select(NobetDersProgrami).where(
                and_(
                    NobetDersProgrami.gun == day,
                    NobetDersProgrami.ogretmen_id == teacher_id,
                    NobetDersProgrami.uygulama_tarihi == latest_date
                )
            )
            programs = session.execute(stmt).scalars().all()
            return {"ogretmen_id":teacher_id,'dersleri':{program.ders_saati: program.subeadi for program in programs}}

    def get_duty_teachers_yer(self, teacher_id):
        """Belirtilen öğretmenin en son nöbet yerini döndürür."""
        with self.get_db_session() as session:
            # 🔸 En son nöbet tarihini bul
            latest_date = self.get_latest_date(NobetGorevi)
            if not latest_date:
                return None
    
            # 🔸 Son nöbet kaydını sorgula
            record = (
                session.query(NobetGorevi.nobet_yeri)
                .filter(
                    NobetGorevi.ogretmen_id == teacher_id,
                    NobetGorevi.uygulama_tarihi == latest_date
                )
                .order_by(NobetGorevi.uygulama_tarihi.desc())
                .scalar()
            )
    
            # 🔸 Sadece nöbet_yeri değerini döndür
            return record or "Bilinmiyor"


    def get_ogretmen_for_day(self, day):
        """Get all teachers scheduled for a specific day (without nobeti_var check)"""
        with self.get_db_session() as session:
            latest_date = self.get_latest_date(NobetDersProgrami)
            if not latest_date:
                return {}
            stmt = (
                select(NobetOgretmen)
                .join(NobetDersProgrami, NobetDersProgrami.ogretmen_id == NobetOgretmen.id)
                .where(
                    and_(
                        NobetDersProgrami.gun == day,
                        NobetDersProgrami.uygulama_tarihi == latest_date
                    )
                )
                .distinct()
            )
            teachers = session.execute(stmt).scalars().all()
            return {t.id: f"{t.adi_soyadi} ({t.brans})" for t in teachers}

    def get_duty_teachers(self, day):
        """Get teachers assigned to duty for a specific day"""
        with self.get_db_session() as session:
            latest_date = self.get_latest_date(NobetGorevi)
            if not latest_date:
                return []

            stmt = (
                select(NobetGorevi, NobetOgretmen)
                .join(NobetOgretmen, NobetGorevi.ogretmen_id == NobetOgretmen.id)
                .where(
                    and_(
                        NobetGorevi.nobet_gun == day,
                        NobetGorevi.uygulama_tarihi == latest_date
                    )
                )
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
                        ogretmen_id=assignment['teacher_id'],
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
                        ogretmen_id=unassigned['absent_teacher_id'],
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

    # -------------------------------------------------
    # 🔹 Nöbet istatistiği hesaplama fonksiyonu
    # -------------------------------------------------
    def calculate_teacher_stats(self, session, ogretmen_id):
        """
        Verilen öğretmen için NobetIstatistik tablosuna uygun
        haftalık ortalama, toplam nöbet sayısı ve diğer verileri hesaplar.
        """
        # 🔸 1. Toplam nöbet sayısı
        toplam_nobet = (
            session.query(func.count())
            .select_from(NobetGecmisi)
            .filter(NobetGecmisi.ogretmen_id == ogretmen_id, NobetGecmisi.atandi == 1)
            .scalar()
        ) or 0
        
        # 🔸 2. Son nöbet tarihi ve nöbet yeri
        son_kayit = (
            session.query(NobetGecmisi)
            .filter(NobetGecmisi.ogretmen_id == ogretmen_id, NobetGecmisi.atandi == 1)
            .order_by(NobetGecmisi.tarih.desc())
            .first()
        )
        
        son_nobet_tarihi = son_kayit.tarih if son_kayit else None
        son_nobet_yeri = None
        
        # 🔸 NobetGorevi üzerinden nöbet yeri (son tarih eşleşmesi)
        if son_kayit:
            gorev_yeri = self.get_duty_teachers_yer(ogretmen_id)
            son_nobet_yeri = gorev_yeri or "Bilinmiyor"
        
        # 🔸 3. Hafta sayısı (ilk ve son nöbet arasındaki fark)
        ilk_nobet_tarihi = (
            session.query(func.min(NobetGecmisi.tarih))
            .filter(NobetGecmisi.ogretmen_id == ogretmen_id)
            .scalar()
        )
        hafta_sayisi = 0
        if ilk_nobet_tarihi and son_nobet_tarihi:
            delta_days = (son_nobet_tarihi - ilk_nobet_tarihi).days
            hafta_sayisi = max(1, delta_days // 7)
        
        # 🔸 4. Haftalık ortalama nöbet (toplam / hafta sayısı)
        haftalik_ortalama = round(toplam_nobet / hafta_sayisi, 2) if hafta_sayisi else 0.0
        
        # 🔸 5. Ağırlıklı puan (örnek formül: az nöbet yapanın puanı yüksek)
        agirlikli_puan = round(1 / (1 + haftalik_ortalama), 3) if haftalik_ortalama else 1.0
        
        return {
            "toplam_nobet": toplam_nobet,
            "haftalik_ortalama": haftalik_ortalama,
            "hafta_sayisi": hafta_sayisi,
            "agirlikli_puan": agirlikli_puan,
            "son_nobet_tarihi": son_nobet_tarihi,
            "son_nobet_yeri": son_nobet_yeri,
        }
            

    # -------------------------------------------------
    # 🔹 Kayıt/Güncelleme fonksiyonu
    # -------------------------------------------------
    def update_nobet_istatistik(self, ogretmen_id):
        """Verilen öğretmen için istatistik kaydını günceller veya oluşturur."""
        with self.get_db_session() as session:
            try:
                teacher = session.get(NobetOgretmen, ogretmen_id)
                if not teacher:
                    return {"status": "error", "message": f"Öğretmen (ID={ogretmen_id}) bulunamadı."}

                # Yeni hesaplama
                stats = self.calculate_teacher_stats(session, ogretmen_id)
                
                # Var olan kayıt var mı?
                record = session.scalar(
                    select(NobetIstatistik).where(NobetIstatistik.ogretmen_id == ogretmen_id)
                )

                if record:
                    record.toplam_nobet = stats["toplam_nobet"]
                    record.haftalik_ortalama = stats["haftalik_ortalama"]
                    record.hafta_sayisi = stats["hafta_sayisi"]
                    record.agirlikli_puan = stats["agirlikli_puan"]
                    record.son_nobet_tarihi = stats["son_nobet_tarihi"]
                    record.son_nobet_yeri = stats["son_nobet_yeri"]
                    action = "updated"
                else:
                    new_record = NobetIstatistik(
                        ogretmen_id=ogretmen_id,
                        toplam_nobet=stats["toplam_nobet"],
                        haftalik_ortalama=stats["haftalik_ortalama"],
                        hafta_sayisi=stats["hafta_sayisi"],
                        agirlikli_puan=stats["agirlikli_puan"],
                        son_nobet_tarihi=stats["son_nobet_tarihi"],
                        son_nobet_yeri=stats["son_nobet_yeri"],
                    )
                    session.add(new_record)
                    action = "inserted"

                session.commit()
                return {
                    "status": "success",
                    "action": action,
                    "message": f"Nöbet istatistiği {action} (öğretmen ID={ogretmen_id}).",
                    **stats,
                }

            except Exception as e:
                session.rollback()
                return {"status": "error", "message": f"Database error: {str(e)}"}

    # -------------------------------------------------
    # 🔹 Atama yapılan nöbetçilerin istatistiklerini güncelle
    # -------------------------------------------------
    def update_all_istatistik(self, sonuc):
        """
        Yeni yapılan dağıtımdaki öğretmenlerin istatistiklerini günceller.
        Parametre:
            sonuc (dict): 'assignments' anahtarını içeren, her atamanın
                          'teacher_id' bilgisini barındıran dağıtım sonucu.
        """
        if not sonuc or "assignments" not in sonuc:
            return {"status": "error", "message": "Güncellenecek atama bulunamadı."}

        from sqlalchemy import select

        with self.get_db_session() as session:
            try:
                # 🔸 Dağıtım sonucundan benzersiz öğretmen ID’lerini çıkar
                assigned_teacher_ids = {a["teacher_id"] for a in sonuc["assignments"] if a.get("teacher_id")}
                if not assigned_teacher_ids:
                    return {"status": "error", "message": "Atama yapılan öğretmen bulunamadı."}

                updated = 0
                for teacher_id in assigned_teacher_ids:
                    # 🔸 Her öğretmen için yeniden hesapla
                    stats = self.calculate_teacher_stats(session, teacher_id)

                    # 🔸 Mevcut kayıt var mı?
                    record = session.scalar(
                        select(NobetIstatistik).where(NobetIstatistik.ogretmen_id == teacher_id)
                    )

                    if record:
                        record.toplam_nobet = stats["toplam_nobet"]
                        record.haftalik_ortalama = stats["haftalik_ortalama"]
                        record.hafta_sayisi = stats["hafta_sayisi"]
                        record.agirlikli_puan = stats["agirlikli_puan"]
                        record.son_nobet_tarihi = stats["son_nobet_tarihi"]
                        record.son_nobet_yeri = stats["son_nobet_yeri"]
                    else:
                        new_record = NobetIstatistik(
                            ogretmen_id=teacher_id,
                            toplam_nobet=stats["toplam_nobet"],
                            haftalik_ortalama=stats["haftalik_ortalama"],
                            hafta_sayisi=stats["hafta_sayisi"],
                            agirlikli_puan=stats["agirlikli_puan"],
                            son_nobet_tarihi=stats["son_nobet_tarihi"],
                            son_nobet_yeri=stats["son_nobet_yeri"],
                        )
                        session.add(new_record)

                    updated += 1

                session.commit()
                return {
                    "status": "success",
                    "message": f"{updated} öğretmenin istatistiği güncellendi.",
                    "updated_count": updated
                }

            except Exception as e:
                session.rollback()
                return {"status": "error", "message": f"İstatistik güncelleme hatası: {str(e)}"}

    # -------------------------------------------------
    # Son istatistik kaydını getir
    # -------------------------------------------------
    def get_nobet_istatistik(self, ogretmen_id):
        """Belirtilen öğretmenin istatistik kaydını döndürür."""
        from sqlalchemy import select
        with self.get_db_session() as session:
            stmt = select(NobetIstatistik).where(NobetIstatistik.ogretmen_id == ogretmen_id)
            record = session.scalars(stmt).first()
            return record

    # -------------------------------------------------
    # Tüm öğretmenlerin istatistiklerini getir
    # -------------------------------------------------
    def get_all_nobet_istatistik(self):
        """Tüm öğretmenlerin nöbet istatistiklerini döndürür."""
        from sqlalchemy import select
        with self.get_db_session() as session:
            stmt = select(NobetIstatistik)
            return session.scalars(stmt).all()    

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
    
    def get_ogretmen_id(self, adi_soyadi: str):
        """
        Verilen öğretmen ad-soyadına göre öğretmen ID'sini döndürür.
        Eğer öğretmen bulunamazsa None döner.
        """
        with self.get_db_session() as session:
            from db.models import NobetOgretmen
            result = session.query(NobetOgretmen.id).filter(
                NobetOgretmen.adi_soyadi == adi_soyadi
            ).first()
            if result:
                return result[0]
            return None

    
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

    def get_nobet_yeri(self, teacher_id: int, day: str, uygulama_tarihi=None) -> str:
        """
        Verilen öğretmenin, verilen gün için (opsiyonel) uygulama_tarihi'ne en uygun
        nöbet yerini döndürür. Bulunamazsa None döner.
        """
        with self.get_db_session() as session:
            q = session.query(NobetGorevi.nobet_yeri)\
                       .filter(NobetGorevi.ogretmen_id == teacher_id,
                               NobetGorevi.nobet_gun == day)

            # Uygulama tarihi verilmişse aynı güne en yakın kaydı al
            if uygulama_tarihi is not None:
                # sadece tarih kısmına göre eşleştir (saat oynamaları sorun çıkarmasın)
                q = q.filter(func.date(NobetGorevi.uygulama_tarihi) == func.date(uygulama_tarihi))

            # Yoksa en güncel kaydı çek
            q = q.order_by(desc(NobetGorevi.uygulama_tarihi))

            row = q.first()
            return row[0] if row else None

    def get_gunun_nobetcileri(self, day):
        nobetciler = self.get_duty_teachers(day)
        return nobetciler
    
    def get_gunun_ogretmenleri(self, day):
        teachers = self.get_ogretmen_for_day(day)
        return teachers
    
    def data_save_NobetGecmisi(self, sonuc):
        status = self.save_results_NobetGecmisi(sonuc)
        return status
    
    def data_save_NobetAtanamayan(self,sonuc):
        status = self.save_results_NobetAtanamayan(sonuc)
        return status
    def istatistik_save_NobetIstatistik(self, sonuc):
        status = self.update_all_istatistik(sonuc)
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
        required_columns = ['adisoyadi', 'brans', 'kimlikno', 'gorev', 'cinsiyet']
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
                            {"adi_soyadi": row["adisoyadi"], "brans": row["brans"], "gorev_tipi": row["gorev"],"cinsiyet":row["cinsiyet"]}
                        )
                        status[result] += 1
                    except Exception:
                        status["errors"] += 1
                session.commit()
            status["message"] = f"Personel: {status['inserted']} eklendi, {status['updated']} güncellendi, {status['errors']} hata."
        except Exception as e:
            status.update({"status": "error", "message": f"Veritabanı hatası: {str(e)}"})
        return status

    # ------------------ ÖĞRETMEN ------------------
    def save_yeni_veri_NobetOgretmen(self, personel_df):
        """
        Öğretmen kayıtlarını veritabanına ekler veya günceller.
        Aynı adi_soyadi + brans + gorev_tipi + uygulama_tarihi kombinasyonu varsa update eder.
        """
        status = {
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "status": "success",
            "message": ""
        }
    
        required_columns = ['adi_soyadi', 'brans', 'nobeti_var', 'gorev_tipi', 'uygulama_tarihi','cinsiyet']
        missing = [col for col in required_columns if col not in personel_df.columns]
        if missing:
            return {
                "status": "error",
                "message": f"Eksik sütun(lar): {', '.join(missing)}",
                **status
            }
    
        # Temizlik
        personel_df = personel_df.dropna(subset=['adi_soyadi', 'brans', 'nobeti_var'])
        personel_df['adi_soyadi'] = personel_df['adi_soyadi'].astype(str).str.strip()
        personel_df['brans'] = personel_df['brans'].astype(str).str.strip()
        personel_df['gorev_tipi'] = personel_df['gorev_tipi'].astype(str).str.strip()
    
        try:
            with self.get_db_session() as session:
                for _, row in personel_df.iterrows():
                    try:
                        # 🔹 nobeti_var normalize et
                        nobeti_var_raw = str(row["nobeti_var"]).strip().lower()
                        if nobeti_var_raw in ["0", "false", "hayır", "no"]:
                            nobeti_var = False
                        else:
                            nobeti_var = True
    
                        # Tarihi normalize et (saat kısmını sıfırla)
                        uygulama_tarihi = pd.to_datetime(row["uygulama_tarihi"]).replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        
                        """
                        if pd.isna(uygulama_tarihi):
                            uygulama_tarihi = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        else:
                            uygulama_tarihi = uygulama_tarihi.replace(hour=0, minute=0, second=0, microsecond=0)
                        """
                        
                        # 🔍 Aynı öğretmen, branş, görev tipi ve tarih varsa update et
                        existing = session.query(NobetOgretmen).filter_by(
                            adi_soyadi=row["adi_soyadi"],
                            brans=row["brans"],
                            gorev_tipi=row["gorev_tipi"],
                            cinsiyet=row["cinsiyet"],
                        ).first()
    
                        if existing:
                            # 🔁 Güncelleme (yalnızca tarih farkı yoksa)
                            existing.nobeti_var = nobeti_var
                            status["updated"] += 1
                        else:
                            # ➕ Yeni kayıt
                            yeni = NobetOgretmen(
                                adi_soyadi=row["adi_soyadi"],
                                brans=row["brans"],
                                nobeti_var=nobeti_var,
                                gorev_tipi=row["gorev_tipi"],
                                uygulama_tarihi = uygulama_tarihi,
                                cinsiyet =row["cinsiyet"]
                            )
                            session.add(yeni)
                            status["inserted"] += 1
    
                    except Exception as row_err:
                        print(f"⚠️ Satır hatası ({row.get('adi_soyadi', '???')}): {row_err}")
                        status["errors"] += 1
                        continue
    
                session.commit()
    
            status["message"] = (
                f"Öğretmen: {status['inserted']} eklendi, "
                f"{status['updated']} güncellendi, "
                f"{status['errors']} hata oluştu."
            )
    
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Veritabanı hatası: {str(e)}"
            })
    
        return status

    # ------------------ NÖBET GÖREVİ ------------------
    def save_yeni_veri_NobetGorevi(self, nobet_df):
        """
        Aynı öğretmen ve aynı uygulama_tarihi için kayıt varsa update eder,
        yoksa yeni kayıt oluşturur.
        """
        nobet_df = nobet_df.dropna(subset=['nobetci'])
        status = {
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "status": "success",
            "message": ""
        }

        try:
            with self.get_db_session() as session:
                for _, row in nobet_df.iterrows():
                    try:
                        ogretmen = session.query(NobetOgretmen).filter_by(
                            adi_soyadi=row['nobetci']
                        ).first()

                        if not ogretmen:
                            print(f"⚠️ {row['nobetci']} veritabanında bulunamadı.")
                            status["errors"] += 1
                            continue

                        # Tarihi normalize et (saat kısmını sıfırla)
                        uygulama_tarihi = pd.to_datetime(row["uygulama_tarihi"]).replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )

                        # 🔍 Aynı öğretmen + tarih kombinasyonu var mı?
                        existing_record = session.query(NobetGorevi).filter(
                            NobetGorevi.ogretmen_id == ogretmen.id,
                            NobetGorevi.uygulama_tarihi == uygulama_tarihi
                        ).first()

                        if existing_record:
                            # Güncelleme yap
                            existing_record.nobet_gun = row["nobet_gun"]
                            existing_record.nobet_yeri = row["nobet_yeri"]
                            status["updated"] += 1
                        else:
                            # Yeni kayıt ekle
                            yeni_nobet = NobetGorevi(
                                nobet_gun=row["nobet_gun"],
                                nobet_yeri=row["nobet_yeri"],
                                ogretmen_id=ogretmen.id,
                                uygulama_tarihi=uygulama_tarihi
                            )
                            session.add(yeni_nobet)
                            status["inserted"] += 1

                    except Exception as row_error:
                        print(f"⚠️ Satır hatası: {row_error} -> {row}")
                        status["errors"] += 1
                        continue

                # 💾 Commit işlemi
                session.commit()

            status["message"] = (
                f"Nöbet: {status['inserted']} eklendi, {status['updated']} güncellendi, {status['errors']} hata oluştu."
            )

        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })

        return status


    # ------------------ DERS PROGRAMI ------------------
    def save_yeni_veri_NobetDersProgrami(self, program_df):
        """
        Ders programı kayıtlarını veritabanına ekler veya günceller.
        Aynı öğretmen + gün + ders_saati + uygulama_tarihi kombinasyonu varsa update eder.
        Aksi halde yeni kayıt oluşturur.
        """
        program_df = program_df.dropna(subset=['ders_ogretmeni'])
        status = {
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "status": "success",
            "message": ""
        }
    
        try:
            with self.get_db_session() as session:
                for _, row in program_df.iterrows():
                    try:
                        # 🔹 Öğretmeni bul
                        ogretmen = session.query(NobetOgretmen).filter_by(
                            adi_soyadi=row['ders_ogretmeni']
                        ).first()
    
                        if not ogretmen:
                            print(f"⚠️ {row['ders_ogretmeni']} veritabanında bulunamadı.")
                            status["errors"] += 1
                            continue
    
                        # 🔹 Tarih normalize et
                        uygulama_tarihi = pd.to_datetime(row["uygulama_tarihi"], errors="coerce")
                        if pd.isna(uygulama_tarihi):
                            uygulama_tarihi = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        else:
                            uygulama_tarihi = uygulama_tarihi.replace(hour=0, minute=0, second=0, microsecond=0)
    
                        # 🔹 Aynı öğretmen, gün, ders saati ve uygulama_tarihi var mı kontrol et
                        existing = session.query(NobetDersProgrami).filter(
                            NobetDersProgrami.ogretmen_id == ogretmen.id,
                            NobetDersProgrami.gun == row['gun'],
                            NobetDersProgrami.ders_saati == int(row['ders_saati']),
                            NobetDersProgrami.uygulama_tarihi == uygulama_tarihi
                        ).first()
    
                        if existing:
                            # 🔁 Güncelleme
                            existing.ders_adi = row['ders_adi']
                            existing.sinif = row['sinif']
                            existing.sube = row['sube']
                            existing.subeadi = row['subeadi']
                            existing.giris_saat = self.parse_time(row['giris_saat'])
                            existing.cikis_saat = self.parse_time(row['cikis_saat'])
                            status["updated"] += 1
                        else:
                            # ➕ Yeni kayıt
                            yeni = NobetDersProgrami(
                                gun=row['gun'],
                                giris_saat=self.parse_time(row['giris_saat']),
                                cikis_saat=self.parse_time(row['cikis_saat']),
                                ders_adi=row['ders_adi'],
                                sinif=row['sinif'],
                                sube=row['sube'],
                                subeadi=row['subeadi'],
                                ders_saati=int(row['ders_saati']),
                                uygulama_tarihi=uygulama_tarihi,
                                ogretmen_id=ogretmen.id
                            )
                            session.add(yeni)
                            status["inserted"] += 1
    
                    except Exception as row_err:
                        print(f"⚠️ Satır hatası ({row.get('ders_ogretmeni', '???')}): {row_err}")
                        status["errors"] += 1
                        continue
    
                session.commit()
    
            status["message"] = (
                f"Ders programı: {status['inserted']} eklendi, "
                f"{status['updated']} güncellendi, "
                f"{status['errors']} hata oluştu."
            )
    
        except Exception as e:
            status.update({
                "status": "error",
                "message": f"Database error: {str(e)}"
            })
    
        return status
