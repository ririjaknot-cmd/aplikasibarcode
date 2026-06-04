import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import requests         
from io import StringIO   

st.set_page_config(page_title="Shipment Cabang", layout="centered")
st.title("📦 QR Barcode ID Cabang 2026")

# Tautan langsung ke Google Sheets Anda
ID_SHEETS_BARU = "1CiU5sn37F_GQ0Ma6oC2yyQ6Pa1ce8cMN4MG26zjO4L4"
URL_EKSPOR_LANGSUNG = f"https://google.com{ID_SHEETS_BARU}/export?format=csv"

def muat_database():
    try:
        respon = requests.get(URL_EKSPOR_LANGSUNG, timeout=10)
        respon.raise_for_status() 
        
        df_raw = pd.read_csv(StringIO(respon.text), header=None)
        
        header_idx = 0
        for idx, row in df_raw.iterrows():
            row_str = row.astype(str).str.replace('"', '').str.strip().tolist()
            if "ID" in row_str or "Tujuan Pengiriman" in row_str:
                header_idx = idx
                break
                
        df_db = pd.read_csv(StringIO(respon.text), skiprows=header_idx)
        df_db.columns = df_db.columns.astype(str).str.replace('"', '').str.replace('\n', ' ').str.strip()
        
        kolom_wajib = ['ID', 'Tujuan Pengiriman', 'Nama PIC']
        for col in kolom_wajib:
            if col not in df_db.columns:
                df_db[col] = ""
                st.warning(f"⚠️ Kolom '{col}' tidak ditemukan! Nama kolom saat ini: {list(df_db.columns[:4])}")
                
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

df_database = muat_database()

# =========================================================================
# TAMPILAN FORMULIR INPUT VERTIKAL (MENURUN)
# =========================================================================
st.subheader("📝 Formulir Input ID")
st.caption("Tips: Masukkan ID, tekan Tab/Enter untuk pindah ke Jumlah Box. Setelah isi Jumlah Box, tekan Enter atau klik tombol Validasi.")

# Menggunakan satu Form besar agar menekan enter di ID pindah ke Jumlah Box tanpa memicu validasi awal
with st.form(key="form_vertikal_shipment_sempurna"):
    # 1. Baris Pertama: Input ID
    id_inputan = st.text_input("Masukkan ID", value="").strip().replace('.0', '')
    
    # 2. Baris Kedua: Input Jumlah Box dikosongkan di awal (menggunakan teks agar bisa kosong murni)
    jumlah_box_raw = st.text_input("Jumlah Box", value="")
    
    # Tombol submit form (Satu-satunya pemicu eksekusi validasi data)
    proses_button = st.form_submit_button(label="🔍 Cek & Validasi Data", type="primary", use_container_width=True)

# Logika pemrosesan setelah tombol ditekan atau pengguna menekan Enter di kolom Jumlah Box
if proses_button:
    # Validasi inputan kosong
    if id_inputan == "":
        st.error("Silakan isi data ID terlebih dahulu!")
    elif jumlah_box_raw.strip() == "":
        st.error("Silakan isi Jumlah Box terlebih dahulu!")
    elif not jumlah_box_raw.strip().isdigit() or int(jumlah_box_raw) < 1:
        st.error("Jumlah Box harus berupa angka bulat minimal 1!")
    else:
        jumlah_box = int(jumlah_box_raw.strip())
        
        with st.spinner("Mencari data ke database..."):
            df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
            pencarian = df_database[df_database['ID_STR'] == id_inputan]
            
            if not pencarian.empty:
                tujuan_terdeteksi = str(pencarian.iloc['Tujuan Pengiriman']).strip()
                pic_terdeteksi = str(pencarian.iloc['Nama PIC']).strip()
                
                # Tampilkan data hasil validasi untuk ditinjau oleh pengguna
                st.success("✅ Data Berhasil Ditemukan! Silakan baca data sebelum mencetak.")
                st.info(f"**📍 Tujuan Pengiriman:** {tujuan_terdeteksi}")
                st.info(f"**👤 Nama PIC:** {pic_terdeteksi}")
                
                # =========================================================================
                # PEMBUATAN DOKUMEN PREVIEW & TOMBOL PRINT MANUAL
                # =========================================================================
                try:
                    html_konten = """
                    <html>
                    <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 10px; background: white; color: black; }
                        .area-tombol { margin-bottom: 20px; text-align: center; }
                        .tombol-print { 
                            background-color: #FF4B4B; 
                            color: white; 
                            border: none; 
                            padding: 12px 30px; 
                            font-size: 16px; 
                            font-weight: bold; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            width: 100%;
                        }
                        .tombol-print:hover { background-color: #D32F2F; }
                        .grid-kontainer { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
                        .kotak-label { border: 1px solid #CCCCCC; padding: 10px; text-align: center; border-radius: 4px; page-break-inside: avoid; }
                        .info-teks { font-size: 11px; text-align: left; margin-top: 5px; line-height: 14px; }
                        img { width: 100px; height: 100px; }
                        @media print { 
                            .no-print { display: none !important; } 
                        }
                    </style>
                    </head>
                    <body>
                    
                    <div class="area-tombol no-print">
                        <button class="tombol-print" onclick="window.print()">🖨️ KLIK DI SINI UNTUK CETAK SEKARANG</button>
                    </div>
                    
                    <div class="grid-kontainer">
                    """
                    
                    # Looping pembuatan QR Code berdasarkan jumlah box yang dikonversi
                    for b in range(1, jumlah_box + 1):
                        qr = qrcode.QRCode(version=1, box_size=10, border=1)
                        qr.add_data(id_inputan)
                        qr.make(fit=True)
                        img_qr = qr.make_image(fill_color="black", back_color="white")
                        
                        fp = io.BytesIO()
                        img_qr.save(fp, format="PNG")
                        fp.seek(0)
                        
                        img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                        
                        html_konten += f"""
                        <div class="kotak-label">
                            <img src="data:image/png;base64,{img_base64}" />
                            <div class="info-teks">
                                <b>ID:</b> {id_inputan}<br/>
                                <b>Box:</b> {b} dari {jumlah_box}<br/>
                                <b>Tujuan:</b> {tujuan_terdeteksi}
                            </div>
                        </div>
                        """
                    
                    html_konten += """
                    </div>
                    </body>
                    </html>
                    """
                    
                    st.subheader("🖨️ Pratinjau Lembar Cetak")
                    st.caption("Tinjau QR Code di bawah ini. Klik tombol merah di dalam kotak pratinjau untuk mencetak.")
                    components.html(html_konten, height=450, scrolling=True)
                    
                except Exception as err:
                    st.error(f"Gagal memproses pratinjau cetak: {err}")
            else:
                st.error(f"❌ ID '{id_inputan}' TIDAK DITEMUKAN di dalam Database Google Sheets!")
