import streamlit as st
import pandas as pd
import qrcode
import io
import base64
import streamlit.components.v1 as components
import requests         
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Barcode Cabang", layout="centered")
st.title("📦 QR Barcode ID Cabang 2026")


ID_SHEETS_BARU = "1CiU5sn37F_GQ0Ma6oC2yyQ6Pa1ce8cMN4MG26zjO4L4"
URL_EKSPOR_LANGSUNG = f"https://docs.google.com/spreadsheets/d/{ID_SHEETS_BARU}/export?format=csv"

if "data_tervalidasi" not in st.session_state:
    st.session_state.data_tervalidasi = None
    
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
                waktu_sekarang = datetime.now().strftime("%dd-%mm-%yyyy %hh:%mm:%ss")

                st.session_state.data_tervalidasi = {
                    "id_inputan": id_inputan,
                    "jumlah_box": int(jumlah_box),
                    "tujuan": str(pencarian.iloc['Tujuan Pengiriman']).strip(),
                    "pic": str(pencarian.iloc['Nama PIC']).strip(),
                    "waktu_cetak": waktu_sekarang
                }
            else:
                st.error(f"❌ ID '{id_inputan}' tidak ditemukan di database!")
                st.session_state.data_tervalidasi = None
                
                
if st.session_state.data_tervalidasi:
                data = st.session_state.data_tervalidasi
    
                st.success("✅ Data Berhasil Ditemukan! Pastikan Data Sudah Sesuai.")
                st.info(f"**📍 Tujuan Pengiriman:** {data['tujuan']}")
                st.info(f"**🤴 Nama PIC:** {data['pic']}")
                
               
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
                            background: #f4f4f6; 
                            color: black; 
                            box-sizing: border-box;
                        }
                        .area-tombol {
                            margin: 15px 0;
                            display: flex;
                            justify-content: center;
                            width: 100%;
                        }
                        .tombol-print { 
                            background-color: #FF4B4B; 
                            color: white; 
                            border: none; 
                            padding: 10px 20px; 
                            font-size: 14px; 
                            font-weight: bold; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            mid-width: 150%;
                            box-shadow: 0px 2px 5px rgba(0,0,0,0.15);
                        }
                        .tombol-print:hover { background-color: #D32F2F; }

                        .wrapper-grid {
                            display:  grid;
                            grid-template-columns: repeat(auto-fill, 50mm);
                            gap: 20px;
                            padding: 10px;
                            justify-content: center;
                        }
                        
                        /* LAYOUT COMPACT: Padding dirapatkan ke 2mm agar area cetak maksimal */
                        .kotak-label { 
                            width: 50mm;
                            height: 50mm;
                            padding: 3mm 2mm 2mm 2mm;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            align-items: center;
                            text-align: center;
                            box-sizing: border-box;
                            background: white;
                            border: 1px solid #ccc;
                            border-radius: 5px;
                            box-shadow: 0px 3px 6px rgba(0,0,0,0.08);
                        }
                        .info-teks { 
                            line-height: 1.2; 
                            width: 100%;
                            word-wrap: break-word;
                        }
                        .tujuan-bold {
                            font-weight: bold;
                            font-size: 13pt;
                        }
                        img.barcode-qr { 
                            width: 2.3cm; 
                            height: 2.3cm; 
                            object-fit: contain; 
                        }
                        
                    .waktu-cetak {
                        font-size: 7.5pt;
                        font-style: italic;
                        color: #444444;
                        width: 100%;
                        margin-top: auto;
                        }
                        
                        @media print { 
                            .no-print { display: none !important; } 
                            body { background: white; }
                            .wrapper-grid {
                            display: block !important;
                            padding: 0 !important;
                            gap: 0 !important;
                        }
                        .kotak-label {
                            border: none !important;
                            box-shadow: none !important;
                            page-break-inside: avoid !important;
                            page-break-after: always !important;
                            height: 50mm !important;
                            width:  50mm !important;
                        }
                        .waktu-cetak {
                            color: black !important;
                        }
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
                            <!-- Baris Teks Waktu Cetak Real-time -->
                            <div class="waktu-cetak">{data['waktu_cetak']}</div>
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
