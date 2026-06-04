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
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

df_database = muat_database()

# Inisialisasi session state agar data peninjauan tidak hilang saat tombol cetak diklik
if 'tujuan_terbaca' not in st.session_state:
    st.session_state.tujuan_terbaca = ""
if 'pic_terbaca' not in st.session_state:
    st.session_state.pic_terbaca = ""
if 'id_terbaca' not in st.session_state:
    st.session_state.id_terbaca = ""
if 'box_terbaca' not in st.session_state:
    st.session_state.box_terbaca = 1

st.subheader("📝 Formulir Input ID")
st.caption("Tips: Masukkan ID, tekan Tab untuk pindah ke Jumlah Box, lalu tekan Enter untuk memvalidasi data.")

# TAHAP 1: FORM INPUT VERTIKAL YANG AMAN DARI ERROR KURSOR
with st.form(key="form_input_aman", clear_on_submit=False):
    id_inputan = st.text_input("Masukkan ID", value="").strip().replace('.0', '')
    jumlah_box = st.number_input("Jumlah Box", min_value=1, value=1, step=1)
    
    # Tombol ini bertindak sebagai pemicu saat user menekan Enter di dalam form
    cek_button = st.form_submit_button(label="🔍 1. Validasi & Cek Data", type="secondary", use_container_width=True)

# Logika pencarian data hanya berjalan saat tombol Cek/Enter ditekan (Mencegah eror pengetikan)
if cek_button:
    if id_inputan == "":
        st.error("Silakan isi data ID terlebih dahulu!")
    else:
        df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
        pencarian = df_database[df_database['ID_STR'] == id_inputan]
        
        if not pencarian.empty:
            st.session_state.tujuan_terbaca = str(pencarian.iloc[0]['Tujuan Pengiriman']).strip()
            st.session_state.pic_terbaca = str(pencarian.iloc[0]['Nama PIC']).strip()
            st.session_state.id_terbaca = id_inputan
            st.session_state.box_terbaca = int(jumlah_box)
        else:
            st.session_state.tujuan_terbaca = "ID TIDAK DITEMUKAN"
            st.session_state.pic_terbaca = "TIDAK DIKETAHUI"
            st.session_state.id_terbaca = ""

# TAHAP 2: MENAMPILKAN DATA UNTUK DIBACA USER (DI LUAR FORM)
if st.session_state.tujuan_terbaca != "":
    if st.session_state.tujuan_terbaca == "ID TIDAK DITEMUKAN":
        st.error(f"❌ ID Tidak Ditemukan di dalam Database Google Sheets!")
    else:
        st.success("✅ Data Berhasil Ditemukan! Silakan tinjau data di bawah ini sebelum mencetak.")
        st.info(f"**📍 Tujuan Pengiriman:** {st.session_state.tujuan_terbaca}")
        st.info(f"**👤 Nama PIC:** {st.session_state.pic_terbaca}")
        
        st.divider()
        
        # TAHAP 3: TOMBOL CETAK MANUAL MANDIRI
        st.subheader("🖨️ Menu Pencetakan")
        if st.button("🖨️ 2. Cetak QR Code Sekarang", type="primary", use_container_width=True):
            try:
                with st.spinner("Menyiapkan dokumen cetak..."):
                    html_konten = """
                    <html>
                    <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 10px; background: white; color: black; }
                        .grid-kontainer { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
                        .kotak-label { border: 1px solid #CCCCCC; padding: 10px; text-align: center; border-radius: 4px; page-break-inside: avoid; }
                        .info-teks { font-size: 11px; text-align: left; margin-top: 5px; line-height: 14px; }
                        img { width: 100px; height: 100px; }
                    </style>
                    </head>
                    <body>
                    <div class="grid-kontainer">
                    """
                    
                    for b in range(1, st.session_state.box_terbaca + 1):
                        qr = qrcode.QRCode(version=1, box_size=10, border=1)
                        qr.add_data(st.session_state.id_terbaca)
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
                                <b>ID:</b> {st.session_state.id_terbaca}<br/>
                                <b>Box:</b> {b} dari {st.session_state.box_terbaca}<br/>
                                <b>Tujuan:</b> {st.session_state.tujuan_terbaca}
                            </div>
                        </div>
                        """
                    
                    html_konten += """
                    </div>
                    <script>window.onload = function() { window.print(); }</script>
                    </body>
                    </html>
                    """
                    
                    components.html(html_konten, height=400, scrolling=True)
                    
            except Exception as err:
                st.error(f"Gagal memproses cetak: {err}")
