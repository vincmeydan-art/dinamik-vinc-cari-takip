import streamlit as st
import sqlite3
import os
from datetime import datetime

# Veritabanı Bağlantısı ve Akıllı Tablo Güncelleme
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
    
    # İşler tablosu yoksa oluştur
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
            kdv_durumu TEXT,
            toplam_tutar REAL,
            odenen REAL,
            kalan REAL,
            foto_yolu TEXT,
            FOREIGN KEY(musteri_id) REFERENCES musteriler(id) ON DELETE CASCADE
        )
    """)
    
    # Eskiden kalan tablolarda kdv_durumu sütunu yoksa otomatik ekle (Hata almamak için)
    try:
        cursor.execute("ALTER TABLE isler ADD COLUMN kdv_durumu TEXT")
    except sqlite3.OperationalError:
        pass # Zaten varsa hata verme, devam et
        
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# Sayfa Konfigürasyonu ve Sektörel Tasarım
st.set_page_config(page_title="Vinç & Operasyon Yönetim Sistemi", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    .main-header {
        font-size: 22px;
        font-weight: bold;
        color: #ff9800;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🏗️ VİNÇ KİRALAMA & SAHA OPERASYON YÖNETİMİ</p>', unsafe_allow_html=True)

# Menü / Sekmeler
menu = ["Alacak / Borç (Cari Özet)", "Yeni İş Girişi", "İş Geçmişi & Tahsilat", "Müşteri Yönetimi"]
secim = st.sidebar.selectbox("📋 MENÜ", menu)

# --- 1. CARİ ÖZET / ALACAK VERECEK ---
if secim == "Alacak / Borç (Cari Özet)":
    st.header("📊 Genel Alacak ve Cari Durum")
    
    query = """
        SELECT musteriler.id, musteriler.unvan, musteriler.telefon, 
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
        toplam_alacak = sum([r[5] for r in rows])
        st.metric(label="💰 Toplam Kalan Alacağınız", value=f"{toplam_alacak:,.2f} TL")
        st.divider()
        
        for r in rows:
            m_id, unvan, telefon, toplam, odenen, kalan = r
            with st.expander(f"🏢 {unvan} — Kalan Alacak: **{kalan:,.2f} TL**"):
                st.write(f"**Telefon:** {telefon if telefon else 'Belirtilmemiş'}")
                st.write(f"**Toplam İş Hacmi:** {toplam:,.2f} TL | **Yapılan Toplam Ödeme:** {odenen:,.2f} TL")
                
                whatsapp_text = f"Sayın {unvan}, {datetime.now().strftime('%d.%m.%Y')} tarihi itibarıyla güncel kalan borç/bakiye tutarınız: {kalan:,.2f} TL'dir. İyi çalışmalar dileriz."
                st.code(whatsapp_text, language="text")
                st.caption("Yukarıdaki metni kopyalayarak müşteriye WhatsApp üzerinden borç hatırlatması gönderebilirsiniz.")
    else:
        st.info("Henüz kayıtlı müşteri veya iş bulunmuyor.")

