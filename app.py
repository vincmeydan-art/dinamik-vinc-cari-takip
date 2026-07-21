import streamlit as st
import sqlite3
import os
from datetime import datetime

# Veritabanı Bağlantısı ve Kurulumu
def init_db():
    conn = sqlite3.connect("vinc_takip.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unvan TEXT NOT NULL,
            telefon TEXT,
            adres TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS isler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_id INTEGER,
            tarih TEXT,
            santiye TEXT,
            vinc_plaka TEXT,
            operator TEXT,
            aciklama TEXT,
            sure REAL,
            birim_fiyat REAL,
            toplam_tutar REAL,
            odenen REAL,
            kalan REAL,
            foto_yolu TEXT,
            FOREIGN KEY(musteri_id) REFERENCES musteriler(id)
        )
    """)
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# Sayfa Konfigürasyonu
st.set_page_config(page_title="Vinç Kiralama & Cari Takip", page_icon="🏗️", layout="wide")

st.title("🏗️ Vinç Kiralama ve Cari Takip Sistemi")
st.markdown("Sahadan veya ofisten tüm operasyonlarınızı ve alacak/borç durumunuzu kolayca yönetin.")

# Menü / Sekmeler
menu = ["Alacak / Borç (Cari Özet)", "Yeni İş Girişi", "İş Geçmişi & Detaylar", "Müşteri Yönetimi"]
secim = st.sidebar.selectbox("Menü", menu)

# --- 1. CARİ ÖZET / ALACAK VERECEK ---
if secim == "Alacak / Borç (Cari Özet)":
    st.header("📊 Genel Alacak ve Cari Durum")
    
    query = """
        SELECT musteriler.unvan, musteriler.telefon, 
               COALESCE(SUM(isler.toplam_tutar), 0), 
               COALESCE(SUM(isler.odenen), 0), 
               COALESCE(SUM(isler.kalan), 0)
        FROM musteriler
        LEFT JOIN isler ON musteriler.id = isler.musteri_id
        GROUP BY musteriler.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if rows:
        toplam_alacak = sum([r[4] for r in rows])
        st.metric(label="Toplam Kalan Alacağınız", value=f"{toplam_alacak:,.2f} TL")
        st.divider()
        
        for r in rows:
            unvan, telefon, toplam, odenen, kalan = r
            with st.expander(f"🏢 {unvan} — Kalan Alacak: **{kalan:,.2f} TL**"):
                st.write(f"**Telefon:** {telefon if telefon else 'Belirtilmemiş'}")
                st.write(f"**Toplam İş Hacmi:** {toplam:,.2f} TL | **Ödenen:** {odenen:,.2f} TL")
    else:
        st.info("Henüz kayıtlı müşteri veya iş bulunmuyor.")

