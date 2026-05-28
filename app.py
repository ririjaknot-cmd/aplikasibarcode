import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import urllib.parse
import re

st.set_page_config(page_title="Generator QR Code 50x50mm", layout="centered")
st.title("📦 Printer QR Code Otomatis (50x50mm)")
st.write("Sistem terintegrasi Google Sheets (Sheet: Draft Summary | Header Merge Baris 4-5 | Data Baris 6).")

# =========================================================================
# ⚠️ PASTIKAN LINK GOOGLE SHEETS ANDA BENAR (ANYONE WITH THE LINK AS VIEWER)
URL_SHEET = "https://docs.google.com/spreadsheets/d/1xW1mTTQzBnZ4Ah7UvRgpIR18geBfF1RrzGVvoRvZyPc/edit?usp=sharing"
# =========================================================================

# Fungsi membaca database Google Sheets khusus untuk Sheet "Draft Summary"
@st.cache_data(ttl=5) # Data disegarkan otomatis setiap 5 detik
def muat_database(url_input):
    try:
        url_str = str(url_input).strip()
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_str)
        if match:
            sheet_id = match.group(1)
        else:
            sheet_id = url_str
            
        nama_sheet_aman = urllib.parse.quote("Draft Summary")
        csv_url = f"https://google.com{sheet_id}/gviz/tq?tqx=out:csv&sheet={nama_sheet_aman}"
        
        # skiprows=3 digunakan untuk melompati baris 1, 2, dan 3.
        # Sehingga Baris 4 otomatis naik menjadi Judul Kolom (Header) resmi bagi Python
        df_db = pd.read_csv(csv_url, skiprows=3)
        
        # Karena Baris 5 adalah bagian dari Merge Cell, Python akan membacanya sebagai baris data pertama.
        # Kita harus menghapus baris pertama index ke-0 ini agar data asli di Baris 6 tidak bergeser.
        if not df_db.empty:
            df_db = df_db.drop(df_db.index[0]).reset_index(drop=True)
            
        # Bersihkan nama kolom dari spasi tidak sengaja di awal/akhir kata
        df_db.columns = df_db.columns.str.strip()
        
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal menghubungkan ke Database Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Memuat data dari cloud database Google Sheets via jaringan PC lokal
df_database = muat_database(URL_SHEET)

st.subheader("📝 Tabel Input Data")
st.caption("Tips: Isi kolom 'Masukkan ID' dan tekan Enter, maka kolom Tujuan dan Operator PIC akan otomatis terisi.")

# Menyimpan data tabel di memori halaman agar tidak hilang saat memproses ulang
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
        "Operator PIC": st.column_config.TextColumn("Nama PIC (Database)", disabled=True) # Hanya tampil di web
    }
)

# LOGIKA OTOMATISASI: Mencocokkan data secara langsung saat operator mengetik ID
diubah = False
for idx, row in df_edit.iterrows():
    id_inputan = str(row["Masukkan ID"]).strip()
    
    if id_inputan != "":
        # Pastikan kolom 'ID' (Kolom A4) ada di dalam sheet
        if 'ID' in df_database.columns:
            pencarian = df_database[df_database['ID'].astype(str).str.strip() == id_inputan]
            
            if not pencarian.empty:
                # Mengambil data dari kolom 'Tujuan Pengiriman' (D4) dan 'Nama PIC' (I4)
                tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman']) if 'Tujuan Pengiriman' in df_database.columns else "KOLOM TUJUAN TIDAK ADA"
                pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC']) if 'Nama PIC' in df_database.columns else "KOLOM PIC TIDAK ADA"
            else:
                tujuan_terdeteksi = "ID TIDAK DITEMUKAN"
                pic_terdeteksi = "TIDAK DIKETAHUI"
        else:
            tujuan_terdeteksi = "KOLOM 'ID' TIDAK COCOK"
            pic_terdeteksi = "PERIKSA BARIS 4"
            
        # Perbarui sel tabel web jika terjadi perubahan data input
        if df_edit.at[idx, "Tujuan Pengiriman"] != tujuan_terdeteksi or df_edit.at[idx, "Operator PIC"] != pic_terdeteksi:
            df_edit.at[idx, "Tujuan Pengiriman"] = tujuan_terdeteksi
            df_edit.at[idx, "Operator PIC"] = pic_terdeteksi
            diubah = True

# Jika tabel terupdate, segarkan halaman web untuk memunculkan data baru
if diubah:
    st.session_state.tabel_data = df_edit
    st.rerun()

# TOMBOL UTAMA UNTUK PROSES CETAK
if st.button("🖨️ Cetak QR Code Langsung", type="primary"):
    if df_edit.empty or df_edit['Masukkan ID'].isna().all() or df_edit['Masukkan ID'].eq('').all():
        st.error("Silakan isi data ID pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Menyiapkan lembar cetak khusus 50x50mm..."):
                
                # Desain layout kertas cetak (HTML + CSS) presisi ukuran proporsional 50mm x 50mm
                html_konten = """
                <html>
                <head>
                <style>
                    @page {
                        size: 50mm 50mm;
                        margin: 0; 
                    }
                    body { 
                        font-family: 'Arial', sans-serif; 
                        margin: 0; 
                        padding: 0;
                        background: white; 
                        color: black; 
                        width: 50mm;
                        height: 50mm;
                        box-sizing: border-box;
                    }
                    .kontainer-vertikal {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }
                    .kotak-label {
                        width: 50mm;
                        height: 50mm;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                        padding: 2mm;
                        box-sizing: border-box;
                        page-break-after: always;
                    }
                    .info-teks {
                        font-size: 11px;
                        font-weight: bold;
                        text-align: center;
                        margin-top: 1.5mm;
                        width: 100%;
                        word-wrap: break-word;
                        line-height: 14px;
                    }
                    img { 
                        width: 25mm; 
                        height: 25mm; 
                    }
                </style>
                </head>
                <body>
                <div class="kontainer-vertikal">
                """
                
                ada_data_valid = False
                
                for index, row in df_edit.iterrows():
                    if pd.isna(row['Masukkan ID']) or str(row['Masukkan ID']).strip() == "":
                        continue
                        
                    id_inputan = str(row['Masukkan ID']).strip()
                    jumlah_box = int(row['Jumlah Box']) if not pd.isna(row['Jumlah Box']) else 1
                    tujuan = str(row['Tujuan Pengiriman'])
                    
                    # Cetak label hanya jika ID terdaftar resmi di Google Sheets
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
                            
                            # Susunan kertas label cetak vertikal proporsional (Tanpa menyertakan Nama PIC)
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
                <script>
                    window.onload = function() { 
                        window.print(); 
                    }
                </script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    components.html(html_konten, height=0, width=0)
                    st.balloons()
                else:
                    st.warning("Tidak ada data valid yang bisa dicetak. Pastikan ID terdaftar di Google Sheets.")
                    
