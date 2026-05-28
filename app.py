import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import urllib.parse
import re

st.set_page_config(page_title="Generator QR Code Lokal", layout="centered")
st.title("📦 Sistem Printer QR Code Lokal (50x50mm)")
st.write("Sistem Terintegrasi Google Sheets (Tab Sheet: Master 2026 | Header Baris 1).")

# =========================================================================
# ⚠️ PASTIKAN LINK GOOGLE SHEETS ANDA BENAR (ANYONE WITH THE LINK AS VIEWER)
URL_SHEET = "https://google.com"
# =========================================================================

# Fungsi membaca database Google Sheets khusus untuk Sheet "Master 2026"
@st.cache_data(ttl=2) # Data disegarkan otomatis setiap 2 detik secara lokal
def muat_database(url_input):
    try:
        url_str = str(url_input).strip()
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_str)
        if match:
            sheet_id = match.group(1)
        else:
            sheet_id = url_str
            
        # Mengonversi nama sheet "Master 2026" menjadi format URL aman
        nama_sheet_aman = urllib.parse.quote("Master 2026")
        csv_url = f"https://google.com{sheet_id}/gviz/tq?tqx=out:csv&sheet={nama_sheet_aman}"
        
        # Langsung membaca dari awal (Baris 1 otomatis menjadi judul kolom resmi bagi Python)
        df_db = pd.read_csv(csv_url)
        
        # Bersihkan nama kolom dari spasi tidak sengaja di awal/akhir kata
        df_db.columns = df_db.columns.str.strip()
        
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal menghubungkan ke Database Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Memuat data ke memori komputer PC 1
df_database = muat_database(URL_SHEET)

st.subheader("📝 Tabel Input Data")
st.caption("Tips: Isi kolom 'Masukkan ID' dan tekan Enter, maka kolom Tujuan dan Operator PIC akan otomatis terisi.")

if 'tabel_data' not in st.session_state:
    st.session_state.tabel_data = pd.DataFrame([
        {"Masukkan ID": "", "Jumlah Box": 1, "Tujuan Pengiriman": "", "Operator PIC": ""}
    ])

# Menampilkan tabel input interaktif di layar web
df_edit = st.data_editor(
    st.session_state.tabel_data, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Masukkan ID": st.column_config.TextColumn("Masukkan ID", required=True),
        "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", min_value=1, default=1, required=True),
        "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True),
        "Operator PIC": st.column_config.TextColumn("Nama PIC (Database)", disabled=True)
    }
)

# LOGIKA OTOMATISASI: Mencocokkan data secara langsung saat operator mengetik ID
diubah = False
for idx, row in df_edit.iterrows():
    id_inputan = str(row["Masukkan ID"]).strip()
    
    if id_inputan != "":
        if 'ID' in df_database.columns:
            pencarian = df_database[df_database['ID'].astype(str).str.strip() == id_inputan]
            
            if not pencarian.empty:
                tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman']) if 'Tujuan Pengiriman' in df_database.columns else "KOLOM TUJUAN TIDAK ADA"
                pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC']) if 'Nama PIC' in df_database.columns else "KOLOM PIC TIDAK ADA"
            else:
                tujuan_terdeteksi = "ID TIDAK DITEMUKAN"
                pic_terdeteksi = "TIDAK DIKETAHUI"
        else:
            tujuan_terdeteksi = "KOLOM 'ID' TIDAK COCOK"
            pic_terdeteksi = "PERIKSA BARIS 1"
            
        if df_edit.at[idx, "Tujuan Pengiriman"] != tujuan_terdeteksi or df_edit.at[idx, "Operator PIC"] != pic_terdeteksi:
            df_edit.at[idx, "Tujuan Pengiriman"] = tujuan_terdeteksi
            df_edit.at[idx, "Operator PIC"] = pic_terdeteksi
            diubah = True

if diubah:
    st.session_state.tabel_data = df_edit
    st.rerun()

# TOMBOL UTAMA UNTUK PROSES CETAK
if st.button("🖨️ Cetak QR Code Langsung", type="primary"):
    df = pd.DataFrame(df_edit)
    
    if df.empty or df['Masukkan ID'].isna().all() or df['Masukkan ID'].eq('').all():
        st.error("Silakan isi data ID pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Menyiapkan lembar cetak khusus 50x50mm..."):
                html_konten = """
                <html>
                <head>
                <style>
                    @page { size: 50mm 50mm; margin: 0; }
                    body { 
                        font-family: 'Arial', sans-serif; margin: 0; padding: 0;
                        background: white; color: black; width: 50mm; height: 50mm; box-sizing: border-box;
                    }
                    .kontainer-vertikal { display: flex; flex-direction: column; align-items: center; }
                    .kotak-label {
                        width: 50mm; height: 50mm; display: flex; flex-direction: column;
                        justify-content: center; align-items: center; text-align: center;
                        padding: 2mm; box-sizing: border-box; page-break-after: always;
                    }
                    .info-teks {
                        font-size: 11px; font-weight: bold; text-align: center;
                        margin-top: 1.5mm; width: 100%; word-wrap: break-word; line-height: 14px;
                    }
                    img { width: 25mm; height: 25mm; }
                </style>
                </head>
                <body>
                <div class="kontainer-vertikal">
                """
                
                ada_data_valid = False
                for index, row in df.iterrows():
                    if pd.isna(row['Masukkan ID']) or str(row['Masukkan ID']).strip() == "":
                        continue
                        
                    id_inputan = str(row['Masukkan ID']).strip()
                    jumlah_box = int(row['Jumlah Box']) if not pd.isna(row['Jumlah Box']) else 1
                    tujuan = str(row['Tujuan Pengiriman'])
                    
                    if tujuan != "ID TIDAK DITEMUKAN" and "TIDAK" not in tujuan:
                        ada_data_valid = True
                        for b in range(1, jumlah_box + 1):
                            data_qr = f"{id_inputan}-{b}/{jumlah_box}-{tujuan}"
                            qr = qrcode.QRCode(version=1, box_size=10, border=1)
                            qr.add_data(data_qr)
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
                                    {tujuan}<br/>
                                    {id_inputan}<br/>
                                    {b}/{jumlah_box}
                                </div>
                            </div>
                            """
                
                html_konten += """
                </div>
                <script>window.onload = function() { window.print(); }</script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    components.html(html_konten, height=0, width=0)
                    st.balloons()
                else:
                    st.warning("Tidak ada data valid yang bisa dicetak. Pastikan ID terdaftar di Google Sheets.")
                    
        except Exception as e:
            st.error(f"⚠️ Terjadi kesalahan teknis saat memproses cetak: {e}")