# --- 2. YENİ İŞ / OPERASYON GİRİŞİ ---
elif secim == "Yeni İş Girişi":
    st.header("📝 Yeni İş / Operasyon Kaydı")
    
    cursor.execute("SELECT id, unvan FROM musteriler")
    musteriler = cursor.fetchall()
    
    if notmusteriler:
        st.warning("Önce 'Müşteri Yönetimi' sekmesinden bir müşteri eklemelisiniz!")
    else:
        musteri_dict = {m[1]: m[0] for m in musteriler}
        secilen_musteri_adi = st.selectbox("Müşteri Seç", list(musteri_dict.keys()))
        musteri_id = musteri_dict[secilen_musteri_adi]
        
        col1, col2 = st.columns(2)
        with col1:
            tarih = st.date_input("İş Tarihi", datetime.now()).strftime("%d.%m.%Y")
            santiye = st.text_input("Şantiye Adı / Konum")
            vinc = st.text_input("Vinç / Plaka")
        with col2:
            operator = st.text_input("Operatör Adı")
            sure = st.number_input("Süre (Saat veya Gün)", min_value=0.1, value=1.0)
            birim_fiyat = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=0.0)
            odenen = st.number_input("Alınan Peşinat / Ödenen (TL)", min_value=0.0, value=0.0)
            
        aciklama = st.text_area("İşin Detay Açıklaması")
        
        # Fotoğraf / Belge Yükleme (Telefondan direkt kamera ile çekilebilir veya dosya seçilebilir)
        uploaded_file = st.file_uploader("Saha Tutanağı / Fotoğraf Ekle", type=["png", "jpg", "jpeg"])
        foto_yolu = ""
        if uploaded_file is not None:
            os.makedirs("uploads", exist_ok=True)
            foto_yolu = os.path.join("uploads", uploaded_file.name)
            with open(foto_yolu, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Fotoğraf başarıyla eklendi!")

        if st.button("İşi Kaydet", type="primary"):
            toplam_tutar = sure * birim_fiyat
            kalan = toplam_tutar - odenen
            
            cursor.execute("""
                INSERT INTO isler (musteri_id, tarih, santiye, vinc_plaka, operator, aciklama, sure, birim_fiyat, toplam_tutar, odenen, kalan, foto_yolu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (musteri_id, tarih, santiye, vinc, operator, aciklama, sure, birim_fiyat, toplam_tutar, odenen, kalan, foto_yolu))
            conn.commit()
            st.success(f"İş başarıyla kaydedildi! Toplam: {toplam_tutar} TL | Kalan: {kalan} TL")

# --- 3. İŞ GEÇMİŞİ & DETAYLAR ---
elif secim == "İş Geçmişi & Detaylar":
    st.header("📂 Geçmiş İşler ve Operasyonlar")
    
    query = """
        SELECT isler.id, musteriler.unvan, isler.tarih, isler.santiye, isler.vinc_plaka, 
               isler.operator, isler.aciklama, isler.sure, isler.birim_fiyat, 
               isler.toplam_tutar, isler.odenen, isler.kalan, isler.foto_yolu
        FROM isler 
        JOIN musteriler ON isler.musteri_id = musteriler.id
        ORDER BY isler.id DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if rows:
        for r in rows:
            with st.expander(f"Tarih: {r[2]} | Müşteri: **{r[1]}** | Şantiye: {r[3]} | Kalan: **{r[11]} TL**"):
                st.write(f"**Vinç / Plaka:** {r[4]} | **Operatör:** {r[5]}")
                st.write(f"**Açıklama:** {r[6]}")
                st.write(f"**Süre:** {r[7]} | **Birim Fiyat:** {r[8]} TL | **Toplam:** {r[9]} TL | **Ödenen:** {r[10]} TL")
                if r[12] and os.path.exists(r[12]):
                    st.image(r[12], caption="Saha Tutanağı / Fotoğraf", width=300)
    else:
        st.info("Kayıtlı iş bulunmuyor.")

# --- 4. MÜŞTERİ YÖNETİMİ ---
elif secim == "Müşteri Yönetimi":
    st.header("👥 Müşteri / Firma Yönetimi")
    
    with st.form("musteri_form"):
        unvan = st.text_input("Firma / Müşteri Unvanı")
        telefon = st.text_input("Telefon Numarası")
        adres = st.text_area("Adres")
        submitted = st.form_submit_button("Müşteri Kaydet")
        
        if submitted:
            if unvan.strip():
                cursor.execute("INSERT INTO musteriler (unvan, telefon, adres) VALUES (?, ?, ?)", (unvan, telefon, adres))
                conn.commit()
                st.success(f"'{unvan}' başarıyla eklendi!")
            else:
                st.error("Firma unvanı boş olamaz!")
                
    st.divider()
    st.subheader("Kayıtlı Müşteriler Listesi")
    cursor.execute("SELECT unvan, telefon, adres FROM musteriler")
    m_rows = cursor.fetchall()
    if m_rows:
        for m in m_rows:
            st.markdown(f"- **{m[0]}** | Tel: {m[1]} | Adres: {m[2]}")
    else:
        st.info("Henüz müşteri eklenmemiş.")