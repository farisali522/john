import math

def analyze_dapil(jumlah_kursi, suara_partai, target_partai_id):
    """
    suara_partai: dict {partai_id: total_suara}
    Returns: dict with metrics (kursi_didapat, suara_mubazir, target_tambahan_suara)
    """
    target_partai_id = int(target_partai_id)
    kursi_didapat = {pid: 0 for pid in suara_partai.keys()}
    pembagi = {pid: 1 for pid in suara_partai.keys()}
    
    quotients = []
    
    for _ in range(jumlah_kursi):
        partai_pemenang = None
        suara_tertinggi = -1
        
        for pid, suara in suara_partai.items():
            nilai = suara / pembagi[pid]
            if nilai > suara_tertinggi:
                suara_tertinggi = nilai
                partai_pemenang = pid
                
        if partai_pemenang is None or suara_tertinggi == 0:
            break
            
        quotients.append({
            'partai_id': partai_pemenang,
            'quotient': suara_tertinggi,
        })
        
        kursi_didapat[partai_pemenang] += 1
        pembagi[partai_pemenang] += 2

    # Cari quotient terendah yang mendapat kursi (Kursi Terakhir)
    if quotients:
        lowest_winning_quotient = quotients[-1]['quotient']
    else:
        lowest_winning_quotient = 0

    # Cari quotient tertinggi yang GAGAL mendapat kursi
    highest_failing_quotient = 0
    for pid, suara in suara_partai.items():
        nilai = suara / pembagi[pid]
        if nilai > highest_failing_quotient:
            highest_failing_quotient = nilai

    target_kursi = kursi_didapat.get(target_partai_id, 0)
    target_suara = suara_partai.get(target_partai_id, 0)

    # Hitung Suara Mubazir
    if target_kursi == 0:
        suara_mubazir = target_suara
    else:
        pembagi_kursi_terakhir_target = (target_kursi * 2) - 1
        min_suara_aman = math.floor(highest_failing_quotient * pembagi_kursi_terakhir_target) + 1
        if target_suara > min_suara_aman:
            suara_mubazir = target_suara - min_suara_aman
        else:
            suara_mubazir = 0

    # Hitung Kebutuhan Tambahan Suara untuk +1 Kursi
    pembagi_kursi_berikutnya = (target_kursi * 2) + 1
    if lowest_winning_quotient == 0:
        butuh_suara_total = 1
    else:
        butuh_suara_total = math.floor(lowest_winning_quotient * pembagi_kursi_berikutnya) + 1
        
    tambahan_suara_dibutuhkan = butuh_suara_total - target_suara
    if tambahan_suara_dibutuhkan < 0:
        tambahan_suara_dibutuhkan = 0

    return {
        'kursi_didapat': target_kursi,
        'suara_mubazir': suara_mubazir,
        'tambahan_suara_dibutuhkan': tambahan_suara_dibutuhkan,
        'suara_total_partai': target_suara,
        'harga_satu_kursi': math.floor(lowest_winning_quotient) if lowest_winning_quotient > 0 else 0
    }
