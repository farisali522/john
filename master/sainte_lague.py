def hitung_sainte_lague(jumlah_kursi, suara_partai):
    """
    Algoritma perhitungan kursi metode Sainte-Laguë.
    
    :param jumlah_kursi: Integer, total kursi yang diperebutkan di Dapil tersebut.
    :param suara_partai: Dictionary, format {partai_id: total_suara_sah}
    :return: Dictionary, format {partai_id: total_kursi_yang_didapat}
    """
    
    # Inisialisasi perolehan kursi setiap partai menjadi 0
    kursi_didapat = {partai_id: 0 for partai_id in suara_partai.keys()}
    
    # Simpan pembagi saat ini untuk setiap partai (dimulai dari 1)
    pembagi = {partai_id: 1 for partai_id in suara_partai.keys()}
    
    # Lakukan pembagian kursi satu per satu
    for _ in range(jumlah_kursi):
        partai_pemenang = None
        suara_tertinggi = -1
        
        # Cari partai dengan nilai (suara / pembagi) tertinggi saat ini
        for partai_id, suara in suara_partai.items():
            nilai_saat_ini = suara / pembagi[partai_id]
            
            if nilai_saat_ini > suara_tertinggi:
                suara_tertinggi = nilai_saat_ini
                partai_pemenang = partai_id
        
        # Jika semua suara 0 atau tidak ada partai valid
        if partai_pemenang is None or suara_tertinggi == 0:
            break
            
        # Alokasikan 1 kursi untuk partai pemenang di putaran ini
        kursi_didapat[partai_pemenang] += 1
        
        # Naikkan angka pembagi partai pemenang ke bilangan ganjil berikutnya (+2)
        pembagi[partai_pemenang] += 2

    return kursi_didapat
