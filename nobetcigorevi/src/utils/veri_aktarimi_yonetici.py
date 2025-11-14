#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  8 22:29:26 2025

@author: senolirmak

Veri aktarımı yöneticisi:
Düzenlenmiş Excel dosyalarını SQL veritabanına kaydeder.
@author: Ş.
"""

import os
import pandas as pd
from datetime import datetime
from utils.database_util import EOkulVeriAktar


class VeriAktarimiYonetici:
    """
    e-Okul verilerini (Personel, Öğretmen, Nöbet, Ders Programı)
    Excel dosyalarından okuyup SQL veritabanına kaydeden yardımcı sınıf.
    """

    def __init__(self, base_path="nobetcigorevi/"):
        self.base_path = base_path
        self.uygulama_tarihi = datetime.now().replace(microsecond=0)
        self.veri_aktar = EOkulVeriAktar()
        self.logs = []  # durum mesajları tutulur

        # Dosya yolları
        self.personel_file = os.path.join(base_path, "veri/personel.xlsx")
        self.ogretmen_file = os.path.join(base_path, "hazirlik/hz_personel_listesi.xlsx")
        self.nobet_file = os.path.join(base_path, "hazirlik/hz_duzenlenmis_nobet.xlsx")
        self.program_file = os.path.join(base_path, "hazirlik/hz_duzenlenmis_program.xlsx")

    # -------------------------------------------------------------
    # Yardımcı fonksiyonlar
    # -------------------------------------------------------------
    def _load_excel(self, path):
        """Excel dosyasını oku, boş satır ve Unnamed sütunları at."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dosya bulunamadı: {path}")

        df = pd.read_excel(path)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
        df = df.dropna(how="all")
        return df

    def _normalize_dates(self, df):
        """Tarih sütunlarını normalize et."""
        if "uygulama_tarihi" in df.columns:
            df["uygulama_tarihi"] = pd.to_datetime(
                df["uygulama_tarihi"], errors="coerce"
            ).fillna(self.uygulama_tarihi)
        else:
            df["uygulama_tarihi"] = self.uygulama_tarihi
        return df

    def _log(self, text):
        """Durum mesajını hem ekrana hem listeye kaydet."""
        print(text)
        self.logs.append(text)

    # -------------------------------------------------------------
    # Ana işlem fonksiyonu
    # -------------------------------------------------------------
    def yukle(self):
        """
        Tüm verileri sırayla oku ve veritabanına aktar.
        Dönüş: logs (liste)
        """
        try:
            # 1️⃣ Excel dosyalarını oku
            self._log("🔹 Excel dosyaları okunuyor...")
            personel_df = self._load_excel(self.personel_file)
            ogretmen_df = self._load_excel(self.ogretmen_file)
            nobet_df = self._load_excel(self.nobet_file)
            program_df = self._load_excel(self.program_file)

            # 2️⃣ Tarih sütunlarını normalize et
            self._log("🔹 Tarih sütunları normalize ediliyor...")
            nobet_df = self._normalize_dates(nobet_df)
            program_df = self._normalize_dates(program_df)
            #ogretmen_df=self._normalize_dates(ogretmen_df)

            # 3️⃣ Veritabanı aktarımı
            self._log("\n📤 Veritabanı aktarımı başlatıldı...")

            self._log("→ Personel aktarımı...")
            p_status = self.veri_aktar.save_yeni_veri_NobetPersonel(personel_df)
            self._log(f"✅ {p_status['message']}")

            self._log("→ Öğretmen aktarımı...")
            o_status = self.veri_aktar.save_yeni_veri_NobetOgretmen(ogretmen_df)
            self._log(f"✅ {o_status['message']}")

            self._log("→ Nöbet görevi aktarımı...")
            n_status = self.veri_aktar.save_yeni_veri_NobetGorevi(nobet_df)
            self._log(f"✅ {n_status['message']}")

            self._log("→ Ders programı aktarımı...")
            d_status = self.veri_aktar.save_yeni_veri_NobetDersProgrami(program_df)
            self._log(f"✅ {d_status['message']}")

            self._log(
                f"\n📅 Tüm veriler {self.uygulama_tarihi.strftime('%d.%m.%Y %H:%M:%S')} tarihinde kaydedildi."
            )

        except Exception as e:
            self._log(f"❌ Hata: {str(e)}")

        return self.logs

    # -------------------------------------------------------------
    # GUI veya CLI için kısa çağrı fonksiyonu
    # -------------------------------------------------------------
    def run(self):
        """Kısa çağrı: yukle() çalıştırır ve sonuçları döndürür."""
        return self.yukle()

