#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  5 23:02:47 2025

@author: senolirmak
"""
from datetime import datetime, date, timedelta

class NobetUIHelper:
    @staticmethod
    def get_haftanin_gunu(tarih: date = None):
        """Verilen tarihin haftanın hangi günü olduğunu İngilizce olarak döndürür"""
        if not tarih:
            tarih = date.today()
        return tarih.strftime("%A")  # Monday, Tuesday, etc.

    @staticmethod
    def get_haftanin_gunu_turkce(tarih: date = None):
        """Verilen tarihin haftanın hangi günü olduğunu Türkçe olarak döndürür"""
        gunler = {
                "Pazartesi": "Monday",
                "Salı": "Tuesday",
                "Çarşamba": "Wednesday",
                "Perşembe": "Thursday",
                "Cuma": "Friday"
            }
        
        ingilizce_gun = NobetUIHelper.get_haftanin_gunu(tarih)
        return gunler.get(ingilizce_gun, ingilizce_gun)

    @staticmethod
    def get_haftalik_tarih_araligi(baslangic_tarihi: date = None):
        """Verilen tarihin içinde bulunduğu haftanın tüm günlerini döndürür"""
        if not baslangic_tarihi:
            baslangic_tarihi = date.today()
        
        baslangic = baslangic_tarihi - timedelta(days=baslangic_tarihi.weekday())
        hafta = [baslangic + timedelta(days=i) for i in range(7)]
        
        return {
            "Monday": hafta[0],
            "Tuesday": hafta[1],
            "Wednesday": hafta[2],
            "Thursday": hafta[3],
            "Friday": hafta[4],
            "Saturday": hafta[5],
            "Sunday": hafta[6]
        }

    @staticmethod
    def ogretmen_listesi_olustur(ogretmenler, brans_goster=True):
        """Öğretmen listesini QListWidget veya QComboBox için uygun formata getirir"""
        return [
            {
                "text": f"{ogr.adi_soyadi} ({ogr.brans})" if brans_goster else ogr.adi_soyadi,
                "data": ogr.id,
                "object": ogr
            }
            for ogr in ogretmenler
        ]