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
            adres TEXT,
            sifre TEXT DEFAULT '1234'
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
            kdv_durumu TEXT,
            toplam_tutar REAL,
            odenen REAL,
            kalan REAL,
            foto_yolu TEXT,
            FOREIGN KEY(musteri_id) REFERENCES musteriler(id) ON DELETE CASCADE
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE isler ADD COLUMN kdv_durumu TEXT")
    except sqlite3.OperationalError:
        pass 

    try:
        cursor.execute("ALTER TABLE musteriler ADD COLUMN sifre TEXT DEFAULT '1234'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# Sayfa Konfigürasyonu
st.set_page_config(page_title="Dinamik Vinç | Güvenli Yönetim Sistemi", page_icon="🏗️", layout="wide")

# Oturum Durumu Kontrolleri
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
if "giris_turu" not in st.session_state:
    st.session_state["giris_turu"] = None # "admin" veya "musteri"
if "aktif_musteri_id" not in st.session_state:
    st.session_state["aktif_musteri_id"] = None
if "aktif_musteri_adi" not in st.session_state:
    st.session_state["aktif_musteri_adi"] = ""

# --- GİRİŞ EKRANI (YÖNETİCİ & MÜŞTERİ SEÇİMLİ) ---
if not st.session_state["giris_yapildi"]:
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background-color: #161616; padding: 25px; border-radius: 12px; border: 1px solid #333; text-align: center;'>
                <h1 style='color: #ff9800; font-size: 26px; margin-bottom: 5px;'>🏗️ DİNAMİK VİNÇ</h1>
                <p style='color: #888; font-size: 13px;'>Operasyon ve Müşteri Portal Girişi</p>
            </div>
        """, unsafe_allow_html=True)
        
        giris_tipi = st.radio("Giriş Türü Seçin", ["👑 Yönetici Girişi", "🏢 Müşteri Cari Girişi"], horizontal=True)
        
        if giris_tipi == "👑 Yönetici Girişi":
            with st.form("admin_login"):
                kullanici_adi = st.text_input("Yönetici Kullanıcı Adı")
                sifre = st.text_input("Yönetici Şifre", type="password")
                submitted = st.form_submit_button("🔒 Yönetici Olarak Giriş Yap", use_container_width=True)
                
                if submitted:
                    if kullanici_adi == "admin" and sifre == "1234":
                        st.session_state["giris_yapildi"] = True
                        st.session_state["giris_turu"] = "admin"
                        st.success("Yönetici girişi başarılı!")
                        st.rerun()
                    else:
                        st.error("Hatalı kullanıcı adı veya şifre!")
        else:
            cursor.execute("SELECT id, unvan FROM musteriler")
            tum_musteriler = cursor.fetchall()
            
            if tum_musteriler:
                musteri_secenekleri = {m[1]: m[0] for m in tum_musteriler}
                with st.form("musteri_login"):
                    secilen_firma = st.selectbox("Firma Unvanınızı Seçin", list(musteri_secenekleri.keys()))
                    musteri_sifre = st.text_input("Müşteri Erişim Şifresi (Varsayılan: 1234)", type="password")
                    m_submitted = st.form_submit_button("🔍 Cari Bilgilerimi Görüntüle", use_container_width=True)
                    
                    if m_submitted:
                        m_id = musteri_secenekleri[secilen_firma]
                        cursor.execute("SELECT sifre FROM musteriler WHERE id = ?", (m_id,))
                        db_sifre = cursor.fetchone()[0]
                        if db_sifre is None:
                            db_sifre = "1234"
                            
                        if musteri_sifre == db_sifre:
                            st.session_state["giris_yapildi"] = True
                            st.session_state["giris_turu"] = "musteri"
                            st.session_state["aktif_musteri_id"] = m_id
                            st.session_state["aktif_musteri_adi"] = secilen_firma
                            st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                            st.rerun()
                        else:
                            st.error("Hatalı şifre!")
            else:
                st.info("Sistemde kayıtlı müşteri bulunmuyor. Lütfen yöneticinin sizi kaydetmesini bekleyin.")
    st.stop()


# ==========================================
# MÜŞTERİ PANELİ EKRANI (Eğer müşteri giriş yaptıysa)
# ==========================================
if st.session_state["giris_turu"] == "musteri":
    st.markdown(f"""
        <div style='background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ff9800; margin-bottom: 20px;'>
            <h2 style='color: #856404; margin: 0;'>Hoş Geldiniz, {st.session_state["aktif_musteri_adi"]}</h2>
            <p style='color: #666; margin: 5px 0 0 0;'>Buradan şirketinize ait tüm operasyonları, çalışma saatlerini ve güncel borç/bakiye durumunuzu inceleyebilirsiniz.</p>
        </div>
    """, unsafe_allow_html=True)
    
    m_id = st.session_state["aktif_musteri_id"]
    
    # Müşteriye ait işleri çek
    query = """
        SELECT id, tarih, santiye, vinc_plaka, operator, aciklama, sure, toplam_tutar, odenen, kalan 
        FROM isler WHERE musteri_id = ? ORDER BY id DESC
    """
    cursor.execute(query, (m_id,))
    isler = cursor.fetchall()
    
    # Toplam bakiye hesapla
    cursor.execute("SELECT COALESCE(SUM(toplam_tutar), 0), COALESCE(SUM(odenen), 0), COALESCE(SUM(kalan), 0) FROM isler WHERE musteri_id = ?", (m_id,))
    toplam_borc, toplam_odenen, kalan_bakiye = cursor.fetchone()
    
    # Üst Özet Kartları
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Toplam İş Hacmi", f"{toplam_borc:,.2f} TL")
    col2.metric("💳 Yapılan Toplam Ödeme", f"{toplam_odenen:,.2f} TL")
    col3.metric("⚠️ Güncel Kalan Borcunuz", f"{kalan_bakiye:,.2f} TL")
    
    st.divider()
    st.subheader("📋 Yapılan İşler, Saatler ve Detaylar")
    
    if isler:
        for is_item in isler:
            i_id, tarih, santiye, vinc, operator, aciklama, sure, toplam, odenen, kalan = is_item
            
            # Süre bilgisini şık biçimlendirme
            sure_str = f"{sure} Saat" if "Saatlik" in aciklama or sure < 24 else f"{int(sure)} Gün"
            
            with st.expander(f"📅 Tarih: {tarih} | Şantiye: {santiye} | Kalan Borç: **{kalan:,.2f} TL**"):
                st.write(f"**Vinç / Plaka:** {vinc if vinc else 'Belirtilmemiş'} | **Operatör:** {operator if operator else 'Belirtilmemiş'}")
                st.write(f"**Çalışma Süresi / Miktarı:** {sure_str}")
                st.write(f"**İş Açıklaması / Detay:** {aciklama}")
                st.markdown("---")
                st.write(f"**Toplam Tutar:** {toplam:,.2f} TL | **Ödenen Tutar:** {oden:,.2f} TL | **Kalan:** **{kalan:,.2f} TL**" if 'oden' in locals() else f"**Toplam Tutar:** {toplam:,.2f} TL | **Ödenen:** {odenen:,.2f} TL | **Kalan:** **{kalan:,.2f} TL**")
    else:
        st.info("Henüz adınıza kaydedilmiş bir operasyon veya iş bulunmuyor.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Güvenli Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.session_state["giris_turu"] = None
        st.session_state["aktif_musteri_id"] = None
        st.rerun()

    st.stop()


# ==========================================
# YÖNETİCİ PANELİ EKRANI (Admin giriş yaptıysa)
# ==========================================

# --- PRO SOL MENÜ STİLLERİ ---
st.markdown("""
    <style>
    .main-header {
        font-size: 26px;
        font-weight: 800;
        color: #ff9800;
        margin-bottom: 0px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .sub-header {
        font-size: 13px;
        color: #aaaaaa;
        margin-bottom: 25px;
        letter-spacing: 0.3px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        border: 1px solid #444444;
    }
    .stButton>button:hover {
        border-color: #ff9800;
        color: #ff9800;
    }
    /* SOL MENÜNÜN RENGİNİ AÇIK / FERAH YAPMA */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: #212529 !important;
    }
    .pro-badge {
        background: linear-gradient(90deg, #ff9800 0%, #ff5722 100%);
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- PRO SOL MENÜ ---
with st.sidebar:
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        st.markdown("<div style='background-color: #fff3cd; padding: 10px; border-radius: 8px; border: 1px solid #ffeeba; text-align: center;'>", unsafe_allow_html=True)
        st.image(logo_path, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #ff9800;'>🏗️ DİNAMİK VİNÇ</h2>", unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; margin-top: 10px;"><span class="pro-badge">PRO EDITION v3.5</span></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    menu_options = {
        "📊 Cari & Alacak Özeti": "Genel Finans ve Alacak Takibi",
        "📝 Yeni İş / Operasyon": "Saha ve Kiralama Girişi",
        "📂 İş Geçmişi & Tahsilat": "Arşiv, Ödeme ve Dekontlar",
        "👥 Müşteri Yönetimi": "Firma ve İletişim Rehberi"
    }
    
    secim = st.radio("📋 OPERASYONEL MENÜ", list(menu_options.keys()))

    st.sidebar.divider()
    
    if st.sidebar.button("🚪 Yönetici Oturumunu Kapat"):
        st.session_state["giris_yapildi"] = False
        st.session_state["giris_turu"] = None
        st.rerun()
        
    st.sidebar.markdown("""
        <div style='background-color: #e9ecef; padding: 10px; border-radius: 6px; border-left: 3px solid #ff9800; margin-top: 10px;'>
            <p style='font-size: 10px; color: #495057; margin: 0;'>💡 <b>İpucu:</b> Müşteri ekranı üzerinden müşterileriniz şifreleriyle girip saatlerini ve borçlarını görebilir.</p>
        </div>
    """, unsafe_allow_html=True)

# Üst Başlık Alanı
st.markdown('<p class="main-header">🏗️ DİNAMİK VİNÇ & OPERASYON YÖNETİMİ</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">Aktif Modül (Yönetici): <b style="color: #ff9800;">{secim}</b></p>', unsafe_allow_html=True)

# --- 1. CARİ ÖZET / ALACAK VERECEK ---
if secim == "📊 Cari & Alacak Özeti":
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
                
                whatsapp_text = f"Sayın {unvan}, {datetime.now().strftime('%d.%m.%Y')} tarihi itibarıyla güncel kalan borç/bakiye tutarınız: {kalan:,.2f} TL'dir. Dinamik Vinç - İyi çalışmalar dileriz."
                st.code(whatsapp_text, language="text")
                st.caption("📲 Yukarıdaki metni kopyalayarak müşteriye WhatsApp üzerinden borç hatırlatması gönderebilirsiniz.")
    else:
        st.info("Henüz kayıtlı müşteri veya iş bulunmuyor.")

# --- 2. YENİ İŞ / OPERASYON GİRİŞİ ---
elif secim == "📝 Yeni İş / Operasyon":
    st.header("📝 Yeni İş / Operasyon Kaydı")
    
    cursor.execute("SELECT id, unvan FROM musteriler")
    musteriler = cursor.fetchall()
    
    if not musteriler:
        st.warning("⚠️ Önce sol menüden 'Müşteri Yönetimi' kısmına giderek bir müşteri eklemelisiniz!")
    else:
        musteri_dict = {m[1]: m[0] for m in musteriler}
        secilen_musteri_adi = st.selectbox("Müşteri Firma Seç", list(musteri_dict.keys()))
        musteri_id = musteri_dict[secilen_musteri_adi]
        
        col1, col2 = st.columns(2)
        with col1:
            tarih = st.date_input("İş Tarihi", datetime.now()).strftime("%d.%m.%Y")
            santiye = st.text_input("Şantiye Adı / Konum")
            vinc = st.text_input("Vinç / Plaka (Örn: 34 VNC 01)")
            operator = st.text_input("Operatör Adı")
            
        with col2:
            ucret_tipi = st.selectbox("Çalışma / Ücret Tipi", ["Saatlik Çalışma", "Günlük Çalışma (Yevmiye)"])
            
            if ucret_tipi == "Saatlik Çalışma":
                sure = st.number_input("Çalışma Süresi (Saat)", min_value=0.5, value=1.0, step=0.5)
                birim_fiyat = st.number_input("Saatlik Birim Fiyat (TL)", min_value=0.0, value=0.0, step=100.0)
            else:
                sure = st.number_input("Çalışma Süresi (Gün)", min_value=1.0, value=1.0, step=1.0)
                birim_fiyat = st.number_input("Günlük Yevmiye Fiyatı (TL)", min_value=0.0, value=0.0, step=500.0)
                
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
            st.success("Saha belgesi başarıyla yüklendi!")

        st.markdown("")
        if st.button("🚀 İşi ve Operasyonu Kaydet", type="primary"):
            temel_tutar = sure * birim_fiyat
            tam_aciklama = f"[{ucret_tipi} - {sure} { 'Saat' if 'Saatlik' in ucret_tipi else 'Gün' }] {aciklama}"
            
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
            """, (musteri_id, tarih, santiye, vinc, operator, tam_aciklama, sure, birim_fiyat, kdv_tipi, toplam_tutar, odenen, kalan, foto_yolu))
            conn.commit()
            st.success(f"İş başarıyla kaydedildi! Toplam Tutar: {toplam_tutar:,.2f} TL | Kalan Bakiye: {kalan:,.2f} TL")

# --- 3. İŞ GEÇMİŞİ & TAHSİLAT ---
elif secim == "📂 İş Geçmişi & Tahsilat":
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
        st.info("Kayıtlı iş bulunmuyor.")

# --- 4. MÜŞTERİ YÖNETİMİ ---
elif secim == "👥 Müşteri Yönetimi":
    st.header("👥 Müşteri / Firma Yönetimi ve Şifreler")
    
    with st.form("musteri_form"):
        unvan = st.text_input("Firma / Müşteri Unvanı")
        telefon = st.text_input("Telefon Numarası")
        adres = st.text_area("Adres")
        m_sifre = st.text_input("Müşteri Portal Giriş Şifresi", value="1234")
        submitted = st.form_submit_button("➕ Yeni Müşteri Kaydet")
        
        if submitted:
            if unvan.strip():
                cursor.execute("INSERT INTO musteriler (unvan, telefon, adres, sifre) VALUES (?, ?, ?, ?)", (unvan, telefon, adres, m_sifre))
                conn.commit()
                st.success(f"'{unvan}' başarıyla eklendi! Müşteri şifresi: {m_sifre}")
                st.rerun()
            else:
                st.error("Firma unvanı boş olamaz!")
                
    st.divider()
    st.subheader("📋 Kayıtlı Müşteriler ve Şifre Düzenleme")
    
    cursor.execute("SELECT id, unvan, telefon, adres, COALESCE(sifre, '1234') FROM musteriler")
    m_rows = cursor.fetchall()
    
    if m_rows:
        for m in m_rows:
            m_id, m_unvan, m_tel, m_adres, m_sif = m
            with st.expander(f"🏢 {m_unvan} (Tel: {m_tel})"):
                yeni_sifre_input = st.text_input(f"Müşteri Şifresini Güncelle [{m_unvan}]", value=m_sif, key=f"m_sif_{m_id}")
                col_ g1, col_g2 = st.columns(2)
                with col_g1:
                    if st.button("💾 Şifreyi Kaydet", key=f"sif_btn_{m_id}"):
                        cursor.execute("UPDATE musteriler SET sifre = ? WHERE id = ?", (yeni_sifre_input, m_id))
                        conn.commit()
                        st.success("Müşteri şifresi güncellendi!")
                        st.rerun()
                with col_g2:
                    if st.button("🗑️ Müşteriyi Sil", key=f"m_sil_{m_id}"):
                        cursor.execute("DELETE FROM isler WHERE musteri_id = ?", (m_id,))
                        cursor.execute("DELETE FROM musteriler WHERE id = ?", (m_id,))
                        conn.commit()
                        st.error(f"'{m_unvan}' ve tüm geçmişi silindi!")
                        st.rerun()
            st.divider()
    else:
        st.info("Henüz müşteri eklenmemiş.")