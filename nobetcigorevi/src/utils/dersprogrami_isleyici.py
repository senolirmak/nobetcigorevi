#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DersProgramiIsleyici – Kullanıcı ev dizininde ($HOME/NobetciVeri) çalışacak şekilde düzenlenmiş sürüm

Tüm veri dosyaları şu yapıda tutulur:

$HOME/NobetciVeri/
    ├── veri/
    │     ├── OOK11002_R01_112.XLS
    │     ├── personel.xlsx
    │     ├── 03KASIM2025_ÖğretmenNöbet.xlsx
    │     └── program_temiz.xlsx   (otomatik üretilir)
    └── hazirlik/
          ├── hz_duzenlenmis_program.xlsx
          ├── hz_personel_listesi.xlsx
          └── hz_duzenlenmis_nobet.xlsx
"""

import pandas as pd
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')


# ---------------------------------------------------------
# Kullanıcı veri kökü: $HOME/NobetciVeri
# ---------------------------------------------------------
HOME_DATA_DIR = Path.home() / "NobetciVeri"
VERI_DIR = HOME_DATA_DIR / "veri"
HAZIRLIK_DIR = HOME_DATA_DIR / "hazirlik"

# Gerekli klasörleri oluştur
for d in (HOME_DATA_DIR, VERI_DIR, HAZIRLIK_DIR):
    d.mkdir(parents=True, exist_ok=True)


class DersProgramiIsleyici:
    TRGUN_CHOICES = [
        ('PAZARTESİ', 'Monday'),
        ('SALI', 'Tuesday'),
        ('ÇARSAMBA', 'Wednesday'),
        ('PERŞEMBE', 'Thursday'),
        ('CUMA', 'Friday'),
        ('CUMARTESİ', 'Saturday'),
        ('PAZAR', 'Sunday')
    ]

    DERSNOSU = {
        1: "08:00",
        2: "08:50",
        3: "09:40",
        4: "10:30",
        5: "11:20",
        6: "12:10",
        7: "13:35",
        8: "14:25"
    }

    def __init__(self, file_path, personel_path,
                 file_path_nobet, uygulama_tarihi, sinif_bilgileri):

        self.uygulama_tarihi = uygulama_tarihi
        self.sinif_bilgileri = sinif_bilgileri

        # -------------------------------------------------
        # Gelen yolları $HOME/NobetciVeri/veri altına sabitle
        # absolute verilirse olduğu gibi kullanılır
        # -------------------------------------------------
        self.file_path = self._resolve_veri_path(file_path)
        self.personel_path = self._resolve_veri_path(personel_path)
        self.file_path_nobet = self._resolve_veri_path(file_path_nobet)

        # Program temizleme (program_temiz.xlsx de VERI_DIR altına yazılır)
        self.df = self.program_temizle(self.file_path)

        # Personel ve nöbet dosyalarını oku
        self.df_personel = pd.read_excel(self.personel_path, sheet_name='Sayfa1')
        df_nobet_raw = pd.read_excel(self.file_path_nobet, sheet_name="SABAH")
        df_nobet_raw = df_nobet_raw.iloc[3:, :4]  # 3 satır başlığı atla
        df_nobet_raw.columns = ["nobetgun", "_", "adisoyadi", "nobetyeri"]
        self.df_nobet = df_nobet_raw

        self.gunler = [v[1] for v in self.TRGUN_CHOICES][:5]  # Pazartesi–Cuma
        self.processed_df = None
        self.df_ogretmenler = None
        self.nobetci_veri = None

    # -----------------------------------------------------
    # Yol yardımcıları
    # -----------------------------------------------------
    def _resolve_veri_path(self, p):
        """
        Eğer p mutlak değilse, $HOME/NobetciVeri/veri altına yerleştir.
        Örn: 'personel.xlsx' → $HOME/NobetciVeri/veri/personel.xlsx
        """
        p = Path(p)
        if p.is_absolute():
            return p
        return VERI_DIR / p

    def _resolve_hazirlik_path(self, p):
        """
        Eğer p mutlak değilse, $HOME/NobetciVeri/hazirlik altına yerleştir.
        Örn: 'hz_duzenlenmis_program.xlsx'
             → $HOME/NobetciVeri/hazirlik/hz_duzenlenmis_program.xlsx
        """
        p = Path(p)
        if p.is_absolute():
            return p
        return HAZIRLIK_DIR / p

    # -----------------------------------------------------
    def program_temizle(self, file_path: Path):
        out_file = VERI_DIR / "program_temiz.xlsx"

        # İlk 6 satır başlık/boş satır
        df = pd.read_excel(file_path, header=None, skiprows=6)
        kontrol_araligi = df.iloc[:, 0:24]
        mask_dolu = kontrol_araligi.notna().any(axis=1)
        df_temiz = df.loc[mask_dolu].reset_index(drop=True)

        # Çıktıyı $HOME/NobetciVeri/veri/program_temiz.xlsx olarak kaydet
        df_temiz.to_excel(out_file, index=False, header=False)

        return pd.read_excel(out_file)

    def split_and_replace(self, row):
        """
        Hücre içeriğinden (ders_adi, ders_ogretmeni) çiftini döndürür.
        """
        import pandas as pd

        if pd.isna(row):
            return None, None

        text = str(row).strip()
        if not text:
            return None, None

        parts = [p.strip() for p in text.split('\n') if p.strip()]

        ders_adi = None
        ogretmen_adlari = []

        if parts:
            if parts[0].strip().upper() == "SEÇMELİ DERS":
                ders_satiri_var = False
            else:
                ders_satiri_var = True
                ders_adi = parts[0]

        if len(parts) >= 2:
            ikinci_satir = parts[1]

            if '-' in ikinci_satir:
                ogretmen_kisim, ders_kisim = [p.strip() for p in ikinci_satir.split('-', 1)]
                ders_adi = ders_kisim
                ogretmen_adlari = [ad.strip() for ad in ogretmen_kisim.split(',') if ad.strip()]
            else:
                ogretmen_adlari = [ad.strip() for ad in ikinci_satir.split(',') if ad.strip()]

        ogretmen_adlari_str = ', '.join(ogretmen_adlari) if ogretmen_adlari else None

        return ders_adi, ogretmen_adlari_str

    def parse_program(self):
        """
        Her 8 satır bir şubeye ait haftalık programdır.
        Şube bilgisi doğrudan burada atanır.
        Virgülle ayrılan öğretmenler explode edildiğinde
        şube bilgisi korunur.
        """
        trgun_dict = dict(self.TRGUN_CHOICES)
        new_data = []

        # 1️⃣ Sütun adlarını temizle
        cleaned_cols = []
        for c in self.df.columns:
            cs = str(c).strip().upper()
            cleaned_cols.append(None if cs.startswith("UNNAMED") or cs == "NAN" else cs)
        self.df.columns = cleaned_cols

        # 2️⃣ Sınıf–şube listesini sırayla hazırla
        tum_siniflar = [
            (sinif, sube, f"{sinif} / {sube}")
            for sinif, subeler in self.sinif_bilgileri.items()
            for sube in subeler
        ]

        blok_boyutu = 8
        toplam_satir = len(self.df)
        toplam_sube = toplam_satir // blok_boyutu
        toplam_sube = min(toplam_sube, len(tum_siniflar))

        print(f"Toplam {toplam_sube} şube tespit edildi ({toplam_satir} satır).")

        # 3️⃣ Her şube bloğunu sırayla işle
        for sube_index in range(toplam_sube):
            start = sube_index * blok_boyutu
            end = start + blok_boyutu
            sube_df = self.df.iloc[start:end]

            sinif, sube, subeadi = tum_siniflar[sube_index]

            for _, row in sube_df.iterrows():
                if pd.isna(row[1]) or '-' not in str(row[1]):
                    continue

                giris_saat, cikis_saat = [s.strip() for s in str(row[1]).split('-', 1)]

                for col_index in range(2, self.df.shape[1]):
                    gun_adi = self.df.columns[col_index]
                    if not gun_adi or gun_adi not in trgun_dict:
                        continue

                    value = row[col_index]
                    if pd.isna(value):
                        continue

                    ders_adi, ders_ogretmeni = self.split_and_replace(value)
                    if not ders_adi or not ders_ogretmeni:
                        continue

                    ogretmenler = [o.strip() for o in str(ders_ogretmeni).split(',') if o.strip()]
                    for ogretmen in ogretmenler:
                        new_data.append([
                            giris_saat,
                            cikis_saat,
                            trgun_dict[gun_adi],
                            ders_adi,
                            ogretmen,
                            sinif,
                            sube,
                            subeadi
                        ])

        self.processed_df = pd.DataFrame(
            new_data,
            columns=[
                'giris_saat', 'cikis_saat', 'gun', 'ders_adi',
                'ders_ogretmeni', 'sinif', 'sube', 'subeadi'
            ]
        )

        print(f"✅ parse_program: {len(self.processed_df)} satır işlendi. "
              f"({toplam_sube} şube * {blok_boyutu} satır)")

    def cevir_gunler(self):
        gun_cevirim = {tr: eng for tr, eng in self.TRGUN_CHOICES}
        self.processed_df['gun'] = self.processed_df['gun'].map(gun_cevirim)

    def ekle_ders_saati(self):
        saat_to_ders = {v: k for k, v in self.DERSNOSU.items()}
        self.processed_df['ders_saati'] = self.processed_df['giris_saat'].map(saat_to_ders)
        self.processed_df['ders_ogretmeni'] = self.processed_df['ders_ogretmeni'].str.split(',')
        self.processed_df = (
            self.processed_df.explode('ders_ogretmeni')
            .reset_index(drop=True)
        )
        self.processed_df['ders_ogretmeni'] = self.processed_df['ders_ogretmeni'].str.strip()
        self.processed_df['ders_saati_adi'] = self.processed_df['ders_saati'].astype(str) + ". Ders"
        self.processed_df['uygulama_tarihi'] = pd.to_datetime(self.uygulama_tarihi)

    def personel(self):
        c_df = self.processed_df['ders_ogretmeni'].drop_duplicates().reset_index(drop=True)
        ogretmenler_df = pd.DataFrame(c_df)
        merged = ogretmenler_df.merge(
            self.df_personel[['gorev', 'adisoyadi', 'brans','cinsiyet']],
            how='left',
            left_on='ders_ogretmeni',
            right_on='adisoyadi'
        )
        merged = merged.drop(columns='adisoyadi')
        self.df_ogretmenler = merged

    def nobet_dosyasi_olustur_sabah(self):
        self.df_nobet = self.df_nobet.dropna(subset=["adisoyadi", "nobetyeri"], how="all")
        self.df_nobet["nobetgun"] = self.df_nobet["nobetgun"].ffill()

        gun_map = {
            "Pazartesi": "Monday",
            "Salı": "Tuesday",
            "Çarşamba": "Wednesday",
            "Perşembe": "Thursday",
            "Cuma": "Friday"
        }
        self.df_nobet["nobetgun"] = self.df_nobet["nobetgun"].replace(gun_map)
        self.df_nobet["uygulama_tarihi"] = pd.to_datetime(self.uygulama_tarihi)
        self.df_nobet = self.df_nobet[["adisoyadi", "nobetgun", "nobetyeri", "uygulama_tarihi"]]

        self.nobetci_veri = self.df_nobet.rename(columns={
            "adisoyadi": "nobetci",
            "nobetgun": "nobet_gun",
            "nobetyeri": "nobet_yeri"
        })
        return self.nobetci_veri

    def nobetci_data(self):
        nobet_veri = self.nobet_dosyasi_olustur_sabah()
        return nobet_veri[['nobetci', 'nobet_gun', 'nobet_yeri', 'uygulama_tarihi']]

    def detayli_nobet_tablosu(self):
        return self.nobet_dosyasi_olustur_sabah()

    def nobet_nobetgorevi_data(self):
        self.nobetci_veri = self.nobetci_data()
        self.nobetci_veri['nobetci'] = self.nobetci_veri['nobetci'].str.strip()

    def nobet_ogretmen_data(self):
        nobet_ogretmen_sutun_name = {
            'ders_ogretmeni': 'adi_soyadi',
            'gorev': 'gorev_tipi',
            'brans': 'brans'
        }

        nobet_ogretmen_nobeti_yok = ['Müdür', 'Müdür Yardımcısı', 'Ücretli Öğretmen']
        self.df_ogretmenler = self.df_ogretmenler.rename(columns=nobet_ogretmen_sutun_name)
        self.df_ogretmenler['nobeti_var'] = 1
        self.df_ogretmenler.loc[
            self.df_ogretmenler['gorev_tipi'].isin(nobet_ogretmen_nobeti_yok),
            'nobeti_var'
        ] = 0
        self.df_ogretmenler = self.df_ogretmenler.sort_values(by='adi_soyadi').reset_index(drop=True)
        self.df_ogretmenler['adi_soyadi'] = self.df_ogretmenler['adi_soyadi'].str.strip()
        self.df_ogretmenler["uygulama_tarihi"] = pd.to_datetime(self.uygulama_tarihi)

    def kaydet(self, program_listesi, personel_listesi, nobetci_listesi):
        # Çıktı yollarını $HOME/NobetciVeri/hazirlik altında çözüyoruz
        program_listesi = self._resolve_hazirlik_path(program_listesi)
        personel_listesi = self._resolve_hazirlik_path(personel_listesi)
        nobetci_listesi = self._resolve_hazirlik_path(nobetci_listesi)

        self.nobet_ogretmen_data()
        self.nobet_nobetgorevi_data()

        # Klasörlerin varlığını garanti et
        program_listesi.parent.mkdir(parents=True, exist_ok=True)
        personel_listesi.parent.mkdir(parents=True, exist_ok=True)
        nobetci_listesi.parent.mkdir(parents=True, exist_ok=True)

        self.processed_df.to_excel(program_listesi, index=False)
        self.df_ogretmenler.to_excel(personel_listesi, index=False)
        self.nobetci_veri.to_excel(nobetci_listesi, index=False)

    def calistir(self,
                 program_listesi='hz_duzenlenmis_program.xlsx',
                 personel_listesi='hz_personel_listesi.xlsx',
                 nobetci_listesi='hz_duzenlenmis_nobet.xlsx'):
        """
        Tüm süreci çalıştırır ve çıktıları $HOME/NobetciVeri/hazirlik altına yazar.
        """
        print("⏳ Program verisi işleniyor...")

        self.parse_program()
        self.ekle_ders_saati()
        self.personel()
        self.kaydet(program_listesi, personel_listesi, nobetci_listesi)

        print(f"✅ Tüm işlemler tamamlandı.\n"
              f"   ➤ Program:   {self._resolve_hazirlik_path(program_listesi)}\n"
              f"   ➤ Personel:  {self._resolve_hazirlik_path(personel_listesi)}\n"
              f"   ➤ Nöbetçi:   {self._resolve_hazirlik_path(nobetci_listesi)}")

"""
# Kullanım Örneği
if __name__ == "__main__":        

    sinif_bilgileri = {
        9:  ['A','B','C','D','E','F'],
        10: ['A','B','C','D','E','F','G','H','İ'],
        11: ['A','B','C','D','E','F','G','H'],
        12: ['A','B','C','D','E','F','G']
    }
    
    isleyici = DersProgramiIsleyici(
        file_path='veri/OOK11002_R01_112.XLS',
        personel_path ='veri/personel.xlsx',
        file_path_nobet = 'veri/03KASIM2025_ÖğretmenNöbet.xlsx',
        uygulama_tarihi='2025/11/03',
        sinif_bilgileri=sinif_bilgileri
    )

    isleyici.calistir()
"""