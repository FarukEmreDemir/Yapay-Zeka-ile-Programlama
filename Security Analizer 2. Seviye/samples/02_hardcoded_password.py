def veritabani_baglan():
    db_sifre = "SuperSecretPassword123!"
    baglanti = create_connection(password=db_sifre)
    return baglanti