from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required
from master.models import Partai, Kokab
from .services import analyze_dapil
import pileg_kokab.models as model_kokab
import pileg_prov.models as model_prov
import pileg_ri.models as model_ri

@permission_required('rebut_kursi.can_access_simulasi', raise_exception=True)
def dashboard_view(request):
    partai_list = Partai.objects.all().order_by('no_urut')
    kokab_list = Kokab.objects.all().order_by('nama')
    
    context = {
        'title': 'Dashboard Rebut Kursi',
        'partai_list': partai_list,
        'kokab_list': kokab_list,
    }
    return render(request, 'rebut_kursi/dashboard.html', context)

@permission_required('rebut_kursi.can_access_simulasi', raise_exception=True)
def simulate_view(request):
    partai_id = request.GET.get('partai_id')
    kokab_id = request.GET.get('kokab_id')
    tingkat = request.GET.get('tingkat', 'kokab')
    
    if not partai_id:
        return JsonResponse({'error': 'Partai harus dipilih'}, status=400)
    if tingkat == 'kokab' and not kokab_id:
        return JsonResponse({'error': 'Kota/Kab harus dipilih'}, status=400)
        
    partai_id = int(partai_id)
    kokab_id = int(kokab_id) if kokab_id else None
    
    total_suara_mubazir = 0
    hasil_dapil_list = []
    semua_partai_ids = list(Partai.objects.values_list('id', flat=True))

    if tingkat == 'kokab':
        dapils = model_kokab.Dapil.objects.filter(kokab_id=kokab_id).prefetch_related('kecamatan__rekap_suara_kokab__detail_suara')
    elif tingkat == 'prov':
        dapils = model_prov.Dapil.objects.all().prefetch_related('kokab__kecamatan_set__rekap_suara_prov__detail_suara')
    elif tingkat == 'ri':
        dapils = model_ri.Dapil.objects.all().prefetch_related('kokab__kecamatan_set__rekapsuara__detail_suara')
    else:
        dapils = []

    for dapil in dapils:
        suara_partai = {pid: 0 for pid in semua_partai_ids}
        total_suara_dapil = 0
        total_dpt_dapil = 0
        
        # Simpan rincian suara per kecamatan
        rincian_kecamatan = {}

        kecamatan_list = []
        if tingkat == 'kokab':
            kecamatan_list = dapil.kecamatan.all()
        else:
            for kkb in dapil.kokab.all():
                kecamatan_list.extend(kkb.kecamatan_set.all())

        for kec in kecamatan_list:
            nama_kec_tampil = f"{kec.kokab.nama} - {kec.nama}" if tingkat in ['prov', 'ri'] else kec.nama
            
            total_dpt_dapil += kec.dpt_pemilu
            rincian_kecamatan[nama_kec_tampil] = {
                'dpt': kec.dpt_pemilu,
                'partai': {pid: 0 for pid in semua_partai_ids}
            }
            
            rekap = None
            if tingkat == 'kokab' and hasattr(kec, 'rekap_suara_kokab'):
                rekap = kec.rekap_suara_kokab
            elif tingkat == 'prov' and hasattr(kec, 'rekap_suara_prov'):
                rekap = kec.rekap_suara_prov
            elif tingkat == 'ri' and hasattr(kec, 'rekapsuara'):
                rekap = kec.rekapsuara
                
            if rekap:
                for ds in rekap.detail_suara.all():
                    suara_partai[ds.partai_id] += ds.jumlah_suara
                    rincian_kecamatan[nama_kec_tampil]['partai'][ds.partai_id] += ds.jumlah_suara
                    total_suara_dapil += ds.jumlah_suara
            
        analysis = analyze_dapil(dapil.jumlah_kursi, suara_partai, partai_id)
        total_suara_mubazir += analysis['suara_mubazir']
        
        # --- LOGIKA PETA TEMPUR CERDAS (Greedy Feasibility) ---
        target_kecamatan_list = []
        
        if analysis['tambahan_suara_dibutuhkan'] > 0:
            kandidat_kecamatan = []
            
            for kec_nama, data in rincian_kecamatan.items():
                data_partai = data['partai']
                dpt_lokal = data['dpt']
                suara_kita_lokal = data_partai.get(partai_id, 0)
                total_suara_sah_lokal = sum(data_partai.values())
                golput_lokal = max(0, dpt_lokal - total_suara_sah_lokal)
                
                # Cari juara 1 (partai terbesar) di kecamatan ini, selain partai kita
                max_suara_lokal = -1
                raja_lokal_id = None
                
                for pid, suara in data_partai.items():
                    if pid != partai_id and suara > max_suara_lokal:
                        max_suara_lokal = suara
                        raja_lokal_id = pid
                
                if raja_lokal_id and max_suara_lokal > 0:
                    partai_lokal = Partai.objects.get(id=raja_lokal_id)
                    nama_partai_lokal = partai_lokal.nama
                    suara_lawan = max_suara_lokal
                    
                    # Hitung Kapasitas Potensial (10% Golput + 20% Suara Lawan)
                    kapasitas_golput = int(0.10 * golput_lokal)
                    kapasitas_rampok = int(0.20 * suara_lawan)
                    kapasitas_total = kapasitas_golput + kapasitas_rampok
                    
                    # Tentukan Status Zona (Difficulty)
                    # 1 = Mudah (Kandang Sendiri), 2 = Sedang (Swing), 3 = Sulit (Kandang Lawan)
                    if suara_kita_lokal > suara_lawan:
                        status_zona = 1
                        label_zona = "Kandang Sendiri"
                        warna_zona = "success" # Hijau
                    elif (suara_lawan - suara_kita_lokal) <= 1500:
                        status_zona = 2
                        label_zona = "Zona Tempur"
                        warna_zona = "warning" # Kuning
                    else:
                        status_zona = 3
                        label_zona = "Kandang Lawan"
                        warna_zona = "danger" # Merah

                    kandidat_kecamatan.append({
                        'nama_kecamatan': kec_nama,
                        'suara_kita': suara_kita_lokal,
                        'nama_partai': nama_partai_lokal,
                        'suara_rival': suara_lawan,
                        'golput': golput_lokal,
                        'kapasitas': kapasitas_total,
                        'status_zona': status_zona,
                        'label_zona': label_zona,
                        'warna_zona': warna_zona
                    })
            
            # URUTKAN GREEDY: Prioritaskan zona termudah (1 -> 3), lalu urutkan berdasarkan kapasitas terbesar
            kandidat_kecamatan.sort(key=lambda x: (x['status_zona'], -x['kapasitas']))
            
            # AKUMULASI GREEDY OPSI 1
            suara_terkumpul = 0
            target_defisit = analysis['tambahan_suara_dibutuhkan']
            
            for kec in kandidat_kecamatan:
                sisa_kebutuhan = target_defisit - suara_terkumpul
                if sisa_kebutuhan <= 0:
                    break 
                    
                beban_kecamatan = min(kec['kapasitas'], sisa_kebutuhan)
                kec['beban_target'] = beban_kecamatan
                suara_terkumpul += beban_kecamatan
                target_kecamatan_list.append(kec)
            
            # --- LOGIKA PETA TEMPUR OPSI 2 (Sapu Bersih Suara Hangus) ---
            target_kecamatan_opsi2 = []
            harga_kursi = analysis['harga_satu_kursi']
            
            # Hitung Alokasi Kursi Semua Partai untuk Keterangan
            alokasi_semua = {p: 0 for p in suara_partai.keys()}
            pembagi_semua = {p: 1 for p in suara_partai.keys()}
            if dapil.jumlah_kursi > 0 and sum(suara_partai.values()) > 0:
                for _ in range(dapil.jumlah_kursi):
                    pemenang = max(suara_partai.keys(), key=lambda p: suara_partai[p] / pembagi_semua[p])
                    alokasi_semua[pemenang] += 1
                    pembagi_semua[pemenang] += 2
            
            # Hitung Proksi Suara Hangus per Partai Se-Dapil
            suara_hangus_partai = {}
            keterangan_hangus_partai = {}
            for pid, suara in suara_partai.items():
                if pid == partai_id: continue
                kursi_didapat = alokasi_semua[pid]
                if harga_kursi > 0:
                    if kursi_didapat == 0:
                        suara_hangus_partai[pid] = suara # Partai gurem (hangus 100%)
                        keterangan_hangus_partai[pid] = "Gagal dapat kursi pertama"
                    else:
                        suara_hangus_partai[pid] = suara % harga_kursi # Sisa suara partai besar
                        keterangan_hangus_partai[pid] = f"Sisa suara dari kursi ke-{kursi_didapat}"
                else:
                    suara_hangus_partai[pid] = 0
                    keterangan_hangus_partai[pid] = "-"

            kandidat_opsi2 = []
            # Cache nama partai
            cache_partai = {}
            
            for kec_nama, data in rincian_kecamatan.items():
                data_partai = data['partai']
                
                for pid, suara in data_partai.items():
                    if pid == partai_id: continue
                    if suara_partai.get(pid, 0) > 0:
                        # Proporsikan suara hangus dapil ke level kecamatan
                        rasio_hangus = suara_hangus_partai[pid] / suara_partai[pid]
                        hangus_kecamatan = int(suara * rasio_hangus)
                        
                        if hangus_kecamatan > 0:
                            if pid not in cache_partai:
                                try:
                                    cache_partai[pid] = Partai.objects.get(id=pid).nama
                                except:
                                    cache_partai[pid] = f"Partai {pid}"
                                    
                            kandidat_opsi2.append({
                                'nama_kecamatan': kec_nama,
                                'nama_partai_korban': cache_partai[pid],
                                'keterangan_sisa': keterangan_hangus_partai[pid],
                                'suara_hangus_tersedia': hangus_kecamatan,
                                'kapasitas': hangus_kecamatan # Sapu bersih 100%
                            })
            
            # URUTKAN GREEDY OPSI 2 (Kapasitas Hangus Terbesar)
            kandidat_opsi2.sort(key=lambda x: x['kapasitas'], reverse=True)
            
            suara_terkumpul_opsi2 = 0
            for item in kandidat_opsi2:
                sisa_kebutuhan = target_defisit - suara_terkumpul_opsi2
                if sisa_kebutuhan <= 0:
                    break
                
                beban_kecamatan = min(item['kapasitas'], sisa_kebutuhan)
                item['beban_target'] = beban_kecamatan
                suara_terkumpul_opsi2 += beban_kecamatan
                target_kecamatan_opsi2.append(item)
                
            # --- LOGIKA PETA TEMPUR OPSI 3 (Radar Ancaman Pesaing) ---
            ancaman_pesaing = []
            for pid, suara in suara_partai.items():
                if pid == partai_id: continue
                if harga_kursi > 0:
                    pembagi_next = pembagi_semua[pid]
                    # Syarat curi kursi: (Suara / Pembagi_Next) > Harga_Kursi
                    # Defisit = (Harga_Kursi * Pembagi_Next) - Suara + 1
                    target_suara_mereka = harga_kursi * pembagi_next
                    defisit_mereka = int(target_suara_mereka - suara) + 1
                    
                    if defisit_mereka > 0:
                        if pid not in cache_partai:
                            try:
                                cache_partai[pid] = Partai.objects.get(id=pid).nama
                            except:
                                cache_partai[pid] = f"Partai {pid}"
                        
                        kursi_sekarang = alokasi_semua[pid]
                        
                        persentase_ancaman = (defisit_mereka / total_dpt_dapil) * 100 if total_dpt_dapil > 0 else 0
                        
                        if persentase_ancaman <= 3.0:
                            level_bahaya = "Sangat Berbahaya"
                            warna_bahaya = "danger"
                        elif persentase_ancaman <= 7.0:
                            level_bahaya = "Waspada"
                            warna_bahaya = "warning"
                        else:
                            level_bahaya = "Aman (Jauh)"
                            warna_bahaya = "success"
                            
                        ancaman_pesaing.append({
                            'nama_partai': cache_partai[pid],
                            'kursi_sekarang': kursi_sekarang,
                            'butuh_tambahan': defisit_mereka,
                            'level_bahaya': level_bahaya,
                            'warna_bahaya': warna_bahaya
                        })
                        
            # Urutkan dari yang defisitnya paling sedikit (Paling Mengancam)
            ancaman_pesaing.sort(key=lambda x: x['butuh_tambahan'])

        hasil_dapil_list.append({
            'nama_dapil': dapil.nama,
            'jumlah_kursi': dapil.jumlah_kursi,
            'kursi_didapat': analysis['kursi_didapat'],
            'suara_total_partai': analysis['suara_total_partai'],
            'total_suara_dapil': total_suara_dapil,
            'total_dpt_dapil': total_dpt_dapil,
            'suara_mubazir': analysis['suara_mubazir'],
            'tambahan_suara_dibutuhkan': analysis['tambahan_suara_dibutuhkan'],
            'harga_satu_kursi': analysis['harga_satu_kursi'],
            'operasi_rebut': {
                'target_kecamatan': target_kecamatan_list,
                'target_kecamatan_opsi2': target_kecamatan_opsi2,
                'ancaman_pesaing': ancaman_pesaing
            }
        })

    data = {
        'total_suara_mubazir': total_suara_mubazir,
        'dapil_list': hasil_dapil_list
    }

    return JsonResponse(data)
