import os
from google import genai
from google.genai import types

# API Anahtarını tanımla
client = genai.Client(api_key="AQ.Ab8RN6JdkwAJo1-HjPZuUAv3pQU340L_ShHBoaS6POCIOHN6Sg")

sistem_mesaji = """
Sen uzman bir Frontend Geliştiricisin. Kullanıcının tasarım talebine göre 3 adet tam işlevsel HTML5 sayfası üreteceksin.

KESİN KURALLAR:
1. Yanıtında giriş/çıkış açıklaması veya sohbet metni YAZMA. Sadece aşağıdaki 3 ayıraç etiketini ve altlarına ilgili saf HTML kodlarını yaz:
===INDEX.HTML===
===FORGOT_PASSWORD.HTML===
===SIGNUP.HTML===

2. Her dosya kendi içinde tam olmalıdır. Harici CSS veya JS dosyası kullanma; tüm CSS kodlarını <style> içine, tüm JS kodlarını <script> içine göm.
3. Sayfalar arası bağlantılar (href="index.html", href="forgot_password.html", href="signup.html") eksiksiz çalışmalıdır.
4. Bileşenler:
   - index.html: E-posta, Şifre (göster/gizle göz ikonlu), Giriş Yap butonu, Şifremi Unuttum linki, Üye Ol linki.
   - forgot_password.html: Şifremi Unuttum başlığı, E-posta alanı, Şifre Sıfırlama Bağlantısı Gönder butonu, Giriş sayfasına dön linki.
   - signup.html: Ad Soyad, E-posta, Şifre, Şifre Tekrar (her ikisi de göster/gizle ikonlu), Üye Ol butonu, Giriş sayfasına dön linki.
5. JavaScript ile tüm formlarda boş alan kontrolü, e-posta format kontrolü ve signup sayfasında şifre eşleşme kontrolü yapıp kullanıcıya şık uyarı mesajları göster.
"""

tasarim_talebi = input("Web sitesi tasarım talebinizi girin (Varsayılan için Enter'a basın): ").strip()
if not tasarim_talebi:
    tasarim_talebi = (
        "Modern, profesyonel, karanlık temalı bir üyelik sistemi oluştur. "
        "Mor ve mavi neon renkler kullan. Login, Forgot Password ve Signup sayfaları "
        "aynı tasarım dilini kullansın. Sayfalar arasında geçişler çalışsın. "
        "Butonların üzerine gelindiğinde parlama efekti oluşsun."
    )

print("Sayfalar üretiliyor, lütfen bekleyin...")

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=tasarim_talebi,
    config=types.GenerateContentConfig(
        system_instruction=sistem_mesaji,
        temperature=0.5,
        max_output_tokens=16000,
    )
)

ham_metin = response.text

# Etiketlere göre ayrıştırma
etiketler = [
    ("index.html", "===INDEX.HTML===", "===FORGOT_PASSWORD.HTML==="),
    ("forgot_password.html", "===FORGOT_PASSWORD.HTML===", "===SIGNUP.HTML==="),
    ("signup.html", "===SIGNUP.HTML===", None)
]

for dosya_adi, baslangic, bitis in etiketler:
    if baslangic in ham_metin:
        parca = ham_metin.split(baslangic)[1]
        if bitis and bitis in parca:
            parca = parca.split(bitis)[0]
        
        # Markdown kalıntılarını temizle
        temiz_html = parca.replace("```html", "").replace("```", "").strip()
        
        with open(dosya_adi, "w", encoding="utf-8") as f:
            f.write(temiz_html)
        print(f"[BAŞARILI] {dosya_adi} oluşturuldu.")
    else:
        print(f"[HATA] {baslangic} etiketi model çıktısında bulunamadı!")