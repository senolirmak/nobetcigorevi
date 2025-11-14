
# Nöbetçi Öğretmen Ders Doldurma Görevi
# 🏫 Nöbetçi Öğretmen Ders Doldurma Sistemi

**Yazan:** Şenol Irmak  
**Okul:** Abdurrahim Karakoç Anadolu Lisesi  
**Teknolojiler:** PyQt5 · SQLAlchemy · pandas · openpyxl · reportlab

---

## 🎯 Amaç

Bu sistem, öğretmenlerin devamsızlık durumlarında nöbet görevi ve ders dağılımını adil bir şekilde planlar.  
Tüm dağılımlar, SQL veritabanında saklanır ve PyQt arayüzü üzerinden yönetilir.

---
*****************
Okul Haftalık Ders Programını
Verileri e-okul<br>
    -->ders programı<br>
        -->sınıf programı<br>
        -->excel dökümünden<br>  
<br>
raporlardan alalım(OOK11002_R01_XXXX.xlsx)<br>  
XXX:raporun AyGun bilgisi<br>
..<br>
.<br>
nobetciler.xlsx dosyası;<br>

| NÖBETÇİLER |-----------------------------|-------------------|------------------------------|
|------------|-----------------------------|-------------------|------------------------------|
|------------|-----------------------------|-------------------|------------------------------|
|------------|-----------------------------|-------------------|------------------------------|
| Günler     | Nöbetçi Öğretmenler         | Nöbetçi Yerleri   | Nöbetçi Müdür Yardımcısı     | 
|            | Ahmet Metin                 | 1.Kat Koridor     |                              |
| Pazartesi  | Kemal Dağlı                 | Giriş             |                              |
.....
 
formatında,
******************
/veri klasörüne personel.xlsx dosyasını oluşturun
personel.xlsx dosyası basitçe; 

| gorev            | kimlikno     |adisoyadi          | brans           |
|------------------|--------------|-------------------|-----------------|
| Öğretmen         | 99000000001  | Ahmet             | Matematik       |
| Müdür            | 99000000002  | Hakan Haktan      | Kimya           |
| Müdür Yardımcısı | 99000000003  | Kemal Kum         | Beden Eğitimi   |
| Görevlendirme    | 99000000004  | Ayşe Ayşecik      | Biyoloji        |
| Ücretli Öğretmen | 99000000005  | Hasan Kuru        | Fizik           |
.....

formatında,
******************

Veri Yükle kartını seçerek OOK11002_R01_XXXX.xlsx ve nobetciler.xlsx dosyanısın yerini gösterin
yeni veriler Uygulama Tarihi ile kayıt yapılır.

## ⚙️ Kurulum

### Conda Ortamı Oluşturma
```bash
conda env create -f environment.yml
conda activate nobet


