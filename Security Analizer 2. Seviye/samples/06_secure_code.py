import os

def guvenli_dosya_oku(dosya_adi):
    izinli_klasor = "/var/www/uploads"
    tam_yol = os.path.abspath(os.path.join(izinli_klasor, dosya_adi))
    
    # Dizin geçişi (Path Traversal) engelleme
    if not tam_yol.startswith(os.path.abspath(izinli_klasor)):
        raise ValueError("Yetkisiz dosya erişim denemesi!")
        
    if not os.path.isfile(tam_yol):
        return None
        
    with open(tam_yol, "r", encoding="utf-8") as f:
        return f.read()