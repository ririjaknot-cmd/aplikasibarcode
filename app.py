import streamlit as st
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

st.set_page_config(page_title="Generator Barcode Massal", layout="centered")
st.title("📦 Sistem Input & Cetak Barcode Massal")
st.write("Ketik data pengiriman langsung di bawah ini tanpa perlu upload file CSV.")

# Membuat form input data menggunakan fitur tabel interaktif Streamlit
st.subheader("📝 Masukkan Data Pengiriman")
st.caption("Tips: Klik tombol '+' di bawah tabel untuk menambah baris baru. Klik dua kali pada sel untuk mengetik.")

# Data awal sebagai contoh di tabel
data_awal = [
    {"id_unik": "BRG001", "jumlah_box": 1, "tujuan_pengiriman": "Jakarta"},
]

# Menampilkan tabel input yang bisa diedit langsung oleh user
df_input = st.data_editor(
    data_awal, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "id_unik": st.column_config.TextColumn("ID Unik (Barcode)", required=True),
        "jumlah_box": st.column_config.NumberColumn("Jumlah Box", min_value=1, default=1, required=True),
        "tujuan_pengiriman": st.column_config.TextColumn("Tujuan Pengiriman", required=True)
    }
)

# Tombol untuk memproses data dari tabel di atas
if st.button("🚀 Mulai Generate Barcode (PDF)", type="primary"):
    df = pd.DataFrame(df_input)
    
    # Validasi apakah ada data yang kosong
    if df.empty or df['id_unik'].isna().all() or df['id_unik'].eq('').all():
        st.error("Silakan isi data pada tabel terlebih dahulu!")
    else:
        try:
            with st.spinner("Sedang memproses, mohon tunggu..."):
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                story = []
                
                styles = getSampleStyleSheet()
                style_teks = styles['Normal']
                style_teks.fontSize = 10
                style_teks.leading = 12
                
                data_tabel = []
                baris_sekarang = []
                EAN = barcode.get_barcode_class('code128')
                
                for index, row in df.iterrows():
                    # Lewati jika baris kosong atau ID kosong
                    if pd.isna(row['id_unik']) or str(row['id_unik']).strip() == "":
                        continue
                        
                    id_unik = str(row['id_unik'])
                    jumlah_box = int(row['jumlah_box']) if not pd.isna(row['jumlah_box']) else 1
                    tujuan = str(row['tujuan_pengiriman']) if not pd.isna(row['tujuan_pengiriman']) else "-"
                    
                    # Perulangan berdasarkan jumlah box
                    for b in range(1, jumlah_box + 1):
                        fp = io.BytesIO()
                        my_barcode = EAN(id_unik, writer=ImageWriter())
                        my_barcode.write(fp, options={"write_text": False, "module_height": 5.0, "module_width": 0.2})
                        fp.seek(0)
                        
                        img_barcode = Image(fp, width=120, height=45)
                        info_text = f"<b>ID:</b> {id_unik}<br/><b>Box:</b> {b}/{jumlah_box}<br/><b>Tujuan:</b> {tujuan}"
                        p = Paragraph(info_text, style_teks)
                        
                        kotak_label = Table([[img_barcode], [Spacer(1, 2)], [p]], colWidths=[150])
                        kotak_label.setStyle(TableStyle([
                            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                            ('BOX', (0,0), (-1,-1), 1, '#CCCCCC'),
                            ('TOPPADDING', (0,0), (-1,-1), 6),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                        ]))
                        
                        baris_sekarang.append(kotak_label)
                        if len(baris_sekarang) == 3:
                            data_tabel.append(baris_sekarang)
                            baris_sekarang = []
                
                if baris_sekarang:
                    while len(baris_sekarang) < 3:
                        baris_sekarang.append("")
                    data_tabel.append(baris_sekarang)
                
                if data_tabel:
                    tabel_utama = Table(data_tabel, colWidths=[160, 160, 160])
                    tabel_utama.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                    ]))
                    story.append(tabel_utama)
                    doc.build(story)
                    pdf_buffer.seek(0)
                    
                    st.balloons()
                    st.download_button(
                        label="📥 Unduh PDF Barcode Siap Cetak",
                        data=pdf_buffer,
                        file_name="labels_barcode_langsung.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("Tidak ada data barcode valid yang bisa diproses.")
        except Exception as e:
            st.error(f"Terjadi error: {e}")
