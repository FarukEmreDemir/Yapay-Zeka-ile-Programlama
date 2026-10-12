import json
import os
import google.generativeai as genai

# Gemini API Yapılandırması
# API anahtarınızı ortam değişkenine (GEMINI_API_KEY) tanımlayabilir veya doğrudan buraya yazabilirsiniz.
API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KjjDRgiglyM1loBq7OO-nHBAoOKXImvqJGwOnCoavqxg")
genai.configure(api_key=API_KEY)

DOSYA_ADI = "urunler.json"

# ==========================================
# 1. DOSYA VE VERİ YÖNETİMİ FONKSİYONLARI
# ==========================================

def dosyadan_yukle():
    """urunler.json dosyasından ürün listesini yükler. Dosya yoksa veya bozuksa liste döner."""
    if not os.path.exists(DOSYA_ADI):
        return []
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            return veri if isinstance(veri, list) else []
    except (json.JSONDecodeError, IOError):
        print("\n[UYARI] Veri dosyası okunamadı veya bozuk. Boş liste ile devam ediliyor.")
        return []

def dosyaya_kaydet(urunler):
    """Ürün listesini urunler.json dosyasına formatlı şekilde kaydeder."""
    try:
        with open(DOSYA_ADI, "w", encoding="utf-8") as f:
            json.dump(urunler, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"\n[HATA] Dosya kaydedilirken sorun oluştu: {e}")

def yeni_kod_uret(urunler):
    """URN-0001 formatında bir sonraki benzersiz ürün kodunu üretir."""
    if not urunler:
        return "URN-0001"
    
    numaralar = []
    for u in urunler:
        kod = u.get("urun_kodu", "")
        if kod.startswith("URN-") and kod[4:].isdigit():
            numaralar.append(int(kod[4:]))
            
    son_no = max(numaralar) if numaralar else 0
    return f"URN-{son_no + 1:04d}"

def stok_durumu_kontrol(stok):
    """Stok miktarına göre uyarı mesajını yazdırır."""
    if stok == 0:
        print("[UYARI] STOKTA YOK!")
    elif 1 <= stok <= 4:
        print(f"[UYARI] KRİTİK STOK! Yalnızca {stok} adet kaldı.")

# ==========================================
# 2. GEMINI API ENTEGRASYONU
# ==========================================

