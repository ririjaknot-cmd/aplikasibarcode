import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="Generator QR Code Mandiri", layout="centered")
st.title("📦 Sistem Input & Cetak QR Code Mandiri")
st.write("Isi data ID, Jumlah Box, dan Tujuan secara mandiri langsung pada tabel di bawah ini.")

st.subheader("📝 Tabel Input Data")
st.caption("Tips: Klik tombol '+' di bawah tabel untuk menambah baris baru. Klik dua kali pada sel untuk mengetik.")

# Struktur data awal kolom tabel input web (Semua kolom bisa diisi mandiri)
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
            with st.spinner("Menyiapkan lembar cetak QR Code..."):
                
                # Desain layout kertas cetak (HTML + CSS) 1 kolom lurus menurun ke bawah
                html_konten = """
                <html>
                <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 10px; background: white; color: black; }
                    .kontainer-vertikal {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 20px; /* Jarak antar label */
                    }
                    .kotak-label {
                        border: 1px solid #CCCCCC;
                        padding: 15px;
                        text-align: center;
                        border-radius: 4px;
                        width: 250px; /* Lebar kotak label pas untuk printer thermal */
                        page-break-inside: avoid; /* Mencegah label terpotong di tengah halaman */
                    }
                    .info-teks {
                        font-size: 12px;
                        text-align: left;
                        margin-top: 8px;
                        line-height: 16px;
                    }
                    img { width: 130px; height: 130px; }
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
                        qr = qrcode.QRCode(version=1, box_size=10, border=1)
                        qr.add_data(id_inputan)
                        qr.make(fit=True)
                        img_qr = qr.make_image(fill_color="black", back_color="white")
                        
                        fp = io.BytesIO()
                        img_qr.save(fp, format="PNG")
                        fp.seek(0)
                        
                        img_base64 = base64.b64encode(fp.read()).decode('utf-8')
                        
                        # Susun label QR Code masuk ke dalam susunan menurun vertikal
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
