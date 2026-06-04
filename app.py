import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import requests         
from io import StringIO   

st.set_page_config(page_title="Shipment Cabang", layout="centered")
st.title("📦 QR Barcode ID Shipment Cabang")

# PERBAIKAN: Menggunakan ID Dokumen Asli berdasarkan Log Anda
ID_SHEETS_BARU = "1CiU5sn37F_GQ0Ma6oC2yyQ6Pa1ce8cMN4MG26zjO4L4"
URL_EKSPOR_LANGSUNG = f"https://docs.google.com/spreadsheets/d/{ID_SHEETS_BARU}/export?format=csv"

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
        
        # Cek ketersediaan kolom wajib
        kolom_wajib = ['ID', 'Tujuan Pengiriman', 'Nama PIC']
        for col in kolom_wajib:
            if col not in df_db.columns:
                df_db[col] = ""
                st.warning(f"⚠️ Kolom '{col}' tidak ditemukan! Nama kolom yang ada saat ini: {list(df_db.columns[:4])}")
                
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])

# Jalankan fungsi muat data
df_database = muat_database()

st.subheader("📝 Tabel Input ID")
st.caption("Tips: Isi kolom 'Masukkan ID' dan tekan Enter, maka kolom Tujuan dan Nama PIC akan otomatis terisi.")

if 'tabel_data' not in st.session_state:
    st.session_state.tabel_data = pd.DataFrame([
        {"Masukkan ID": "", "Jumlah Box": 1, "Tujuan Pengiriman": "", "Operator PIC": ""}
    ])

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

diubah = False
df_proses = df_edit.copy()

for idx, row in df_proses.iterrows():
    # PERBAIKAN: Menghapus parameter 'regex=False' karena ini fungsi string biasa
    id_inputan = str(row["Masukkan ID"]).strip().replace('.0', '')
    
    if id_inputan != "" and id_inputan != "None" and not pd.isna(row["Masukkan ID"]):
        # Pastikan data ID di database dibersihkan dengan cara yang sama
        df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
        pencarian = df_database[df_database['ID_STR'] == id_inputan]
        
        if not pencarian.empty:
            # PERBAIKAN FATAL: Menggunakan .iloc[0] untuk mengambil baris pertama hasil pencarian
            tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman']).strip()
            pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC']).strip()
        else:
            tujuan_terdeteksi = "ID TIDAK DITEMUKAN"
            pic_terdeteksi = "TIDAK DIKETAHUI"
            
        if str(row["Tujuan Pengiriman"]).strip() != tujuan_terdeteksi or str(row["Operator PIC"]).strip() != pic_terdeteksi:
            df_proses.at[idx, "Tujuan Pengiriman"] = tujuan_terdeteksi
            df_proses.at[idx, "Operator PIC"] = pic_terdeteksi
            diubah = True

if diubah:
    st.session_state.tabel_data = df_proses
    st.rerun()

if st.button("🖨️ Cetak QR Code Langsung", type="primary"):
    if df_proses.empty or df_proses['Masukkan ID'].isna().all() or df_proses['Masukkan ID'].eq('').all():
        st.error("Silakan isi data ID pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Menyiapkan lembar cetak QR Code..."):
                html_konten = """
                <html>
                <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 10px; background: white; color: black; }
                    .grid-kontainer { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
                    .kotak-label { border: 1px solid #CCCCCC; padding: 10px; text-align: center; border-radius: 4px; page-break-inside: avoid; }
                    .info-teks { font-size: 11px; text-align: left; margin-top: 5px; line-height: 14px; }
                    img { width: 100px; height: 100px; }
                    @media print { .no-print { display: none !important; } }
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
                <script>window.onload = function() { window.print(); }</script>
                </body>
                </html>
                """
                
                if ada_data_valid:
                    components.html(html_konten, height=600, scrolling=True)
                else:
                    st.warning("Tidak ada ID valid yang bisa dicetak.")
        except Exception as err:
            st.error(f"Gagal memproses cetak: {err}")
