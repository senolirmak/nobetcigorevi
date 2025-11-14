#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 12 19:11:21 2025

@author: senolirmak
"""

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class DersProgramiIsleyici:
    TRGUN_CHOICES = [
        ('PAZARTESİ','Monday'),
        ('SALI','Tuesday'),
        ('ÇARSAMBA','Wednesday'),
        ('PERŞEMBE','Thursday'),
        ('CUMA','Friday'),
        ('CUMARTESİ','Saturday'),
        ('PAZAR','Sunday')
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
                 file_path_nobet , uygulama_tarihi, sinif_bilgileri):
        
        self.uygulama_tarihi = uygulama_tarihi
        self.sinif_bilgileri = sinif_bilgileri
        self.file_path_nobet = file_path_nobet
        self.df = self.program_temizle(file_path)#başlıkları otomatik algılama  pd.read_excel(file_path, sheet_name='Sheet1')
        self.df_personel = pd.read_excel(personel_path, sheet_name='Sayfa1')
        self.df_nobet = pd.read_excel(self.file_path_nobet, sheet_name="SABAH")
        self.df_nobet = self.df_nobet.iloc[3:, :4]  # 3 satır başlığı atla
        self.df_nobet.columns = ["nobetgun", "_", "adisoyadi", "nobetyeri"]
        self.gunler = [v[1] for v in self.TRGUN_CHOICES][:5]  # Pazartesi–Cuma
        self.processed_df = None
        self.df_ogretmenler =None
        self.nobetci_veri = None
           
    def program_temizle(self, file_path):
        out_file = "veri/program_temiz.xlsx"
        # İlk 6 satır başlık/boş satır
        df = pd.read_excel(file_path, header=None, skiprows=6)
        kontrol_araligi = df.iloc[:, 0:24]
        mask_dolu = kontrol_araligi.notna().any(axis=1)
        df_temiz = df.loc[mask_dolu].reset_index(drop=True)
        df_temiz.to_excel(out_file, index=False, header=False)
        return pd.read_excel(out_file)

        
    def split_and_replace(self, row):
        """
        Hücre içeriğinden (ders_adi, ders_ogretmeni) çiftini döndürür.
        
        Kurallar:
        1️⃣ Hücrede satır ayracı (\n) varsa iki parçaya bölünür.
            - İlk satır "SEÇMELİ DERS" ise atılır.
            - Aksi halde ilk satır ders adıdır.
        2️⃣ İkinci satır öğretmen bilgilerini içerir.
            - Eğer "-" varsa: 'öğretmen adı - ders adı' şeklindedir.
            - Eğer "," varsa: birden fazla öğretmen vardır.
        3️⃣ Dönüş: (ders_adi, öğretmen_adı)
        """
        import pandas as pd
    
        if pd.isna(row):
            return None, None
    
        text = str(row).strip()
        if not text:
            return None, None
    
        # Satırlara böl
        parts = [p.strip() for p in text.split('\n') if p.strip()]
    
        ders_adi = None
        ogretmen_adlari = []
    
        # 1️⃣ İlk satır: eğer "SEÇMELİ DERS" ise atla
        if parts:
            if parts[0].strip().upper() == "SEÇMELİ DERS":
                ders_satiri_var = False
            else:
                ders_satiri_var = True
                ders_adi = parts[0]
    
        # 2️⃣ İkinci satır varsa öğretmen/ders bilgisi buradadır
        if len(parts) >= 2:
            ikinci_satir = parts[1]
    
            # Eğer "-" varsa: öğretmen - ders biçimi
            if '-' in ikinci_satir:
                ogretmen_kisim, ders_kisim = [p.strip() for p in ikinci_satir.split('-', 1)]
                ders_adi = ders_kisim  # ders adı güncellenir
                # Birden fazla öğretmen olabilir
                ogretmen_adlari = [ad.strip() for ad in ogretmen_kisim.split(',') if ad.strip()]
            else:
                # Sadece öğretmen adları (virgüllü olabilir)
                ogretmen_adlari = [ad.strip() for ad in ikinci_satir.split(',') if ad.strip()]
    
        # 3️⃣ Öğretmen adlarını birleştir (liste halinde dönebilir)
        ogretmen_adlari_str = ', '.join(ogretmen_adlari) if ogretmen_adlari else None
    
        return ders_adi, ogretmen_adlari_str
    
    def parse_program(self):
        """
        Her 8 satır bir şubeye ait haftalık programdır.
        Şube bilgisi doğrudan burada atanır.
        Virgülle ayrılan öğretmenler explode edildiğinde
        şube bilgisi korunur.
        """
        """
        # 2️⃣ A:X sütun aralığını seç (ilk 24 sütun; A=0, X=23)
        kontrol_araligi = self.df.iloc[:, 0:24]

        # 3️⃣ Bu aralıkta tamamen boş satırları bul
        mask_dolu = kontrol_araligi.notna().any(axis=1)  # en az bir hücre doluysa True

        # 4️⃣ Boş satırları filtrele
        temiz = self.df.loc[mask_dolu].reset_index(drop=True)
        #temiz = temiz.iloc[1:]
        self.df = temiz
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
    
                # Pazartesi–Cuma sütunlarını işle
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
    
                    # Virgülle ayrılmış öğretmenler (explode öncesi)
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
    
        # 4️⃣ Sonuç DataFrame oluştur
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
        merged = ogretmenler_df.merge(self.df_personel[['gorev','adisoyadi', 'brans']],
                                      how='left',
                                      left_on='ders_ogretmeni', right_on='adisoyadi')
        
        merged = merged.drop(columns='adisoyadi')
        self.df_ogretmenler =merged
        #self.df_ogretmenler["uygulama_tarihi"] = pd.to_datetime(self.uygulama_tarihi)
    
    def nobet_dosyasi_olustur_sabah(self):
        """
        08EYLUL2025_ÖğretmenNöbet.xls dosyasındaki SABAH sayfasından
        nöbetçi, nöbet_gun, nöbet_yeri ve uygulama_tarihi bilgilerini çıkarır.
        """
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
        # doğru sütunlar:
        return nobet_veri[['nobetci', 'nobet_gun', 'nobet_yeri', 'uygulama_tarihi']]

    def detayli_nobet_tablosu(self):
        # aynı veriyi döndürmesi yeterli
        return self.nobet_dosyasi_olustur_sabah()
    
    def nobet_nobetgorevi_data(self):
        self.nobetci_veri = self.nobetci_data()
        self.nobetci_veri['nobetci'] = self.nobetci_veri['nobetci'].str.strip()

    def nobet_ogretmen_data(self):
        nobet_ogretmen_sutun_name={'ders_ogretmeni':'adi_soyadi',
                                   'gorev':'gorev_tipi',
                                   'brans':'brans'}
        
        nobet_ogretmen_nobeti_yok = ['Müdür', 'Müdür Yardımcısı', 'Ücretli Öğretmen']
        self.df_ogretmenler= self.df_ogretmenler.rename(columns=nobet_ogretmen_sutun_name)
        self.df_ogretmenler['nobeti_var']=1
        self.df_ogretmenler.loc[self.df_ogretmenler['gorev_tipi'].isin(nobet_ogretmen_nobeti_yok), 'nobeti_var'] = 0
        self.df_ogretmenler = self.df_ogretmenler.sort_values(by='adi_soyadi').reset_index(drop=True)
        self.df_ogretmenler['adi_soyadi'] = self.df_ogretmenler['adi_soyadi'].str.strip()
        self.df_ogretmenler["uygulama_tarihi"] = pd.to_datetime(self.uygulama_tarihi)
        

    def kaydet(self, program_listesi,personel_listesi,nobetci_listesi):
        self.nobet_ogretmen_data()
        self.nobet_nobetgorevi_data()
        self.processed_df.to_excel(program_listesi, index=False)
        self.df_ogretmenler.to_excel(personel_listesi, index=False)
        self.nobetci_veri.to_excel(nobetci_listesi, index=False)

    def calistir(self,
             program_listesi='hazirlik/hz_duzenlenmis_program.xlsx',
             personel_listesi='hazirlik/hz_personel_listesi.xlsx',
             nobetci_listesi='hazirlik/hz_duzenlenmis_nobet.xlsx'):
        """
        Tüm süreci çalıştırır:
        1. Excel'den veriyi okur ve işler (parse_program)
        2. Ders saatlerini ve öğretmen dağılımını ekler
        3. Personel bilgilerini eşleştirir
        4. Nöbet verisini oluşturur
        5. Sonuç dosyalarını kaydeder
        """
        print("⏳ Program verisi işleniyor...")
    
        # 1️⃣ Ders programını oku ve şube bilgilerini dahil et
        self.parse_program()
    
        # 2️⃣ Ders saatlerini ekle
        self.ekle_ders_saati()
    
        # 3️⃣ Personel eşleştirmesi
        self.personel()
    
        # 4️⃣ Dosyaları kaydet
        self.kaydet(program_listesi, personel_listesi, nobetci_listesi)
    
        print(f"✅ Tüm işlemler tamamlandı.\n"
              f"   ➤ Program: {program_listesi}\n"
              f"   ➤ Personel: {personel_listesi}\n"
              f"   ➤ Nöbet: {nobetci_listesi}")

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