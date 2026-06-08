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

ID_SHEETS_BARU = "1CiU5sn37F_GQ0Ma6oC2yyQ6Pa1ce8cMN4MG26zjO4L4"
URL_EKSPOR_LANGSUNG = f"https://google.com{ID_SHEETS_BARU}/export?format=csv"

# Inisialisasi Session State agar data tidak hilang saat halaman di-refresh akibat interaksi HTML
if "data_tervalidasi" not in st.session_state:
    st.session_state.data_tervalidasi = None

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
                st.warning(f"⚠️ Kolom '{col}' tidak ditemukan! Nama kolom yang ada saat ini: {list(df_db.columns[:4])}")
                
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

df_database = muat_database()

st.subheader("📝 Formulir Input ID")
st.caption("Tips: Masukkan ID, tekan Tab untuk pindah ke Jumlah Box. Validasi dilakukan dengan menekan tombol di bawah.")

with st.form(key="form_vertikal_shipment", enter_to_submit=False):
    id_inputan = st.text_input("Masukkan ID", value="").strip().replace('.0', '')
    
    # Nilai awal diubah ke 1 dan min_value=1 agar tombol + dan - langsung aktif sejak awal
    jumlah_box = st.number_input("Jumlah Box", min_value=1, value=1, step=1)
    
    proses_button = st.form_submit_button(label="🔍 Cek & Validasi ID", type="primary", use_container_width=True)

# PROSES VALIDASI DATA (Dipicu saat tombol form ditekan)
if proses_button:
    if id_inputan == "":
        st.error("Silakan isi Nomor ID terlebih dahulu!")
        st.session_state.data_tervalidasi = None
    else:
        with st.spinner("Mencari data ke database..."):
            df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
            pencarian = df_database[df_database['ID_STR'] == id_inputan]
            
            if not pencarian.empty:
                # Simpan hasil pencarian ke session state agar aman dari refresh halaman
                st.session_state.data_tervalidasi = {
                    "id_inputan": id_inputan,
                    "jumlah_box": int(jumlah_box),
                    "tujuan": str(pencarian.iloc[0]['Tujuan Pengiriman']).strip(),
                    "pic": str(pencarian.iloc[0]['Nama PIC']).strip()
                }
            else:
                st.error(f"❌ ID '{id_inputan}' tidak ditemukan di database!")
                st.session_state.data_tervalidasi = None

# OUTPUT PREVIEW DAN TOMBOL CETAK (Dikontrol oleh session state agar tetap menetap di layar)
if st.session_state.data_tervalidasi:
    data = st.session_state.data_tervalidasi
    
    st.success("✅ Data Berhasil Ditemukan! Pastikan Data Sudah Sesuai.")
    st.info(f"**📍 Tujuan Pengiriman:** {data['tujuan']}")
    st.info(f"**🤴 Nama PIC:** {data['pic']}")
    
    try:
        html_konten = """
        <html>
        <head>
        <style>
            @page {
                size: 50mm 50mm;
                margin: 0;
            }
            body { 
                font-family: 'Calibri', Arial, sans-serif; 
                font-size: 11pt;
                margin: 0; 
                padding: 0;
                background: #f9f9f9; 
                color: black; 
                box-sizing: border-box;
            }
            /* Menengahkan area tombol cetak */
            .area-tombol { 
                margin: 15px 0; 
                display: flex;
                justify-content: center;
                width: 100%;
            }
            .tombol-print { 
                background-color: #FF4B4B; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                font-size: 14px; 
                font-weight: bold; 
                border-radius: 4px; 
                cursor: pointer; 
                min-width: 150px;
                box-shadow: 0px 2px 5px rgba(0,0,0,0.15);
            }
            .tombol-print:hover { background-color: #D32F2F; }
            
            /* GRID PREVIEW: Menyusun label rapi ke arah kanan jika berjumlah banyak */
            .wrapper-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(50mm, 1fr));
                gap: 15px;
                padding: 15px;
                justify-items: center;
            }
            
            /* KOTAK LABEL: Visualisasi potongan kertas di layar aplikasi */
            .kotak-label { 
                width: 50mm;
                height: 50mm;
                padding: 2mm;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                box-sizing: border-box;
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
            }
            .info-teks { 
                margin-top: 3px; 
                line-height: 1.15; 
                width: 100%;
                word-wrap: break-word;
            }
            .tujuan-bold {
                font-weight: bold;
                font-size: 13pt;
            }
            img.barcode-qr { 
                width: 2.3cm; 
                height: 2.3cm; 
                object-fit: contain; 
            }
            
            /* ATURAN SAAT DICETAK: Menghapus layout grid, bayangan, dan border */
            @media print { 
                .no-print { display: none !important; } 
                body { background: white; }
                .wrapper-grid { 
                    display: block !important; 
                    padding: 0 !important; 
                    gap: 0 !important; 
                }
                .kotak-label { 
                    border: none !important; 
                    box-shadow: none !important; 
                    border-radius: 0 !important;
                    page-break-inside: avoid !important;
                    page-break-after: always !important;
                }
            }
        </style>
        </head>
        <body>
        
        <div class="area-tombol no-print">
            <button class="tombol-print" onclick="window.print()">🖨️ Print Label</button>
        </div>

        <div class="wrapper-grid">
        """
        
        for b in range(1, data['jumlah_box'] + 1):
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(data['id_inputan'])
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            fp = io.BytesIO()
            img_qr.save(fp, format="PNG")
            fp.seek(0)
            
            img_base64 = base64.b64encode(fp.read()).decode('utf-8')
            
            html_konten += f"""
            <div class="kotak-label">
                <img class="barcode-qr" src="data:image/png;base64,{img_base64}" />
                <div class="info-teks">
                    <span class="tujuan-bold">{data['tujuan']}</span><br/>
                    {data['id_inputan']}<br/>
                    {b}/{data['jumlah_box']}
                </div>
            </div>
            """
        
        html_konten += """
        </div>
        </body>
        </html>
        """

        # Tinggi komponen dinaikkan ke 500 agar memberi ruang yang cukup bagi grid preview
        components.html(html_konten, height=500, scrolling=True)
        
    except Exception as e:
        st.error(f"⚠️ Gagal membuat komponen cetak: {e}")
