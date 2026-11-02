import sqlite3
import os
import re
import time
import random
import pandas as pd
from google import genai
from google.genai import types

# =========================================================
# 1. VERITABANI OLUSTURMA
# =========================================================

baslangic_zamani = time.perf_counter()

baglanti = sqlite3.connect(":memory:")
imlec = baglanti.cursor()

imlec.execute("""
CREATE TABLE musteriler (
    musteri_id INTEGER PRIMARY KEY,
    ad_soyad TEXT NOT NULL,
    sehir TEXT NOT NULL
)
""")

imlec.execute("""
CREATE TABLE siparisler (
    siparis_id INTEGER PRIMARY KEY,
    musteri_id INTEGER,
    tutar REAL,
    tarih TEXT,
    FOREIGN KEY (musteri_id) REFERENCES musteriler(musteri_id)
)
""")

sehirler = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"]
adlar = ["Ahmet", "Mehmet", "Ayşe", "Fatma", "Emre",
         "Zeynep", "Can", "Elif", "Burak", "Merve"]
soyadlar = ["Yılmaz", "Demir", "Kaya", "Çelik", "Şahin",
            "Yıldız", "Aydın", "Öztürk", "Arslan", "Doğan"]

musteriler = []

for i in range(1, 1001):
    ad_soyad = random.choice(adlar) + " " + random.choice(soyadlar)
    sehir = random.choice(sehirler)
    musteriler.append((i, ad_soyad, sehir))

imlec.executemany(
    "INSERT INTO musteriler VALUES (?, ?, ?)",
    musteriler
)

siparisler = []

for i in range(1, 1001):
    musteri_id = random.randint(1, 1000)
    tutar = round(random.uniform(100, 10000), 2)
    tarih = "2026-01-01"
    siparisler.append((i, musteri_id, tutar, tarih))

imlec.executemany(
    "INSERT INTO siparisler VALUES (?, ?, ?, ?)",
    siparisler
)

baglanti.commit()

imlec.execute("SELECT COUNT(*) FROM musteriler")
musteri_sayisi = imlec.fetchone()[0]

imlec.execute("SELECT COUNT(*) FROM siparisler")
siparis_sayisi = imlec.fetchone()[0]

print("=" * 55)
print("YAPAY ZEKA DESTEKLI SQL ASISTANI")
print("=" * 55)
print(f"Musteri sayisi: {musteri_sayisi}")
print(f"Siparis sayisi: {siparis_sayisi}")


# =========================================================
# 2. GUVENLIK KONTROLU
# =========================================================

yasakli_komutlar = [
    "DROP", "DELETE", "UPDATE", "INSERT",
    "ALTER", "CREATE", "REPLACE", "ATTACH",
    "DETACH", "PRAGMA", "VACUUM"
]

guvenlik_ihlalleri = []
rapor_kayitlari = []


def guvenlik_kontrolu(sql_kodu):
    """
    Sadece SELECT sorgularina izin verir.
    Yasakli SQL komutlarini ve coklu sorgulari engeller.
    """
    if not isinstance(sql_kodu, str):
        return False

    temiz_sql = re.sub(r"/\*.*?\*/", " ", sql_kodu, flags=re.S)
    temiz_sql = re.sub(r"--.*?$", " ", temiz_sql, flags=re.M)
    temiz_sql = temiz_sql.strip()

    if not temiz_sql:
        return False

    if not re.match(r"^SELECT\b", temiz_sql, flags=re.I):
        return False

    for komut in yasakli_komutlar:
        if re.search(r"\b" + komut + r"\b", temiz_sql, flags=re.I):
            return False

    return True


def clean_sql(metin):
    """Gemini cevabindaki Markdown SQL bloklarini temizler."""
    if not metin:
        return ""

    metin = metin.strip()
    metin = re.sub(r"^```(?:sql)?\s*", "", metin, flags=re.I)
    metin = re.sub(r"\s*```$", "", metin)

    return metin.strip()


izin_verilen_islemler = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION
}

if hasattr(sqlite3, "SQLITE_RECURSIVE"):
    izin_verilen_islemler.add(sqlite3.SQLITE_RECURSIVE)


