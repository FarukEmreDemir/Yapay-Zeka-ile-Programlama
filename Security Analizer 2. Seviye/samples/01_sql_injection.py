def kullanici_girisi(kullanici_adi, sifre):
    sorgu = "SELECT * FROM users WHERE username = '" + kullanici_adi + "' AND password = '" + sifre + "'"
    cursor.execute(sorgu)
    return cursor.fetchone()