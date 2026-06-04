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
st.caption("Tips: Masukkan ID, tekan Tab untuk pindah ke Jumlah Box, lalu tekan Enter untuk melihat data tujuan.")

# Menggunakan widget standar Streamlit (bukan st.form) agar data langsung terproses saat Enter
id_inputan = st.text_input("Masukkan ID", value="").strip().replace('.0', '')
jumlah_box = st.number_input("Jumlah Box", min_value=1, value=1, step=1)

# Wadah logika pemrosesan data saat ID diisi
if id_inputan != "":
    # Sinkronisasi format tipe data ID agar pencarian akurat
    df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
    pencarian = df_database[df_database['ID_STR'] == id_inputan]
    
    if not pencarian.empty:
        tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman']).strip()
        pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC']).strip()
        
        # 1. TAMPILKAN DATA UNTUK DIBACA USER TERLEBIH DAHULU
        st.success("✅ Data Berhasil Ditemukan!")
        
        # Desain vertikal menurun yang nyaman dibaca
        st.info(f"**📍 Tujuan Pengiriman:** {tujuan_terdeteksi}")
        st.info(f"**👤 Nama PIC:** {pic_terdeteksi}")
        
        st.divider() # Garis pembatas pembacaan data
        
        # 2. TOMBOL CETAK MANUAL (Jendela print baru muncul jika tombol ini diklik)
        st.subheader("🖨️ Menu Pencetakan")
        if st.button("🖨️ Cetak QR Code Sekarang", type="primary", use_container_width=True):
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
                    <script>window.onload = function() { window.print(); }</script>
                    </body>
                    </html>
                    """
                    
                    # Tampilkan pratinjau lembar cetak dan picu window.print() browser
                    components.html(html_konten, height=400, scrolling=True)
                    
            except Exception as err:
                st.error(f"Gagal memproses cetak: {err}")
    else:
        # Kondisi jika ID yang dicari tidak ada di database Google Sheets
        st.error(f"❌ ID '{id_inputan}' TIDAK DITEMUKAN di dalam Database Google Sheets!")
