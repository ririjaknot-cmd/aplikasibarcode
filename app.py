import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="Shipment Cabang Generator QR Code", layout="centered")
st.title("📦 Sistem Input & Cetak QR Code Pengiriman")
st.write("Sistem terintegrasi database Google Sheets (Header dimulai dari Baris 2).")

# =========================================================================
# ⚠️ PASTE LINK GOOGLE SHEETS ANDA YANG SUDAH JADI 'ANYONE WITH THE LINK' DI SINI
URL_SHEET = "https://docs.google.com/spreadsheets/d/1CiU5sn37F_GQ0Ma6oC2yyQ6Pa1ce8cMN4MG26zjO4L4/edit?usp=sharing"
# =========================================================================

# Fungsi membaca database Google Sheets secara real-time
@st.cache_data(ttl=5) # Data disegarkan setiap 5 detik
def muat_database(url):
    try:
        base_url = url.split("/edit")
        csv_url = f"{base_url[0]}/export?format=csv"
        
        # header=1 berarti melewati baris pertama (indeks 0) dan menjadikan Baris 2 sebagai nama kolom resmi
        df_db = pd.read_csv(csv_url, header=1)
        
        # Bersihkan spasi berlebih di nama kolom agar pencarian akurat
        df_db.columns = df_db.columns.str.strip()
        
        return df_db
    except Exception as e:
        st.error(f"Gagal menghubungkan ke Database Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Memuat data dari cloud
df_database = muat_database(URL_SHEET)

# Input Nama Operator yang sedang memegang komputer
nama_operator = st.text_input("👤 Nama Operator yang Bertugas saat ini:", placeholder="Ketik nama Anda di sini...")

if nama_operator:
    st.success(f"Sesi Aktif: **{nama_operator}** siap memproses dan mencetak.")

st.subheader("📝 Tabel Input Data")

# Struktur kolom input tabel web
data_awal = [
    {"ID Unik": "", "Jumlah Box": 1, "Tujuan Pengiriman": "(Otomatis)"},
]

df_input = st.data_editor(
    data_awal, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "ID Unik": st.column_config.TextColumn("ID Unik", required=True),
        "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", min_value=1, default=1, required=True),
        "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", disabled=True)
    }
)

# TOMBOL PROSES & LANGSUNG CETAK PRINTER
if st.button("🖨️ Ambil Data & Cetak QR Code Langsung", type="primary"):
    df = pd.DataFrame(df_input)
    
    if not nama_operator.strip():
        st.error("Wajib mengisi Nama Operator terlebih dahulu sebelum mencetak!")
    elif df.empty or df['ID Unik'].isna().all() or df['ID Unik'].eq('').all():
        st.error("Silakan isi data ID Unik pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Mencocokkan data dengan database cloud..."):
                
                # Desain layout kertas cetak (HTML + CSS) bersih tanpa tulisan Nama PIC
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
                    if pd.isna(row['ID Unik']) or str(row['ID Unik']).strip() == "":
                        continue
                        
                    id_input = str(row['ID Unik']).strip()
                    jumlah_box = int(row['Jumlah Box']) if not pd.isna(row['Jumlah Box']) else 1
                    
                    # LOGIKA PENCARIAN: Mencocokkan input dengan Kolom "ID" di Google Sheets Anda
                    pencarian = df_database[df_database['ID'].astype(str).str.strip() == id_input]
                    
                    if not pencarian.empty:
                        # Mengambil data dari Kolom D (Tujuan Pengiriman) dan Kolom I (Nama PIC)
                        tujuan = str(pencarian.iloc[0]['Tujuan Pengiriman'])
                        nama_pic = str(pencarian.iloc[0]['Nama PIC'])
                    else:
                        tujuan = "ID TIDAK DITEMUKAN"
                        nama_pic = "TIDAK DIKETAHUI"
                    
                    ada_data_valid = True
                    
                    # Simpan informasi untuk ditampilkan sebagai laporan verifikasi di halaman web
                    ringkasan_proses.append({
                        "ID Unik": id_input,
                        "Jumlah Box": jumlah_box,
                        "Tujuan Pengiriman": tujuan,
                        "Nama PIC (Google Sheets)": nama_pic
                    })
                    
                    # Logika pembuatan lembar lembaran cetak QR Code jika ID ditemukan
                    if目的 != "ID TIDAK DITEMUKAN":
                        for b in range(1, jumlah_box + 1):
                            qr = qrcode.QRCode(version=1, box_size=10, border=1)
                            qr.add_data(id_input)
                            qr.make(fit=True)
                            img_qr = qr.make_image(fill_color="black", back_color="white")
                            
                            fp = io.BytesIO()
                            img_qr.save(fp, format="PNG")
                            fp.seek(0)
                            
                            img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                            
                            # --- ISI LABEL CETAK ---
                            # Nama PIC sengaja dikosongkan dari label cetak sesuai permintaan Anda
                            html_konten += f"""
                            <div class="kotak-label">
                                <img src="data:image/png;base64,{img_base64}" />
                                <div class="info-teks">
                                    <b>ID:</b> {id_input}<br/>
                                    <b>Box:</b> {b}/{jumlah_box}<br/>
                                    <b>Tujuan:</b> {tujuan}
                                </div>
                            </div>
                            """
                
                html_konten += """
                </div>
                <script>
                    window.onload = function() {
                        window.print(); /* Otomatis memicu jendela cetak printer */
                    }
                </script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    # MENAMPILKAN RINGKASAN DI WEB (Termasuk Nama PIC untuk verifikasi user)
                    st.write("---")
                    st.subheader("📊 Hasil Verifikasi Pengiriman:")
                    st.dataframe(pd.DataFrame(ringkasan_proses), use_container_width=True)
                    
                    # Lempar dokumen ke printer
                    components.html(html_konten, height=0, width=0)
                    st.balloons()
                else:
                    st.warning("Tidak ada data valid untuk diproses.")
                    
        except Exception as e:
            st.error(f"Terjadi kesalahan pembacaan database: {e}. Pastikan header Anda di baris ke-2 tertulis persis 'ID', 'Tujuan Pengiriman', dan 'Nama PIC'.")