# --- 2. YENİ İŞ / OPERASYON GİRİŞİ ---
elif secim == "Yeni İş Girişi":
    st.header("📝 Yeni İş / Operasyon Kaydı")
    
    cursor.execute("SELECT id, unvan FROM musteriler")
    musteriler = cursor.fetchall()
    
    if not musteriler:
        st.warning("⚠️ Önce sol menüden 'Müşteri Yönetimi' kısmına giderek bir müşteri eklemelisiniz!")
    else:
        musteri_dict = {m[1]: m[0] for m in musteriler}
        secilen_musteri_adi = st.selectbox("Müşteri Seç", list(musteri_dict.keys()))
        musteri_id = musteri_dict[secilen_musteri_adi]
        
        col1, col2 = st.columns(2)
        with col1:
            tarih = st.date_input("İş Tarihi", datetime.now()).strftime("%d.%m.%Y")
            santiye = st.text_input("Şantiye Adı / Konum")
            vinc = st.text_input("Vinç / Plaka (Örn: 34 VNC 01)")
            operator = st.text_input("Operatör Adı")
        with col2:
            sure = st.number_input("Süre (Saat veya Gün)", min_value=0.1, value=1.0, step=0.5)
            birim_fiyat = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=0.0, step=100.0)
            kdv_tipi = st.selectbox("Vergi / KDV Hesaplama", ["KDV Hariç (Düz Tutar)", "KDV Dahil (%20)", "İnşaat Tevkifatlı (5/10)"])
            odenen = st.number_input("Peşin Alınan Ödeme (TL)", min_value=0.0, value=0.0, step=100.0)
            
        aciklama = st.text_area("İşin Detay Açıklaması (Yapılan işin türü, detaylar vb.)")
        
        uploaded_file = st.file_uploader("📸 Saha Tutanağı / Kantar / Çalışma Fişi Fotoğrafı", type=["png", "jpg", "jpeg"])
        foto_yolu = ""
        if uploaded_file is not None:
            os.makedirs("uploads", exist_ok=True)
            foto_yolu = os.path.join("uploads", uploaded_file.name)
            with open(foto_yolu, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Fotoğraf başarıyla yüklendi!")

        if st.button("🚀 İşi Kaydet", type="primary"):
            temel_tutar = sure * birim_fiyat
            
            if kdv_tipi == "KDV Dahil (%20)":
                toplam_tutar = temel_tutar * 1.20
            elif kdv_tipi == "İnşaat Tevkifatlı (5/10)":
                kdv = temel_tutar * 0.20
                tevkifat_edilen_kdv = kdv / 2
                toplam_tutar = temel_tutar + tevkifat_edilen_kdv
            else:
                toplam_tutar = temel_tutar
                
            kalan = toplam_tutar - odenen
            
            cursor.execute("""
                INSERT INTO isler (musteri_id, tarih, santiye, vinc_plaka, operator, aciklama, sure, birim_fiyat, kdv_durumu, toplam_tutar, odenen, kalan, foto_yolu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (musteri_id, tarih, santiye, vinc, operator, aciklama, sure, birim_fiyat, kdv_tipi, toplam_tutar, odenen, kalan, foto_yolu))
            conn.commit()
            st.success(f"İş başarıyla kaydedildi! Toplam Tutar: {toplam_tutar:,.2f} TL | Kalan Bakiye: {kalan:,.2f} TL")

# --- 3. İŞ GEÇMİŞİ & TAHSİLAT ---
elif secim == "İş Geçmişi & Tahsilat":
    st.header("📂 Geçmiş İşler ve Tahsilat Yönetimi")
    
    query = """
        SELECT isler.id, musteriler.unvan, isler.tarih, isler.santiye, isler.vinc_plaka, 
               isler.operator, isler.aciklama, isler.sure, isler.toplam_tutar, 
               isler.odenen, isler.kalan, isler.foto_yolu
        FROM isler 
        JOIN musteriler ON isler.musteri_id = musteriler.id
        ORDER BY isler.id DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if rows:
        for r in rows:
            is_id, musteri, tarih, santiye, vinc, operator, aciklama, sure, toplam, odenen, kalan, foto = r
            with st.expander(f"Tarih: {tarih} | Müşteri: **{musteri}** | Şantiye: {santiye} | Kalan: **{kalan:,.2f} TL**"):
                st.write(f"**Vinç / Plaka:** {vinc} | **Operatör:** {operator}")
                st.write(f"**Açıklama:** {aciklama}")
                st.write(f"**Toplam Tutar:** {toplam:,.2f} TL | **Ödenen:** {odenen:,.2f} TL | **Kalan:** **{kalan:,.2f} TL**")
                
                if foto and os.path.exists(foto):
                    st.image(foto, caption="Saha Belgesi", width=250)
                
                col_tahsilat, col_sil = st.columns(2)
                
                with col_tahsilat:
                    tahsilat_miktari = st.number_input(f"Tahsilat Ekle (TL) [ID: {is_id}]", min_value=0.0, value=0.0, step=500.0, key=f"t_miktar_{is_id}")
                    if st.button(f"💵 Ödeme Al / Düş", key=f"t_btn_{is_id}"):
                        if tahsilat_miktari > 0:
                            yeni_odenen = odenen + tahsilat_miktari
                            yeni_kalan = toplam - yeni_odenen
                            cursor.execute("UPDATE isler SET odenen = ?, kalan = ? WHERE id = ?", (yeni_odenen, yeni_kalan, is_id))
                            conn.commit()
                            st.success(f"{tahsilat_miktari:,.2f} TL tahsilat işlendi! Güncel Kalan: {yeni_kalan:,.2f} TL")
                            st.rerun()
                
                with col_sil:
                    st.write("") 
                    st.write("")
                    if st.button(f"🗑️ İşi Komple Sil", key=f"is_sil_{is_id}"):
                        cursor.execute("DELETE FROM isler WHERE id = ?", (is_id,))
                        conn.commit()
                        st.warning("İş silindi!")
                        st.rerun()
    else:
        st.info("Kayıtlı iş bulunvuyor.")

# --- 4. MÜŞTERİ YÖNETİMİ ---
elif secim == "Müşteri Yönetimi":
    st.header("👥 Müşteri / Firma Yönetimi")
    
    with st.form("musteri_form"):
        unvan = st.text_input("Firma / Müşteri Unvanı")
        telefon = st.text_input("Telefon Numarası")
        adres = st.text_area("Adres")
        submitted = st.form_submit_button("➕ Müşteri Kaydet")
        
        if submitted:
            if unvan.strip():
                cursor.execute("INSERT INTO musteriler (unvan, telefon, adres) VALUES (?, ?, ?)", (unvan, telefon, adres))
                conn.commit()
                st.success(f"'{unvan}' başarıyla eklendi!")
                st.rerun()
            else:
                st.error("Firma unvanı boş olamaz!")
                
    st.divider()
    st.subheader("📋 Kayıtlı Müşteriler Listesi")
    
    cursor.execute("SELECT id, unvan, telefon, adres FROM musteriler")
    m_rows = cursor.fetchall()
    
    if m_rows:
        for m in m_rows:
            m_id, m_unvan, m_tel, m_adres = m
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"**🏢 {m_unvan}** | Tel: {m_tel} \n\n *Adres:* {m_adres}")
            with col_btn:
                if st.button("🗑️ Müşteriyi Sil", key=f"m_sil_{m_id}"):
                    cursor.execute("DELETE FROM isler WHERE musteri_id = ?", (m_id,))
                    cursor.execute("DELETE FROM musteriler WHERE id = ?", (m_id,))
                    conn.commit()
                    st.error(f"'{m_unvan}' ve tüm geçmişi silindi!")
                    st.rerun()
            st.divider()
    else:
        st.info("Henüz müşteri eklenmemiş.")