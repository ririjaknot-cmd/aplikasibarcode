import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="Generator QR Code 50x50mm", layout="centered")
st.title("📦 Printer QR Code Mandiri (50x50mm)")
st.write("Isi data pada tabel di bawah. Hasil cetak otomatis diformat khusus untuk ukuran label kertas 50x50 mm.")

st.subheader("📝 Tabel Input Data")
st.caption("Tips: Klik tombol '+' di bawah tabel untuk menambah baris baru. Klik dua kali pada sel untuk mengetik.")

# Struktur data awal kolom tabel input web
data_awal = [
    {"Masukkan ID": "", "Jumlah Box": 1, "Tujuan Pengiriman": ""}
]

# Menampilkan tabel input interaktif
df_edit = st.data_editor(
    data_awal, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Masukkan ID": st.column_config.TextColumn("ID Unik", required=True),
        "Jumlah Box": st.column_config.NumberColumn("Jumlah Box", min_value=1, default=1, required=True),
        "Tujuan Pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", required=True)
    }
)

# TOMBOL UTAMA UNTUK PROSES CETAK
if st.button("🖨️ Cetak QR Code Langsung", type="primary"):
    df = pd.DataFrame(df_edit)
    
    if df.empty or df['Masukkan ID'].isna().all() or df['Masukkan ID'].eq('').all():
        st.error("Silakan isi data pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Menyiapkan lembar cetak khusus 50x50mm..."):
                
                # Desain layout kertas cetak (HTML + CSS) presisi untuk ukuran kertas thermal 50mm x 50mm
                html_konten = """
                <html>
                <head>
                <style>
                    /* Mengatur ukuran halaman cetak pas 50mm x 50mm */
                    @page {
                        size: 50mm 50mm;
                        margin: 0; /* Menghilangkan margin bawaan kertas browser */
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
                        page-break-after: always; /* Membuat setiap boks otomatis pindah ke kertas label baru */
                    }
                    .info-teks {
                        font-size: 9px; /* Ukuran font disesuaikan agar pas di lebar 50mm */
                        font-weight: bold;
                        text-align: center;
                        margin-top: 2mm;
                        width: 100%;
                        word-wrap: break-word; /* Memastikan teks panjang otomatis turun ke bawah jika penuh */
                        line-height: 11px;
                    }
                    img { 
                        width: 32mm; /* Ukuran QR Code optimal di dalam area kertas 50mm */
                        height: 32mm; 
                    }
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
                    tujuan = str(row['Tujuan Pengiriman']).strip() if not pd.isna(row['Tujuan Pengiriman']) else "-"
                    
                    ada_data_valid = True
                    
                    # Logika duplikasi cetak berdasarkan Jumlah Box
                    for b in range(1, jumlah_box + 1):
                        # Format gabungan teks di dalam QR Code (Misal: ID-1/2-Jakarta Pusat)
                        teks_gabungan = f"{id_inputan}-{b}/{jumlah_box}-{tujuan}"
                        
                        qr = qrcode.QRCode(version=1, box_size=10, border=1)
                        qr.add_data(teks_gabungan)
                        qr.make(fit=True)
                        img_qr = qr.make_image(fill_color="black", back_color="white")
                        
                        fp = io.BytesIO()
                        img_qr.save(fp, format="PNG")
                        fp.seek(0)
                        
                        img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                        
                        # Susun label QR Code masuk ke dalam susunan vertikal dengan teks ringkas langsung tanpa judul
                        html_konten += f"""
                        <div class="kotak-label">
                            <img src="data:image/png;base64,{img_base64}" />
                            <div class="info-teks">
                                {teks_gabungan}
                            </div>
                        </div>
                        """
                
                html_konten += """
                </div>
                <script>
                    window.onload = function() { 
                        window.print(); /* Otomatis membuka dialog printer komputer */
                    }
                </script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    # Menembakkan perintah cetak langsung ke jendela browser
                    components.html(html_konten, height=0, width=0)
                    st.balloons()
                else:
                    st.warning("Tidak ada data valid yang bisa dicetak.")
                    
        except Exception as e:
            st.error(f"⚠️ Terjadi kesalahan teknis: {e}")
