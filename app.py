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
URL_EKSPOR_LANGSUNG = f"https://docs.google.com/spreadsheets/d/{ID_SHEETS_BARU}/export?format=csv"

def muat_database():
    try:
        respon = requests.get(URL_EKSPOR_LANGSUNG, timeout=10)
        respon.raise_for_status() 
        
        # Baca teks mentah CSV tanpa memotong baris terlebih dahulu
        df_raw = pd.read_csv(StringIO(respon.text), header=None)
        
        # Cari di baris mana kata "ID" berada (Deteksi Otomatis letak Header)
        header_idx = 0
        for idx, row in df_raw.iterrows():
            row_str = row.astype(str).str.replace('"', '').str.strip().tolist()
            if "ID" in row_str or "Tujuan Pengiriman" in row_str:
                header_idx = idx
                break
                
        # Baca ulang CSV dari baris header yang tepat
        df_db = pd.read_csv(StringIO(respon.text), skiprows=header_idx)
        df_db.columns = df_db.columns.astype(str).str.replace('"', '').str.replace('\n', ' ').str.strip()
        
        # Cek ketersediaan kolom wajib
        kolom_wajib = ['ID', 'Tujuan Pengiriman', 'Nama PIC']
        for col in kolom_wajib:
            if col not in df_db.columns:
                df_db[col] = ""
                st.warning(f"⚠️ Kolom '{col}' tidak ditemukan! Nama kolom yang ada saat ini: {list(df_db.columns[:4])}")
                
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Jalankan fungsi muat data
df_database = muat_database()

# =========================================================================
# TAMPILAN FORMULIR INPUT VERTIKAL (MENURUN)
# =========================================================================
st.subheader("📝 Formulir Input ID")
st.caption("Tips: Masukkan ID, tekan Tab/Enter untuk pindah ke Jumlah Box. Validasi dilakukan dengan menekan tombol di bawah.")

# Form dibuat vertikal menurun ke bawah dengan parameter pengunci enter
with st.form(key="form_vertikal_shipment", enter_to_submit=False):
    # 1. Baris Pertama: Input ID
    id_inputan = st.text_input("Masukkan ID", value="").strip().replace('.0', '')
    
    # 2. Baris Kedua: Input Jumlah Box (Kondisi Awal Kosong)
    jumlah_box = st.number_input("Jumlah Box", min_value=1, value=None, step=1)
    
    # Tombol submit form (Memproses data ke layar tanpa langsung memicu print)
    proses_button = st.form_submit_button(label="🔍 Cek & Validasi ID", type="primary", use_container_width=True)

# Logika pemrosesan setelah tombol ditekan atau pengguna menekan Enter
if proses_button:
    if id_inputan == "":
        st.error("Silakan isi Nomor ID terlebih dahulu!")
    elif jumlah_box is None:
        st.error("Silakan isi Jumlah Box terlebih dahulu!")
    else:
        with st.spinner("Mencari data ke database..."):
            # Sinkronisasi format tipe data ID agar pencarian akurat
            df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
            pencarian = df_database[df_database['ID_STR'] == id_inputan]
            
            if not pencarian.empty:
                tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman']).strip()
                pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC']).strip()
                
                # Menampilkan Informasi Data Secara Vertikal untuk dibaca pengguna
                st.success("✅ Data Berhasil Ditemukan! Pastikan Data Sudah Sesuai.")
                
                st.info(f"**📍 Tujuan Pengiriman:** {tujuan_terdeteksi}")
                st.info(f"**👤 Nama PIC:** {pic_terdeteksi}")
                
                # =========================================================================
                # PEMBUATAN DOKUMEN PREVIEW & TOMBOL PRINT MANUAL
                # =========================================================================
                try:
                    # PERBAIKAN UKURAN KERTAS 50x50mm & KONTEN RATAKAN TENGAH
                    html_konten = """
                    <html>
                    <head>
                    <style>
                        @page {
                            size: 50mm 50mm;
                            margin: 0;
                        }
                        body { 
                            font-family: Arial, sans-serif; 
                            margin: 0; 
                            padding: 0;
                            background: white; 
                            color: black; 
                            width: 50mm;
                            height: 50mm;
                            box-sizing: border-box;
                        }
                        .area-tombol { margin: 5px; text-align: center; }
                        .tombol-print { 
                            background-color: #FF4B4B; 
                            color: white; 
                            border: none; 
                            padding: 8px; 
                            font-size: 13px; 
                            font-weight: bold; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            width: 90%;
                        }
                        .tombol-print:hover { background-color: #D32F2F; }
                        
                        /* Layout Kontainer Utama Label */
                        .kotak-label { 
                            width: 50mm;
                            height: 50mm;
                            padding: 3mm;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            align-items: center;
                            text-align: center;
                            box-sizing: border-box;
                            page-break-inside: avoid;
                            page-break-after: always;
                        }
                        .info-teks { 
                            font-size: 10px; 
                            margin-top: 4px; 
                            line-height: 13px; 
                            font-weight: bold;
                        }
                        img { width: 30mm; height: 30mm; object-fit: contain; }
                        
                        @media print { 
                            .no-print { display: none !important; } 
                        }
                    </style>
                    </head>
                    <body>
                    
                    <div class="area-tombol no-print">
                        <button class="tombol-print" onclick="window.print()">🖨️ Print</button>
                    </div>
                    """
                    
                    # Looping pembuatan QR Code berdasarkan jumlah box
                    for b in range(1, int(jumlah_box) + 1):
                        qr = qrcode.QRCode(version=1, box_size=10, border=1)
                        qr.add_data(id_inputan)
                        qr.make(fit=True)
                        img_qr = qr.make_image(fill_color="black", back_color="white")
                        
                        fp = io.BytesIO()
                        img_qr.save(fp, format="PNG")
                        fp.seek(0)
                        
                        img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                        
                        # PERBAIKAN KONTEN: Menghapus sub-judul "ID:", "Box:", dan "Tujuan:"
                        html_konten += f"""
                        <div class="kotak-label">
                            <img src="data:image/png;base64,{img_base64}" />
                            <div class="info-teks">
                                {id_inputan}<br/>
                                {b} dari {jumlah_box}<br/>
                                {tujuan_terdeteksi}
                            </div>
                        </div>
                        """
                    
                    html_konten += """
                    </body>
                    </html>
                    """
            
                    components.html(html_konten, height=450, scrolling=True)
                    
                except Exception as err:
                    st.error(f"Gagal memproses pratinjau cetak: {err}") # 👈 PERBAIKAN: Melengkapi baris terpotong
            else:
                # Kondisi jika ID yang dicari tidak ada di database Google Sheets
                st.error(f"❌ ID '{id_inputan}' TIDAK DITEMUKAN di dalam Database Google Sheets!")
