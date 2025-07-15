#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 21:16:36 2025

@author: senolirmak
"""

import pandas as pd
from nobetcigorevi.utils.veriaktar import VeriAktar

# 1. Düzenlenmiş Excel dosyasını oku
personel_file_path = "nobetcigorevi/tmp/hazirlik/hz_personel_listesi.xlsx"
nobet_file_path = "nobetcigorevi/tmp/hazirlik/hz_duzenlenmis_nobet.xlsx"
program_file_path = "nobetcigorevi/tmp/hazirlik/hz_duzenlenmis_program.xlsx"

personel_df = pd.read_excel(personel_file_path)
nobet_df = pd.read_excel(nobet_file_path)
program_df = pd.read_excel(program_file_path)

veri_aktar = VeriAktar()

personel_status = veri_aktar.save_results_NobetOgretmen(personel_df)
print(personel_status['message'])

nobetci_status = veri_aktar.save_results_NobetGorevi(nobet_df)
print(nobetci_status['message'])

program_status = veri_aktar.save_results_NobetDersProgrami(program_df)
print(program_status['message'])