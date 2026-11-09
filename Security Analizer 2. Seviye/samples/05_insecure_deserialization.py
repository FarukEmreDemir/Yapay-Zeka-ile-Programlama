import pickle

def veri_yukle(gelen_veri):
    # Güvenilmeyen kaynaktan alınan baytlar doğrudan açılıyor
    kullanici_nesnesi = pickle.loads(gelen_veri)
    return kullanici_nesnesi