def sqlite_guvenlik_kontrolu(islem, arg1, arg2, veritabani, kaynak):
    if islem in izin_verilen_islemler:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


baglanti.set_authorizer(sqlite_guvenlik_kontrolu)


# =========================================================
# 3. GEMINI API BAGLANTISI
# =========================================================

client = genai.Client(api_key="AQ.Ab8RN6JCdvw1cM4KDqKXJaQByb1ZN-lmWtTOK_-671cf2_mQ1w")
print("\nGemini API baglantisi hazir.")


# =========================================================
# 4. GEMINI ILE SQL SORGUSU OLUSTURMA
# =========================================================

def sql_olustur(soru, onceki_hata=None):
    tablo_bilgisi = """
    Veritabani tablolarimiz:

    musteriler:
    - musteri_id
    - ad_soyad
    - sehir

    siparisler:
    - siparis_id
    - musteri_id
    - tutar
    - tarih

    Sadece SELECT sorgusu yaz.
    Sadece SQL kodunu dondur.
    Markdown veya aciklama ekleme.
    """

    if onceki_hata:
        istem = f"""
        Onceki SQL sorgusu hata verdi.

        Kullanici sorusu: {soru}

        Hatali SQL: {onceki_hata}

        SQLite hata mesaji: {sql_olustur.son_hata}

        Hatayi duzelt ve yalnizca yeni SELECT sorgusunu ver.

        {tablo_bilgisi}
        """
    else:
        istem = f"""
        Asagidaki kullanici sorusunu SQL sorgusuna cevir.

        Kullanici sorusu: {soru}

        {tablo_bilgisi}
        """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=istem,
        config=types.GenerateContentConfig(
            temperature=0.1
        )
    )

    return clean_sql(response.text)


sql_olustur.son_hata = ""


# =========================================================
# 5. SQL SORGUSUNU CALISTIRMA VE HATA DUZELTME
# =========================================================

def sorguyu_calistir(soru):
    onceki_hata = None

    for deneme in range(1, 4):
        print(f"\nSQL sorgusu olusturuluyor... Deneme: {deneme}/3")

        try:
            sql_kodu = sql_olustur(soru, onceki_hata)

            print("\nOlusturulan SQL:")
            print(sql_kodu)

            if not guvenlik_kontrolu(sql_kodu):
                mesaj = "Guvenlik ihlali: SELECT disinda veya yasakli SQL komutu."
                print(f"\n[ENGELLENDI] {mesaj}")
                guvenlik_ihlalleri.append(f"Soru: {soru} | SQL: {sql_kodu}")
                rapor_kayitlari.append(mesaj)
                return

            sorgu_baslangici = time.perf_counter()

            imlec = baglanti.execute(sql_kodu)

            if imlec.description is None:
                raise sqlite3.Error("Sorgu bir SELECT sonucu dondurmedi.")

            sonuc = imlec.fetchall()
            sutunlar = [bilgi[0] for bilgi in imlec.description]

            sorgu_suresi = time.perf_counter() - sorgu_baslangici

            df = pd.DataFrame(sonuc, columns=sutunlar)

            print("\nSorgu sonucu:")
            print(df.to_string(index=False))

            print(f"\nBulunan kayit sayisi: {len(df)}")
            print(f"Sorgu suresi: {sorgu_suresi:.6f} saniye")

            rapor_kayitlari.append(
                f"Soru: {soru}\n"
                f"SQL: {sql_kodu}\n"
                f"Kayit sayisi: {len(df)}\n"
                f"Sorgu suresi: {sorgu_suresi:.6f} saniye\n"
            )

            return

        except sqlite3.Error as hata:
            print(f"\nSQLite hatasi: {hata}")

            onceki_hata = sql_kodu if "sql_kodu" in locals() else soru
            sql_olustur.son_hata = str(hata)

            rapor_kayitlari.append(f"SQLite hatasi (deneme {deneme}/3): {hata}")

            if deneme == 3:
                print("\nMaksimum deneme sayisina ulasildi. Sorgu duzeltilemedi.")

        except Exception as hata:
            print(f"\nGemini/API hatasi: {hata}")
            rapor_kayitlari.append(f"Gemini/API hatasi: {hata}")
            return


