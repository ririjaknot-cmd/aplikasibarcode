import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import requests         # Pastikan ini ada
from io import StringIO   # Pastikan ini ada

st.set_page_config(page_title="Generator QR Code Massal", layout="centered")
st.title("📦 Sistem Input & Cetak QR Code Otomatis")
st.write("Tujuan Pengiriman & Nama PIC (Operator) akan terisi otomatis di dalam tabel saat ID Unik diisi.")

# =========================================================================
# PERBAIKAN TOTAL: LANGSUNG GUNAKAN URL EKSPOR CSV YANG VALID DAN BENAR
# =========================================================================
URL_EKSPOR_LANGSUNG = "https://google.com"

@st.cache_data(ttl=5) # Data disegarkan otomatis setiap 5 detik
def muat_database():
    try:
        # Menarik data menggunakan requests dengan batas waktu 10 detik
        respon = requests.get(URL_EKSPOR_LANGSUNG, timeout=10)
        respon.raise_for_status() # Memastikan status HTTP 200 OK
        
        # Membaca teks mentah CSV tanpa memotong baris terlebih dahulu
        df_raw = pd.read_csv(StringIO(respon.text), header=None)
        
        # Cari di baris mana kata "ID" atau "Tujuan Pengiriman" berada (Deteksi Otomatis)
        header_idx = 0
        for idx, row in df_raw.iterrows():
            # Bersihkan teks di setiap sel dari tanda kutip dan spasi untuk pencarian akurat
            row_str = row.astype(str).str.replace('"', '').str.strip().tolist()
            if "ID" in row_str or "Tujuan Pengiriman" in row_str:
                header_idx = idx
                break
                
        # Baca ulang CSV dari baris header yang tepat
        df_db = pd.read_csv(StringIO(respon.text), skiprows=header_idx)
        
        # PERBAIKAN UTAMA: Bersihkan nama kolom dari tanda kutip, enter (\n), dan spasi liar
        df_db.columns = df_db.columns.astype(str).str.replace('"', '').str.replace('\n', ' ').str.strip()
        
        # Validasi darurat jika kolom wajib hilang
        kolom_wajib = ['ID', 'Tujuan Pengiriman', 'Nama PIC']
        for col in kolom_wajib:
            if col not in df_db.columns:
                df_db[col] = ""
                st.warning(f"⚠️ Kolom '{col}' tidak ditemukan di Google Sheets!")
                
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal menghubungkan ke Database Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Memuat data dari cloud database (Sekarang tanpa memasukkan parameter URL)
df_database = muat_database()

st.subheader("📝 Tabel Input Data")
st.caption("Tips: Isi kolom 'Masukkan ID' dan tekan Enter, maka kolom Tujuan dan Operator PIC akan otomatis terisi.")

# Menggunakan session state agar data inputan di tabel tidak hilang
if 'tabel_data' not in st.session_state:
    st.session_state.tabel_data = pd.DataFrame([
        {"Masukkan ID": "", "Jumlah Box": 1, "Tujuan Pengiriman": "", "Operator PIC": ""}
    ])

# Menampilkan tabel input interaktif
df_edit = st.data_editor(
    st.session_state.tabel_data, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Masukkan ID": st.column_config.TextColumn("Masukkan ID", required=True),
        "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", min_value=1, default=1, required=True),
        "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True),
        "Operator PIC": st.column_config.TextColumn("Operator PIC", disabled=True)
    },
    key="editor_utama"
)

# LOGIKA OTOMATISASI: Memproses perubahan data tanpa memicu Infinite Loop
diubah = False
df_proses = df_edit.copy()

