#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 21:15:43 2025

@author: senolirmak
"""

from nobetcigorevi.utils.verihazirla import EOkulVeriIsleyici



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
    uygulama_tarihi='2025/09/15',
    sinif_bilgileri=sinif_bilgileri
)

isleyici.calistir()