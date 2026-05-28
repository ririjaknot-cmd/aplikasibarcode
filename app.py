import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import re

st.set_page_config(page_title="Generator QR Code Massal", layout="centered")
st.title("📦 Sistem Input & Cetak QR Code Otomatis")
st.write("Sistem terintegrasi database Google Sheets (Sheet: Master 2026 | Header Baris 2).")

# =========================================================================
# ⚠️ MASUKKAN LINK LENGKAP GOOGLE SHEETS ANDA YANG ASLI DI SINI
URL_SHEET = "https://google.com"
# =========================================================================

# Fungsi membaca database Google Sheets khusus untuk Sheet "Master 2026"
@st.cache_data(ttl=5) # Data disegarkan otomatis setiap 5 detik
def muat_database(url_input):
    try:
        url_str = str(url_input).strip()
        
        # MENGGUNAKAN REGEX (Sistem Ekstraksi Pintar Resmi)
        # Menemukan ID Google Sheets secara otomatis di dalam teks link tanpa metode split manual
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_str)
        if match:
            sheet_id = match.group(1)
        else:
            sheet_id = url_str
            
        nama_sheet_aman = "Master%202026"
        
        # Membuat tautan ekspor CSV resmi dari Google API
        csv_url = f"https://google.com{sheet_id}/gviz/tq?tqx=out:csv&sheet={nama_sheet_aman}"
        
        # skiprows=1 untuk melompati Baris 1 agar Baris 2 otomatis naik menjadi Judul Kolom (ID, Tujuan Pengiriman, Nama PIC)
        df_db = pd.read_csv(csv_url, skiprows=1)
        
        # Bersihkan nama kolom dari spasi tidak sengaja di awal/akhir kata
        df_db.columns = df_db.columns.str.strip()
        
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal menghubungkan ke Database Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Memuat data dari cloud database
df_database = muat_database(URL_SHEET)

# Input Nama Operator/User yang sedang memakai komputer di lapangan
nama_operator = st.text_input("👤 Nama Operator yang Bertugas saat ini:", placeholder="Ketik nama Anda di sini...")

if nama_operator:
    st.success(f"Sesi Aktif: **{nama_operator}** siap memproses data.")

st.subheader("📝 Tabel Input Data")

# Struktur kolom input tabel web (Tujuan dikunci karena akan di-bypass otomatis dari database)
data_awal = [
    {"id_unik": "", "jumlah_box": 1, "tujuan_pengiriman": "(Otomatis)"},
]

df_input = st.data_editor(
    data_awal, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "id_unik": st.column_config.TextColumn("Masukkan ID", required=True),
        "jumlah_box": st.column_config.NumberColumn("Jumlah Box", min_value=1, default=1, required=True),
        "tujuan_pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True)
    }
)

# TOMBOL PROSES & LANGSUNG MELEMPARKAN KE PRINTER
if st.button("🖨️ Ambil Data & Cetak QR Code Langsung", type="primary"):
    df = pd.DataFrame(df_input)
    
    if not nama_operator.strip():
        st.error("Wajib mengisi Nama Operator terlebih dahulu sebelum mencetak!")
    elif df.empty or df['id_unik'].isna().all() or df['id_unik'].eq('').all():
        st.error("Silakan isi data ID pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Mencocokkan data dengan database cloud..."):
                
                # Desain layout kertas cetak (HTML + CSS) bersih 3 kolom tanpa menyertakan tulisan PIC
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
                ringkasan_proses = []
                
                for index, row in df.iterrows():
                    if pd.isna(row['id_unik']) or str(row['id_unik']).strip() == "":
                        continue
                        
                    id_inputan = str(row['id_unik']).strip()
                    jumlah_box = int(row['jumlah_box']) if not pd.isna(row['jumlah_box']) else 1
                    
                    # LOGIKA PENCARIAN: Mencocokkan input dengan Kolom 'ID' (A2) di Google Sheets
                    pencarian = df_database[df_database['ID'].astype(str).str.strip() == id_inputan]
                    
                    if not pencarian.empty:
                        # Mengambil data dari Kolom 'Tujuan Pengiriman' (D2) dan Kolom 'Nama PIC' (I2)
                        tujuan = str(pencarian.iloc['Tujuan Pengiriman'])
                        nama_pic = str(pencarian.iloc['Nama PIC'])
                    else:
                        tujuan = "ID TIDAK DITEMUKAN"
                        nama_pic = "TIDAK DIKETAHUI"
                    
                    ada_data_valid = True
                    
                    # Simpan informasi untuk verifikasi mata di layar web
                    ringkasan_proses.append({
                        "ID Barang": id_inputan,
                        "Jumlah Box": jumlah_box,
                        "Tujuan Tujuan": tujuan,
                        "Nama PIC (Database)": nama_pic
                    })
                    
                    # Pembuatan gambar QR Code (Hanya jika ID terdaftar resmi di Google Sheets)
                    if tujuan != "ID TIDAK DITEMUKAN":
                        for b in range(1, jumlah_box + 1):
                            qr = qrcode.QRCode(version=1, box_size=10, border=1)
                            qr.add_data(id_inputan)
                            qr.make(fit=True)
                            img_qr = qr.make_image(fill_color="black", back_color="white")
                            
                            fp = io.BytesIO()
                            img_qr.save(fp, format="PNG")
                            fp.seek(0)
                            
                            img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                            
                            # Tampilan Kertas Label Cetak (Hanya ID, Box, dan Tujuan - Nama PIC tidak dimasukkan)
                            html_konten += f"""
                            <div class="kotak-label">
                                <img src="data:image/png;base64,{img_base64}" />
                                <div class="info-teks">
                                    <b>ID:</b> {id_inputan}<br/>
                                    <b>Box:</b> {b}/{jumlah_box}<br/>
                                    <b>Tujuan:</b> {tujuan}
                                </div>
                            </div>
                            """
                
                html_konten += """
                </div>
                <script>
                    window.onload = function() {
                        window.print(); /* Otomatis memicu jendela cetak printer komputer browser */
                    }
                </script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    # Menampilkan laporan verifikasi di web (Termasuk Nama PIC hasil pencarian database)
                    st.write("---")
                    st.subheader("📊 Hasil Verifikasi Pengiriman:")
                    st.dataframe(pd.DataFrame(ringkasan_proses), use_container_width=True)
                    
                    # Melemparkan data cetak langsung ke hardware printer browser
                    components.html(html_konten, height=0, width=0)
                    st.balloons()
                else:
                    st.warning("Tidak ada data valid untuk diproses.")
                    
        except Exception as e:
            st.error(f"⚠️ Terjadi kesalahan pembacaan kolom database: {e}. Pastikan nama kolom di Google Sheets Anda tepat di A2='ID', D2='Tujuan Pengiriman', I2='Nama PIC'.")