for idx, row in df_proses.iterrows():
    id_inputan = str(row["Masukkan ID"]).strip()
    
    if id_inputan != "" and id_inputan != "None" and not pd.isna(row["Masukkan ID"]):
        # Cari di database Google Sheets berdasarkan kolom 'ID'
        pencarian = df_database[df_database['ID'].astype(str).str.strip() == id_inputan]
        
        if not pencarian.empty:
            tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman'])
            pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC'])
        else:
            tujuan_terdeteksi = "ID TIDAK DITEMUKAN"
            pic_terdeteksi = "TIDAK DIKETAHUI"
            
        # Perbarui isi dataframe sementara jika ada perbedaan data
        if row["Tujuan Pengiriman"] != tujuan_terdeteksi or row["Operator PIC"] != pic_terdeteksi:
            df_proses.at[idx, "Tujuan Pengiriman"] = tujuan_terdeteksi
            df_proses.at[idx, "Operator PIC"] = pic_terdeteksi
            diubah = True

# Jika ada perubahan pemicu otomatisasi, simpan ke session state dan refresh sekali saja
if diubah:
    st.session_state.tabel_data = df_proses
    st.rerun()

# TOMBOL UTAMA UNTUK PROSES CETAK
if st.button("🖨️ Cetak QR Code Langsung", type="primary"):
    if df_proses.empty or df_proses['Masukkan ID'].isna().all() or df_proses['Masukkan ID'].eq('').all():
        st.error("Silakan isi data ID pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Menyiapkan lembar cetak QR Code..."):
                
                # Desain layout kertas cetak (HTML + CSS) bersih 3 kolom
                html_konten = """
                <html>
                <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 10px; background: white; color: black; }
                    .grid-kontainer {
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 15px;
                    }
                    .kotak-label {
                        border: 1px solid #CCCCCC;
                        padding: 10px;
                        text-align: center;
                        border-radius: 4px;
                        page-break-inside: avoid;
                    }
                    .info-teks {
                        font-size: 11px;
                        text-align: left;
                        margin-top: 5px;
                        line-height: 14px;
                    }
                    img { width: 100px; height: 100px; }
                    @media print {
                        .no-print { display: none !important; }
                    }
                </style>
                </head>
                <body>
                <div class="grid-kontainer">
                """
                
                ada_data_valid = False
                
                for index, row in df_proses.iterrows():
                    if pd.isna(row['Masukkan ID']) or str(row['Masukkan ID']).strip() == "":
                        continue
                        
                    id_inputan = str(row['Masukkan ID']).strip()
                    jumlah_box = int(row['Jumlah Box']) if not pd.isna(row['Jumlah Box']) else 1
                    tujuan = str(row['Tujuan Pengiriman'])
                    
                    # Pembuatan gambar QR Code (Hanya jika ID valid ditemukan di Google Sheets)
                    if tujuan != "ID TIDAK DITEMUKAN" and tujuan != "":
                        ada_data_valid = True
                        for b in range(1, jumlah_box + 1):
                            qr = qrcode.QRCode(version=1, box_size=10, border=1)
                            qr.add_data(id_inputan)
                            qr.make(fit=True)
                            img_qr = qr.make_image(fill_color="black", back_color="white")
                            
                            fp = io.BytesIO()
                            img_qr.save(fp, format="PNG")
                            fp.seek(0)
                            
                            img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                            
                            # Tampilan Kertas Label Cetak (Perbaikan tag penutup HTML)
                            html_konten += f"""
                            <div class="kotak-label">
                                <img src="data:image/png;base64,{img_base64}" />
                                <div class="info-teks">
                                    <b>ID:</b> {id_inputan}<br/>
                                    <b>Box:</b> {b} dari {jumlah_box}<br/>
                                    <b>Tujuan:</b> {tujuan}
                                </div>
                            </div>
                            """
                
                html_konten += """
                </div>
                <script>
                    window.onload = function() { window.print(); }
                </script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    # Menampilkan jendela cetak print otomatis menggunakan iframe tersembunyi
                    components.html(html_konten, height=600, scrolling=True)
                else:
                    st.warning("⚠️ Tidak ada ID valid yang siap dicetak. Pastikan status bukan 'ID TIDAK DITEMUKAN'.")
                    
        except Exception as err:
            st.error(f"Gagal memproses cetak: {err}")
