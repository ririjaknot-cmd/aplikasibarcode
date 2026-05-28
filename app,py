import streamlit as st
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

st.set_page_config(page_title="Generator Barcode Massal", layout="centered")
st.title("📦 Sistem Cetak Barcode Massal")
st.write("Aplikasi ini membaca file CSV Anda dan mengubahnya menjadi lembaran barcode siap cetak.")

uploaded_file = st.file_uploader("Unggah File CSV Anda di sini", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        kolom_wajib = ['id_unik', 'jumlah_box', 'tujuan_pengiriman']
        
        if not all(col in df.columns for col in kolom_wajib):
            st.error(f"Format CSV salah! Harus memiliki judul kolom persis seperti ini: {', '.join(kolom_wajib)}")
        else:
            st.success("File CSV Berhasil Dimuat!")
            st.dataframe(df, use_container_width=True)
            
            if st.button("🚀 Mulai Generate Barcode (PDF)", type="primary"):
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
                        id_unik = str(row['id_unik'])
                        jumlah_box = int(row['jumlah_box'])
                        tujuan = str(row['tujuan_pengiriman'])
                        
                        for b in range(1, jumlah_box + 1):
                            fp = io.BytesIO()
                            my_barcode = EAN(id_unik, writer=ImageWriter())
                            my_barcode.write(fp, options={"write_text": False, "module_height": 5.0, "module_width": 0.2})
                            fp.seek(0)
                            
                            img_barcode = Image(fp, width=120, height=45)
                            info_text = f"<b>ID:</b> {id_unik}<br/><b>Box:</b> {b}/{jumlah_box}<br/><b>Tujuan:</b> {tujuan}"
                            p = Paragraph(info_text, style_teks)
                            
                            kotak_label = Table([[img_barcode], [Spacer(1, 2)], [p]], colWidths=[160])
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
                        tabel_utama = Table(data_tabel, colWidths=[180, 180, 180])
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
                            file_name="labels_barcode.pdf",
                            mime="application/pdf"
                        )
    except Exception as e:
        st.error(f"Terjadi error: {e}")
