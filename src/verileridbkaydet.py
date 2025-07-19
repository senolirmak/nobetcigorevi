#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 21:16:36 2025

@author: senolirmak
"""

import pandas as pd
from nobetcigorevi.utils.veriaktar import VeriAktar
from nobetcigorevi.utils.verihazirla import EOkulVeriIsleyici


# E-Okul verilerini Dönüştürür
sinif_bilgileri = {
    9: ['A','B','C','D','E','F','G','H','İ','J','K'],
    10: ['A','B','C','D','E','F'],
    11: ['A','B','C','D','E','F','G'],
    12: ['A','B','C','D','E','F','G','H','İ','J','K']
}

isleyici = EOkulVeriIsleyici(
    file_path='nobetcigorevi/tmp/veri/OOK11002_R01_422.xlsx',
    personel_path ='nobetcigorevi/tmp/veri/personel.xlsx',
    file_path_nobet = 'nobetcigorevi/tmp/veri/nobetciler.xlsx',
    uygulama_tarihi='2025/09/14',
    sinif_bilgileri=sinif_bilgileri
)

isleyici.calistir()

# Düzenlenmiş verileri veritabanına kaydedelim

# 1. Düzenlenmiş Excel dosyasını oku
personel_file_path = "nobetcigorevi/tmp/veri/personel.xlsx"
ogretmen_file_path = "nobetcigorevi/tmp/hazirlik/hz_personel_listesi.xlsx"
nobet_file_path = "nobetcigorevi/tmp/hazirlik/hz_duzenlenmis_nobet.xlsx"
program_file_path = "nobetcigorevi/tmp/hazirlik/hz_duzenlenmis_program.xlsx"

personel_df = pd.read_excel(personel_file_path)
ogretmen_df = pd.read_excel(ogretmen_file_path)
nobet_df = pd.read_excel(nobet_file_path)
program_df = pd.read_excel(program_file_path)

veri_aktar = VeriAktar()

personel_status = veri_aktar.save_results_NobetPersonel(personel_df)
print(personel_status['message'])

ogretmen_status = veri_aktar.save_results_NobetOgretmen(ogretmen_df)
print(ogretmen_status['message'])

nobetci_status = veri_aktar.save_results_NobetGorevi(nobet_df)
print(nobetci_status['message'])

program_status = veri_aktar.save_results_NobetDersProgrami(program_df)
print(program_status['message'])

