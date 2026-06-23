from datetime import datetime
import pytz
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


ID_SHEETS_BARU = "1CiU5sn37F_GQ0Ma6oC2yyQ6Pa1ce8cMN4MG26zjO4L4"
URL_EKSPOR_LANGSUNG = f"https://docs.google.com/spreadsheets/d/{ID_SHEETS_BARU}/export?format=csv"

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
        
        
        kolom_wajib = ['ID', 'Tujuan Pengiriman', 'Nama PIC']
        for col in kolom_wajib:
            if col not in df_db.columns:
                df_db[col] = ""
                st.warning(f"⚠️ Kolom '{col}' tidak ditemukan! Nama kolom yang ada saat ini: {list(df_db.columns[:4])}")
                
        return df_db
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(columns=['ID', 'Tujuan Pengiriman', 'Nama PIC'])


df_database = muat_database()


st.subheader("📝 Formulir Input ID")
st.caption("Tips: Masukkan ID, tekan Tab untuk pindah ke Jumlah Box. Validasi dilakukan dengan menekan tombol di bawah.")


with st.form(key="form_vertikal_shipment", enter_to_submit=False):
    
    id_inputan = st.text_input("Masukkan ID", value="").strip().replace('.0', '')
    
    
    jumlah_box = st.number_input("Jumlah Box", min_value=1, value=1, step=1)
    
    
    proses_button = st.form_submit_button(label="🔍 Cek & Validasi ID", type="primary", use_container_width=True)


if proses_button:
    if id_inputan == "":
        st.error("Silakan isi Nomor ID terlebih dahulu!")
    elif jumlah_box is None:
        st.error("Silakan isi Jumlah Box terlebih dahulu!")
    else:
        with st.spinner("Mencari data ke database..."):
            
            df_database['ID_STR'] = df_database['ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
            pencarian = df_database[df_database['ID_STR'] == id_inputan]
            
            if not pencarian.empty:
                tujuan_terdeteksi = str(pencarian.iloc[0]['Tujuan Pengiriman']).strip()
                pic_terdeteksi = str(pencarian.iloc[0]['Nama PIC']).strip()
                
                
                st.success("✅ Data Berhasil Ditemukan! Pastikan Data Sudah Sesuai.")
                
                st.info(f"**📍Tujuan Pengiriman:** {tujuan_terdeteksi}")
                st.info(f"**👽Nama PIC:** {pic_terdeteksi}")
                tz_wib = pytz.timezone('Asia/Jakarta')
                waktu_sekarang = datetime.now(tz_wib).strftime('%d/%m/%Y %I:%M %p')
                
                try:
                    html_konten = """
                    <html>
                    <head>
                    <style>
                        @page {
                            size: 50mm 50mm;
                            margin: 0;
                        }
                        body { 
                            font-family: 'Calibri', Arial, sans-serif; 
                            /* DIBUAT LEBIH BESAR: Font dasar naik ke 11pt */
                            font-size: 11pt;
                            margin: 0; 
                            padding: 0;
                            background: white; 
                            color: black; 
                            width: 50mm;
                            height: 50mm;
                            box-sizing: border-box;
                        }
                        .area-tombol { margin: 5px; text-align: center; }
                        .tombol-print { 
                            background-color: #FF4B4B; 
                            color: white; 
                            border: none; 
                            padding: 8px; 
                            font-size: 13px; 
                            font-weight: bold; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            width: 90%;
                        }
                        .tombol-print:hover { background-color: #D32F2F; }
                        
                        /* LAYOUT COMPACT: Padding dirapatkan ke 2mm agar area cetak maksimal */
                        .kotak-label { 
                            width: 50mm;
                            height: 50mm;
                            padding: 3.5mm 1.5mm 1.5mm 1.5mm;
                            display: flex;
                            flex-direction: column;
                            justify-content: flex-start;
                            align-items: center;
                            text-align: center;
                            box-sizing: border-box;
                            page-break-inside: avoid;
                            page-break-after: always;
                            overflow: hidden;
                        }
                        .info-teks { 
                            margin-top: 3px; 
                            line-height: 1.15; 
                            width: 100%;
                            word-wrap: break-word;
                        }
                        .timestamp-cetak {
                        margin-top: auto;
                        font-size: 7.5pt;
                        color: #555555;
                        width: 100%;
                        padding-bottom: 0.5mm;
                        }
                        /* DIBUAT LEBIH BESAR: Nama tujuan menonjol di ukuran 13pt */
                        .tujuan-bold {
                            font-weight: bold;
                            font-size: 13pt;
                        }
                        /* DIBUAT LEBIH BESAR: Ukuran QR Code dinaikkan dari 1.67cm menjadi 2.3cm */
                        img.barcode-qr { 
                            width: 2.3cm; 
                            height: 2.3cm; 
                            object-fit: contain; 
                        }
                        
                        @media print { 
                            .no-print { display: none !important; } 
                        }
                    </style>
                    </head>
                    <body>
                    
                    <div class="area-tombol no-print">
                        <button class="tombol-print" onclick="window.print()">🖨️ Print</button>
                    </div>
                    """
                    
                    
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
                            <img class="barcode-qr" src="data:image/png;base64,{img_base64}" />
                            <div class="info-teks">
                                <span class="tujuan-bold">{tujuan_terdeteksi}</span><br/>
                                {id_inputan}<br/>
                                {b}/{jumlah_box}
                            </div>
                            <div class="timestamp-cetak">{waktu_sekarang}</div>
                        </div>
                        """
                    
                    html_konten += """
                    </div>
                    </body>
                    </html>
                    """
            
                    components.html(html_konten, height=450, scrolling=True)
                    
                except Exception as err:
                    st.error(f"Gagal memproses pratinjau cetak: {err}") 
            else:
                
                st.error(f"❌ ID '{id_inputan}' TIDAK DITEMUKAN pada Database Google Sheets!")
