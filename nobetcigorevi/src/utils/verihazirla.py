#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 21:07:25 2025

@author: senolirmak
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class EOkulVeriIsleyici:
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
        self.df = pd.read_excel(file_path, sheet_name='Sheet1')
        self.df_personel = pd.read_excel(personel_path, sheet_name='Sayfa1')
        self.df_nobet = pd.read_excel(file_path_nobet, sheet_name='Sayfa1')
        self.gunler = [v[1] for v in self.TRGUN_CHOICES][:5]  # Pazartesi–Cuma
        self.processed_df = None
        self.df_ogretmenler =None
        self.nobetci_veri = None

    def split_and_replace(self, row):
        if pd.isna(row):
            return None, None
        parts = row.split('\n')
        if len(parts) > 1:
            second_part = parts[1]
            if '-' in second_part:
                sub_parts = second_part.split('-')
                return sub_parts[1], sub_parts[0]
            else:
                return parts[0].strip(), parts[1].strip()
        return None, None

    def parse_program(self):
        trgun_dict = dict(self.TRGUN_CHOICES)
        new_data = []
        for index, row in self.df.iterrows():
            if pd.isna(row[1]):
                continue
            giris_saat, cikis_saat = row[1].split('-')
            for col_index in range(2, self.df.shape[1]):
                gun = self.df.columns[col_index].strip().upper()
                value = row[col_index]
                if not pd.isna(value):
                    gun = trgun_dict[gun]
                    ders_adi, ders_ogretmeni = self.split_and_replace(value)
                    if ders_ogretmeni:
                        new_data.append([
                            giris_saat,
                            cikis_saat,
                            gun,
                            ders_adi,
                            ders_ogretmeni.strip(',')
                        ])
        self.processed_df = pd.DataFrame(
            new_data,
            columns=['giris_saat', 'cikis_saat', 'gun', 'ders_adi', 'ders_ogretmeni']
        )

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
        self.processed_df['uygulama_tarihi'] = self.uygulama_tarihi

    def dagit_siniflar(self):
        self.processed_df['sinif'] = None
        self.processed_df['sube'] = None
        self.processed_df['subeadi'] = None

        tum_siniflar = [
            (sinif, sube, f"{sinif} / {sube}")
            for sinif, subeler in self.sinif_bilgileri.items()
            for sube in subeler
        ]

        bolunmus = np.array_split(self.processed_df, len(tum_siniflar))

        for parca, (sinif, sube, subeadi) in zip(bolunmus, tum_siniflar):
            self.processed_df.loc[parca.index, 'sinif'] = sinif
            self.processed_df.loc[parca.index, 'sube'] = sube
            self.processed_df.loc[parca.index, 'subeadi'] = subeadi
    
    def personel(self):
        c_df = self.processed_df['ders_ogretmeni'].drop_duplicates().reset_index(drop=True)
        ogretmenler_df = pd.DataFrame(c_df)
        merged = ogretmenler_df.merge(self.df_personel[['gorev','adisoyadi', 'brans']],
                                      how='left',
                                      left_on='ders_ogretmeni', right_on='adisoyadi')
        
        merged = merged.drop(columns='adisoyadi')
        self.df_ogretmenler =merged

    def nobetci_ogretmen(self):
        ders_saatleri = list(self.DERSNOSU.values())
        trgun_dict = dict(self.TRGUN_CHOICES)
        self.df_nobet = self.df_nobet.rename(columns=trgun_dict)
        data = []
        for gun in self.gunler:
            df_nobet_gun = self.df_nobet[gun].dropna().tolist()

            for nb_ogretmen in df_nobet_gun:
                filtre_nobet = self.df_nobet[gun].str.contains(f'{nb_ogretmen}', case=False, na=False)
                nobet_yeri = self.df_nobet[filtre_nobet]['yer'].tolist()[0]
                filtre = (
                    self.processed_df['ders_ogretmeni'].str.contains(f'{nb_ogretmen}', case=False, na=False)
                    & (self.processed_df['gun'] == gun)
                )
                df_ogretmen_dersleri = self.processed_df[filtre]
                ogretmen_ders_saatleri = set(df_ogretmen_dersleri['giris_saat'].tolist())
                bos_saatler = set(ders_saatleri) - ogretmen_ders_saatleri

                bos_saatler_sirali = [self.DERSNOSU[i] for i in sorted(self.DERSNOSU) if self.DERSNOSU[i] in bos_saatler]

                saat_durumu = {
                    k: 'x' if v in bos_saatler_sirali else '-' for k, v in self.DERSNOSU.items()
                }

                saat_durumu.update({
                    'nobetci': nb_ogretmen,
                    'gun': gun,
                    'yer':nobet_yeri,
                    'uygulama_tarihi': self.uygulama_tarihi
                })

                data.append(saat_durumu)
        
        nobetci_manuel = pd.DataFrame(data)
        
        return nobetci_manuel

    def nobetci_data(self):
        nobet_veri = self.nobetci_ogretmen()
        return nobet_veri[['nobetci', 'gun', 'yer','uygulama_tarihi']]

    def detayli_nobet_tablosu(self):
        nobet_veri = self.nobetci_ogretmen()
        return nobet_veri
    
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
        
    def nobet_nobetgorevi_data(self):
        nobet_nobetgorevi_sutun_name={'gun':'nobet_gun','yer':'nobet_yeri'}
        self.nobetci_veri = self.nobetci_data()
        self.nobetci_veri = self.nobetci_veri.rename(columns=nobet_nobetgorevi_sutun_name)
        self.nobetci_veri['nobetci'] = self.nobetci_veri['nobetci'].str.strip()
        
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
        
        self.parse_program()
        self.ekle_ders_saati()
        self.dagit_siniflar()
        self.personel()
        self.kaydet(program_listesi, personel_listesi,nobetci_listesi)
