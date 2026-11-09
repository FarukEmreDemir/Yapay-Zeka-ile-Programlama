import os

def oku_kullanici_dosyasi(filename):
    base_dir = "/var/www/uploads/"
    # Kullanıcıdan alınan dosya adı doğrulanmadan birleştiriliyor
    file_path = base_dir + filename
    with open(file_path, "r") as f:
        return f.read()