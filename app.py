import streamlit as st
import os
from datetime import datetime
import psycopg2

# Sayfa Konfigürasyonu (Koyu tema zorlamasıyla)
st.set_page_config(page_title="Dinamik Vinç | Güvenli Yönetim Sistemi", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# --- GENEL ARKA PLAN VE ARAYÜZ STİLLERİ (KOYU TEMA) ---
st.markdown("""
    <style>
    /* Tüm ana uygulama arka planını koyu yap */
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    /* Üst menü ve header alanları */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }
    /* Metin renklerinin koyu temada okunabilir olması */
    p, span, label, div {
        color: #e0e0e0;
    }
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
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stButton>button:hover {
        border-color: #ff9800;
        color: #ff9800;
        background-color: #2b2b2b;
    }
    /* Kenar çubuğu (Sidebar) tasarımı */
    [data-testid="stSidebar"] {
        background-color: #181818;
        border-right: 1px solid #333333;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] span {
        color: #f0f0f0 !important;
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

# --- BULUT VERİTABANI BAĞLANTISI (PostgreSQL / Supabase) ---
def init_db():
    database_url = st.secrets.get("DATABASE_URL")
    
    if not database_url:
        st.error("⚠️ Streamlit secrets içinde DATABASE_URL bulunamadı! Lütfen ayarlardan DATABASE_URL ekleyin.")
        st.stop()
        
    conn = psycopg2.connect(database_url, sslmode='require')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS musteriler (
            id SERIAL PRIMARY KEY,
            unvan TEXT NOT NULL,
            telefon TEXT,
            adres TEXT,
            sifre TEXT DEFAULT '1234'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS isler (
            id SERIAL PRIMARY KEY,
            musteri_id INTEGER REFERENCES musteriler(id) ON DELETE CASCADE,
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
            foto_yolu TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ayarlar (
            anahtar TEXT PRIMARY KEY,
            deger TEXT
        )
    """)
    cursor.execute("INSERT INTO ayarlar (anahtar, deger) VALUES ('admin_sifre', '1234') ON CONFLICT (anahtar) DO NOTHING")
    
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# Oturum Durumu Kontrolleri
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
if "giris_turu" not in st.session_state:
    st.session_state["giris_turu"] = None 
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
            <div style='background-color: #1e1e1e; padding: 25px; border-radius: 12px; border: 1px solid #333; text-align: center;'>
                <h1 style='color: #ff9800; font-size: 26px; margin-bottom: 5px;'>🏗️ DİNAMİK VİNÇ</h1>
                <p style='color: #aaa; font-size: 13px;'>Operasyon ve Müşteri Portal Girişi</p>
            </div>
        """, unsafe_allow_html=True)
        
        giris_tipi = st.radio("Giriş Türü Seçin", ["👑 Yönetici Girişi", "🏢 Müşteri Cari Girişi"], horizontal=True)
        
        if giris_tipi == "👑 Yönetici Girişi":
            with st.form("admin_login"):
                kullanici_adi = st.text_input("Yönetici Kullanıcı Adı")
                sifre = st.text_input("Yönetici Şifre", type="password")
                submitted = st.form_submit_button("🔒 Yönetici Olarak Giriş Yap", use_container_width=True)
                
                if submitted:
                    cursor.execute("SELECT deger FROM ayarlar WHERE anahtar = 'admin_sifre'")
                    db_admin_sifre = cursor.fetchone()[0]
                    
                    if kullanici_adi == "admin" and sifre == db_admin_sifre:
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
                        cursor.execute("SELECT sifre FROM musteriler WHERE id = %s", (m_id,))
                        db_res = cursor.fetchone()
                        db_sifre = db_res[0] if db_res and db_res[0] else "1234"
                            
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
        
        # --- GİRİŞ EKRANI ALT BİLGİ (İLETİŞİM VE BÜYÜK IBAN) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #444; text-align: center; color: #fff;'>
                <h4 style='color: #ff9800; margin-bottom: 12px; font-weight: 700;'>🏗️ DİNAMİK VİNÇ - İLETİŞİM & ÖDEME</h4>
                <p style='margin: 6px 0; font-size: 15px;'>📞 <b>Cep Tel:</b> 0534 651 65 16</p>
                <p style='margin: 6px 0; font-size: 15px;'>🏦 <b>Garanti Bankası</b> | 👤 <b>Abdulhamid Toğuşlu</b></p>
                <div style='margin-top: 12px; padding: 12px; background-color: #121212; border-radius: 8px; border: 1px dashed #ff9800;'>
                    <span style='font-size: 13px; color: #aaa; display: block; margin-bottom: 4px;'>ÖDEME İÇİN IBAN NUMARASI:</span>
                    <span style='font-size: 18px; color: #4CAF50; font-weight: 900; letter-spacing: 1px;'>TR12 0006 2001 1910 0006 8866 91</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.stop()


# ==========================================
# MÜŞTERİ PANELİ EKRANI
# ==========================================
if st.session_state["giris_turu"] == "musteri":
    st.markdown(f"""
        <div style='background-color: #262211; padding: 20px; border-radius: 10px; border-left: 5px solid #ff9800; margin-bottom: 20px;'>
            <h2 style='color: #ffb703; margin: 0;'>Hoş Geldiniz, {st.session_state["aktif_musteri_adi"]}</h2>
            <p style='color: #ccc; margin: 5px 0 0 0;'>Buradan şirketinize ait tüm operasyonları, çalışma saatlerini ve güncel borç/bakiye durumunuzu inceleyebilirsiniz.</p>
        </div>
    """, unsafe_allow_html=True)
    
    m_id = st.session_state["aktif_musteri_id"]
    
    query = """
        SELECT id, tarih, santiye, vinc_plaka, operator, aciklama, sure, toplam_tutar, odenen, kalan 
        FROM isler WHERE musteri_id = %s ORDER BY id DESC
    """
    cursor.execute(query, (m_id,))
    isler = cursor.fetchall()
    
    cursor.execute("SELECT COALESCE(SUM(toplam_tutar), 0), COALESCE(SUM(odenen), 0), COALESCE(SUM(kalan), 0) FROM isler WHERE musteri_id = %s", (m_id,))
    toplam_borc, toplam_odenen, kalan_bakiye = cursor.fetchone()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Toplam İş Hacmi", f"{toplam_borc:,.2f} TL")
    col2.metric("💳 Yapılan Toplam Ödeme", f"{toplam_odenen:,.2f} TL")
    col3.metric("⚠️ Güncel Kalan Borcunuz", f"{kalan_bakiye:,.2f} TL")
    
    st.divider()
    st.subheader("📋 Yapılan İşler, Saatler ve Detaylar")
    
    if isler:
        for is_item in isler:
            i_id, tarih, santiye, vinc, operator, aciklama, sure, toplam, odenen, kalan = is_item
            sure_str = f"{sure} Saat" if "Saat" in aciklama or sure < 24 else f"{int(sure)} Gün"
            
            with st.expander(f"📅 Tarih: {tarih} | Şantiye: {santiye} | Kalan Borç: **{kalan:,.2f} TL**"):
                st.write(f"**Vinç / Plaka:** {vinc if vinc else 'Belirtilmemiş'} | **Operatör:** {operator if operator else 'Belirtilmemiş'}")
                st.write(f"**Çalışma Süresi / Miktarı:** {sure_str}")
                st.write(f"**İş Açıklaması / Detay:** {aciklama}")
                st.markdown("---")
                st.write(f"**Toplam Tutar:** {toplam:,.2f} TL | **Ödenen:** {odenen:,.2f} TL | **Kalan:** **{kalan:,.2f} TL**")
    else:
        st.info("Henüz adınıza kaydedilmiş bir operasyon veya iş bulunmuyor.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Güvenli Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.session_state["giris_turu"] = None
        st.session_state["aktif_musteri_id"] = None
        st.rerun()

    # --- MÜŞTERİ PANELİ ALT BİLGİ (İLETİŞİM VE BÜYÜK IBAN) ---
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background-color: #1e1e1e; padding: 25px; border-radius: 12px; border: 1px solid #444; text-align: center; color: #fff;'>
            <h3 style='color: #ff9800; margin-bottom: 15px; font-weight: 700;'>🏗️ DİNAMİK VİNÇ - İLETİŞİM & ÖDEME BİLGİLERİ</h3>
            <p style='margin: 6px 0; font-size: 16px;'>📞 <b>İletişim / Cep Tel:</b> 0534 651 65 16</p>
            <p style='margin: 6px 0; font-size: 16px;'>🏦 <b>Banka:</b> Garanti Bankası &nbsp;|&nbsp; 👤 <b>Hesap Sahibi:</b> Abdulhamid Toğuşlu</p>
            <div style='margin-top: 15px; padding: 15px; background-color: #121212; border-radius: 8px; border: 1px dashed #ff9800;'>
                <span style='font-size: 14px; color: #aaa; display: block; margin-bottom: 6px;'>ÖDEME YAPACAĞINIZ RESMİ IBAN NUMARASI:</span>
                <span style='font-size: 20px; color: #4CAF50; font-weight: 900; letter-spacing: 1.5px;'>TR12 0006 2001 1910 0006 8866 91</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.stop()


# ==========================================
# YÖNETİCİ PANELİ EKRANI
# ==========================================
with st.sidebar:
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        st.markdown("<div style='background-color: #262211; padding: 10px; border-radius: 8px; border: 1px solid #ffeeba; text-align: center;'>", unsafe_allow_html=True)
        st.image(logo_path, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #ff9800;'>🏗️ DİNAMİK VİNÇ</h2>", unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; margin-top: 10px;"><span class="pro-badge">PRO EDITION v4.1 (Cloud)</span></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    menu_options = {
        "📊 Cari & Alacak Özeti": "Genel Finans ve Alacak Takibi",
        "📝 Yeni İş / Operasyon": "Saha dan Kiralama Girişi",
        "📂 İş Geçmişi & Tahsilat": "Arşiv, Ödeme ve Dekontlar",
        "👥 Müşteri Yönetimi": "Firma ve İletişim Rehberi",
        "⚙️ Admin Şifre Değiştir": "Yönetici Güvenlik Ayarları"
    }
    
    secim = st.radio("📋 OPERASYONEL MENÜ", list(menu_options.keys()))

    st.sidebar.divider()
    
    if st.sidebar.button("🚪 Yönetici Oturumunu Kapat"):
        st.session_state["giris_yapildi"] = False
        st.session_state["giris_turu"] = None
        st.rerun()

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
        GROUP BY musteriler.id, musteriler.unvan, musteriler.telefon
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
            st.markdown("""
                <style>
                input[type="date"]::-webkit-calendar-picker-indicator {
                    cursor: pointer;
                    filter: invert(1);
                }
                </style>
            """, unsafe_allow_html=True)
            
            tr_aylar = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
            tr_gunler = {"Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba", "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"}
            
            secilen_tarih = st.date_input("İş Tarihi", datetime.now())
            tarih = secilen_tarih.strftime("%d.%m.%Y")
            
            gun_en = secilen_tarih.strftime("%A")
            gun_tr = tr_gunler.get(gun_en, gun_en)
            ay_tr = tr_aylar.get(secilen_tarih.month, "")
            st.caption(f"📅 Seçilen Tarih: **{secilen_tarih.day} {ay_tr} {secilen_tarih.year} ({gun_tr})**")

            santiye = st.text_input("Şantiye Adı / Konum")
            vinc = st.text_input("Vinç / Plaka (Örn: 34 VNC 01)")
            operator = st.text_input("Operatör Adı")
            
        with col2:
            ucret_tipi = st.selectbox(
                "Çalışma / Ücret Tipi", 
                [
                    "Kademeli Saatlik (İlk X Saat + Sonraki Saat Başı Artış)", 
                    "Düz Saatlik Çalışma", 
                    "Günlük Çalışma (Yevmiye)"
                ]
            )
            
            temel_tutar = 0.0
            sure = 1.0
            
            if ucret_tipi == "Kademeli Saatlik (İlk X Saat + Sonraki Saat Başı Artış)":
                st.info("💡 Örn: İlk 1 saat 5000 TL, sonraki her saat 2000 TL artıyorsa; İlk Saat Fiyatına 5000, Saat Başı Artışa 2000 yazın.")
                c_col1, c_col2 = st.columns(2)
                with c_col1:
                    sure = st.number_input("Toplam Çalışma Süresi (Saat)", min_value=1.0, value=2.0, step=0.5)
                    ilk_saat_ucreti = st.number_input("İlk X Saat Fiyatı (TL)", min_value=0.0, value=5000.0, step=500.0)
                with c_col2:
                    sonraki_saat_basi_artis = st.number_input("Sonraki Her Saat Başı Artış (TL)", min_value=0.0, value=2000.0, step=100.0)
                
                if sure <= 1.0:
                    temel_tutar = ilk_saat_ucreti * sure
                else:
                    temel_tutar = ilk_saat_ucreti + ((sure - 1.0) * sonraki_saat_basi_artis)
                birim_fiyat = ilk_saat_ucreti 
                
            elif ucret_tipi == "Düz Saatlik Çalışma":
                sure = st.number_input("Çalışma Süresi (Saat)", min_value=0.5, value=1.0, step=0.5)
                birim_fiyat = st.number_input("Saatlik Birim Fiyat (TL)", min_value=0.0, value=2000.0, step=100.0)
                temel_tutar = sure * birim_fiyat
            else:
                sure = st.number_input("Çalışma Süresi (Gün)", min_value=1.0, value=1.0, step=1.0)
                birim_fiyat = st.number_input("Günlük Yevmiye Fiyatı (TL)", min_value=0.0, value=5000.0, step=500.0)
                temel_tutar = sure * birim_fiyat
                
            kdv_tipi = st.selectbox("Vergi / KDV Hesaplama", ["KDV Hariç (Düz Tutar)", "KDV Dahil (%20)", "İnşaat Tevkifatlı (5/10)"])
            odenen = st.number_input("Peşin Alınan Ödeme (TL)", min_value=0.0, value=0.0, step=100.0)
            
        aciklama = st.text_area("İşin Detay Açıklaması")
        
        uploaded_file = st.file_uploader("📸 Saha Tutanağı / Kantar / Çalışma Fişi Fotoğrafı", type=["png", "jpg", "jpeg"])
        foto_yolu = ""
        if uploaded_file is not None:
            os.makedirs("uploads", exist_ok=True)
            foto_yolu = os.path.join("uploads", uploaded_file.name)
            with open(foto_yolu, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Saha belgesi başarıyla yüklendi!")

        if st.button("🚀 İşi ve Operasyonu Kaydet", type="primary"):
            if "Kademeli" in ucret_tipi:
                tam_aciklama = f"[Kademeli: {sure} Saat | İlk Saat: {ilk_saat_ucreti} TL, Artış: {sonraki_saat_basi_artis} TL] {aciklama}"
            else:
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (musteri_id, tarih, santiye, vinc, operator, tam_aciklama, sure, birim_fiyat, kdv_tipi, toplam_tutar, odenen, kalan, foto_yolu))
            conn.commit()
            st.success(f"İş başarıyla kaydedildi! Hesaplanan Toplam Tutar: {toplam_tutar:,.2f} TL | Kalan Bakiye: {kalan:,.2f} TL")

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
                            cursor.execute("UPDATE isler SET odenen = %s, kalan = %s WHERE id = %s", (yeni_odenen, yeni_kalan, is_id))
                            conn.commit()
                            st.success(f"{tahsilat_miktari:,.2f} TL tahsilat işlendi!")
                            st.rerun()
                
                with col_sil:
                    st.write("") 
                    st.write("")
                    if st.button(f"🗑️ İşi Komple Sil", key=f"is_sil_{is_id}"):
                        cursor.execute("DELETE FROM isler WHERE id = %s", (is_id,))
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
                cursor.execute("INSERT INTO musteriler (unvan, telefon, adres, sifre) VALUES (%s, %s, %s, %s)", (unvan, telefon, adres, m_sifre))
                conn.commit()
                st.success(f"'{unvan}' başarıyla eklendi!")
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
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    if st.button("💾 Şifreyi Kaydet", key=f"sif_btn_{m_id}"):
                        cursor.execute("UPDATE musteriler SET sifre = %s WHERE id = %s", (yeni_sifre_input, m_id))
                        conn.commit()
                        st.success("Müşteri şifresi güncellendi!")
                        st.rerun()
                with col_g2:
                    if st.button("🗑️ Müşteriyi Sil", key=f"m_sil_{m_id}"):
                        cursor.execute("DELETE FROM isler WHERE musteri_id = %s", (m_id,))
                        cursor.execute("DELETE FROM musteriler WHERE id = %s", (m_id,))
                        conn.commit()
                        st.error(f"'{m_unvan}' ve tüm geçmişi silindi!")
                        st.rerun()
            st.divider()
    else:
        st.info("Henüz müşteri eklenmemiş.")

# --- 5. ADMIN ŞİFRE DEĞİŞTİR ---
elif secim == "⚙️ Admin Şifre Değiştir":
    st.header("⚙️ Yönetici (Admin) Şifre Güncelleme")
    st.write("Yönetici panelinize giriş yaptığınız şifreyi buradan güvenli bir şekilde değiştirebilirsiniz.")
    
    with st.form("admin_sifre_form"):
        eski_sifre = st.text_input("Mevcut Yönetici Şifreniz", type="password")
        yeni_sifre1 = st.text_input("Yeni Yönetici Şifresi", type="password")
        yeni_sifre2 = st.text_input("Yeni Yönetici Şifresi (Tekrar)", type="password")
        
        sifre_guncelle_btn = st.form_submit_button("🔒 Yönetici Şifresini Güncelle")
        
        if sifre_guncelle_btn:
            cursor.execute("SELECT deger FROM ayarlar WHERE anahtar = 'admin_sifre'")
            gercek_eski_sifre = cursor.fetchone()[0]
            
            if eski_sifre != gercek_eski_sifre:
                st.error("Mevcut şifrenizi hatalı girdiniz!")
            elif not yeni_sifre1:
                st.error("Yeni şifre boş olamaz!")
            elif yeni_sifre1 != yeni_sifre2:
                st.error("Yeni girdiğiniz şifreler birbiriyle eşleşmiyor!")
            else:
                cursor.execute("UPDATE ayarlar SET deger = %s WHERE anahtar = 'admin_sifre'", (yeni_sifre1,))
                conn.commit()
                st.success("Yönetici şifreniz başarıyla değiştirildi! Bir sonraki girişinizde yeni şifrenizi kullanabilirsiniz.")