# =========================================================
# 6. GUVENLIK TESTLERI
# =========================================================

print("\n" + "=" * 55)
print("GUVENLIK TESTLERI")
print("=" * 55)

test_sorgulari = [
    ("SELECT * FROM musteriler", True),
    ("DELETE FROM musteriler", False),
    ("UPDATE musteriler SET sehir='Ankara'", False),
    ("DROP TABLE musteriler", False),
    ("INSERT INTO musteriler VALUES (1001, 'Test', 'Ankara')", False)
]

guvenlik_test_sonuclari = []

for sorgu, beklenen in test_sorgulari:
    gercek = guvenlik_kontrolu(sorgu)
    durum = "BASARILI" if gercek == beklenen else "BASARISIZ"

    print(f"{sorgu} -> {durum}")
    guvenlik_test_sonuclari.append(f"{sorgu} -> {durum}")

    if gercek != beklenen:
        guvenlik_ihlalleri.append(f"Guvenlik testi basarisiz: {sorgu}")


# =========================================================
# 7. INTERAKTIF KULLANICI EKRANI
# =========================================================

print("\n" + "=" * 55)
print("SQL ASISTANI KULLANIMA HAZIR")
print("Ornek: Istanbul'daki musterileri listele")
print("Cikmak icin 'q' yazin.")
print("=" * 55)

try:
    while True:
        kullanici_sorusu = input("\nSorunuz: ").strip()

        if kullanici_sorusu.lower() in ["q", "quit", "exit", "cikis", "çıkış"]:
            print("\nProgramdan cikiliyor...")
            break

        if not kullanici_sorusu:
            print("Lutfen bir soru girin.")
            continue

        sorguyu_calistir(kullanici_sorusu)

except KeyboardInterrupt:
    print("\nProgram kullanici tarafindan durduruldu.")


# =========================================================
# 8. RAPOR DOSYASI OLUSTURMA
# =========================================================

toplam_sure = time.perf_counter() - baslangic_zamani

with open("sql_asistan_raporu.txt", "w", encoding="utf-8") as dosya:
    dosya.write("YAPAY ZEKA DESTEKLI SQL ASISTANI RAPORU\n")
    dosya.write("=" * 55 + "\n\n")

    dosya.write("1. VERITABANI BILGILERI\n")
    dosya.write(f"Musteri sayisi: {musteri_sayisi}\n")
    dosya.write(f"Siparis sayisi: {siparis_sayisi}\n\n")

    dosya.write("2. GUVENLIK TESTLERI\n")
    for test in guvenlik_test_sonuclari:
        dosya.write(test + "\n")

    dosya.write("\n3. GUVENLIK IHLALLERI\n")
    if guvenlik_ihlalleri:
        for ihlal in guvenlik_ihlalleri:
            dosya.write(ihlal + "\n")
    else:
        dosya.write("Kaydedilmis guvenlik ihlali bulunmamaktadir.\n")

    dosya.write("\n4. SORGU VE HATA KAYITLARI\n")
    if rapor_kayitlari:
        for kayit in rapor_kayitlari:
            dosya.write(kayit + "\n")
    else:
        dosya.write("Herhangi bir sorgu kaydi bulunmamaktadir.\n")

    dosya.write("\n5. CALISMA SURESI\n")
    dosya.write(f"Toplam program suresi: {toplam_sure:.4f} saniye\n")

    dosya.write("\n6. GENEL DEGERLENDIRME\n")
    dosya.write(
        "Program SQLite veritabaninda 1000 musteri ve 1000 siparis "
        "kaydi olusturmustur. SQL sorgulari guvenlik kontrolunden "
        "gecirilmis, SELECT disindaki veritabani islemleri SQLite "
        "yetkilendirme mekanizmasiyla engellenmistir. Gemini API "
        "araciligiyla dogal dildeki sorular SQL sorgularina "
        "donusturulmus ve sorgu sonuclari Pandas DataFrame ile "
        "gosterilmistir.\n"
    )

print("\nRapor olusturuldu: sql_asistan_raporu.txt")
print(f"Toplam program suresi: {toplam_sure:.4f} saniye")
print("\nProgram sona erdi.")

baglanti.close()