def e_ticaret_api_analizi(aciklama):
    """
    Ürün açıklamasını Gemini API'ye gönderir ve JSON olarak ayrıştırılmış sözlük (dict) döner.
    """
    prompt = f"""
    Aşağıdaki ürün açıklamasını analiz et ve belirtilen JSON şemasına birebir uygun çıktı ver:
    Ürün Açıklaması: "{aciklama}"

    İstenen JSON formatı:
    {{
        "urun_adi": "kısa ve profesyonel ürün adı",
        "kategori": "uygun kategori yolu (örn: Outdoor / Kamp)",
        "seo_etiketleri": "üç adet virgülle ayrılmış SEO etiketi",
        "satis_aciklamasi": "tam olarak iki cümlelik dikkat çekici satış açıklaması"
    }}
    """
    try:
        model = genai.GenerativeModel(
            model_name="gemini-3.8-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        veri = json.loads(response.text)
        
        zorunlu_alanlar = ["urun_adi", "kategori", "seo_etiketleri", "satis_aciklamasi"]
        if not all(alan in veri for alan in zorunlu_alanlar):
            print("\n[HATA] API yanıtında zorunlu alanlar eksik.")
            return None
        return veri
    except Exception as e:
        print(f"\n[HATA] Gemini API çağrısı sırasında bir sorun oluştu: {e}")
        return None

# ==========================================
# 3. KULLANICI GİRDİ DOĞRULAMA YARDIMCILARI
# ==========================================

def pozitif_sayi_al(mesaj, tip=float):
    """Negatif olmayan ve sayısal girdi alana kadar kullanıcıyı yönlendirir."""
    while True:
        deger = input(mesaj).strip()
        try:
            sayi = tip(deger)
            if sayi < 0:
                print("[HATA] Değer negatif olamaz. Lütfen 0 veya daha büyük bir değer girin.")
                continue
            return sayi
        except ValueError:
            print("[HATA] Geçersiz giriş. Lütfen sayısal bir değer giriniz.")

# ==========================================
# 4. YÖNETİM PANELİ İŞLEMLERİ
# ==========================================

def yeni_urun_ekle():
    print("\n--- YENİ ÜRÜN EKLE ---")
    aciklama = input("Ürün açıklaması: ").strip()
    if not aciklama:
        print("[HATA] Ürün açıklaması boş bırakılamaz.")
        return

    fiyat = pozitif_sayi_al("Ürün fiyatı: ", float)
    stok = pozitif_sayi_al("Stok miktarı: ", int)

    print("[API] Ürün bilgileri oluşturuluyor...")
    api_sonucu = e_ticaret_api_analizi(aciklama)
    if not api_sonucu:
        print("[BAŞARISIZ] Ürün kaydedilemedi.")
        return

    urunler = dosyadan_yukle()
    yeni_kod = yeni_kod_uret(urunler)

    yeni_kayit = {
        "urun_kodu": yeni_kod,
        "urun_adi": api_sonucu["urun_adi"],
        "kategori": api_sonucu["kategori"],
        "seo_etiketleri": api_sonucu["seo_etiketleri"],
        "satis_aciklamasi": api_sonucu["satis_aciklamasi"],
        "fiyat": fiyat,
        "stok": stok
    }

    urunler.append(yeni_kayit)
    dosyaya_kaydet(urunler)

    print("[BAŞARILI] Ürün kaydedildi.")
    print(f"Ürün Kodu : {yeni_kayit['urun_kodu']}")
    print(f"Ürün Adı  : {yeni_kayit['urun_adi']}")
    print(f"Kategori  : {yeni_kayit['kategori']}")
    print(f"Fiyat     : {yeni_kayit['fiyat']} TL")
    print(f"Stok      : {yeni_kayit['stok']}")
    print(f"SEO       : {yeni_kayit['seo_etiketleri']}")
    stok_durumu_kontrol(stok)

def urunleri_listele():
    print("\n--- ÜRÜN LİSTESİ ---")
    urunler = dosyadan_yukle()
    if not urunler:
        print("Kayıtlı ürün bulunmamaktadır.")
        return

    for u in urunler:
        print("-" * 45)
        print(f"Kod      : {u.get('urun_kodu')}")
        print(f"Adı      : {u.get('urun_adi')}")
        print(f"Kategori : {u.get('kategori')}")
        print(f"Fiyat    : {u.get('fiyat')} TL")
        print(f"Stok     : {u.get('stok')}")
        stok_durumu_kontrol(u.get("stok", 0))
    print("-" * 45)

def urun_ara():
    print("\n--- ÜRÜN ARA ---")
    aranan = input("Aranacak ürün (Ad veya Kod): ").strip().lower()
    if not aranan:
        print("[HATA] Arama terimi boş olamaz.")
        return

    urunler = dosyadan_yukle()
    bulunanlar = [
        u for u in urunler
        if aranan in u.get("urun_kodu", "").lower() or aranan in u.get("urun_adi", "").lower()
    ]

    if not bulunanlar:
        print("[SONUÇ] Eşleşen ürün bulunamadı.")
        return

    print(f"[SONUÇ] {len(bulunanlar)} ürün bulundu:")
    for u in bulunanlar:
        print(f"-> {u.get('urun_kodu')} | {u.get('urun_adi')} | Stok: {u.get('stok')} | Fiyat: {u.get('fiyat')} TL")

def stok_guncelle():
    print("\n--- STOK GÜNCELLE ---")
    kod = input("Ürün kodu: ").strip().upper()
    urunler = dosyadan_yukle()

    hedef_urun = None
    for u in urunler:
        if u.get("urun_kodu", "").upper() == kod:
            hedef_urun = u
            break

    if not hedef_urun:
        print(f"[HATA] '{kod}' kodlu ürün bulunamadı.")
        return

    eski_stok = hedef_urun.get("stok", 0)
    yeni_stok = pozitif_sayi_al("Yeni stok miktarı: ", int)

    hedef_urun["stok"] = yeni_stok
    dosyaya_kaydet(urunler)

    print(f"[BAŞARILI] Stok {eski_stok} -> {yeni_stok} olarak güncellendi.")
    stok_durumu_kontrol(yeni_stok)

# ==========================================
# 5. ANA PROGRAM DÖNGÜSÜ
# ==========================================

def ana_menu():
    while True:
        print("\n== E-TİCARET YÖNETİM PANELİ ==")
        print("1 - Yeni Ürün Ekle")
        print("2 - Ürünleri Listele")
        print("3 - Ürün Ara")
        print("4 - Stok Güncelle")
        print("5 - Çıkış")
        
        secim = input("Seçiminiz: ").strip()

        if secim == "1":
            yeni_urun_ekle()
        elif secim == "2":
            urunleri_listele()
        elif secim == "3":
            urun_ara()
        elif secim == "4":
            stok_guncelle()
        elif secim == "5":
            print("\nProgramdan çıkılıyor. İyi çalışmalar!")
            break
        else:
            print("\n[HATA] Geçersiz seçim! Lütfen 1-5 arasında bir seçenek giriniz.")

if __name__ == "__main__":
    ana_menu()