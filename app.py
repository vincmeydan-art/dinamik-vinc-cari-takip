/* Tüm genel arka plan */
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    header[data-testid="stHeader"] {
        background-color: transparent;
    }
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

    /* --- BUTON STİLLERİ (Giriş Butonları ve Form Butonları Dahil) --- */
    .stButton>button, 
    div[data-testid="stFormSubmitButton"]>button,
    button[kind="secondaryFormSubmit"],
    button[kind="primaryFormSubmit"] {
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        border: 1px solid #ff9800 !important;
        background-color: #ff9800 !important;
        color: #000000 !important;
    }

    /* Buton üzerine gelindiğinde (Hover) */
    .stButton>button:hover, 
    div[data-testid="stFormSubmitButton"]>button:hover,
    button[kind="secondaryFormSubmit"]:hover,
    button[kind="primaryFormSubmit"]:hover {
        border-color: #ffb703 !important;
        background-color: #ffb703 !important;
        color: #000000 !important;
    }

    /* Buton içindeki tüm ikon ve metinleri simsiyah yap */
    .stButton>button *, 
    div[data-testid="stFormSubmitButton"]>button * {
        color: #000000 !important;
        font-weight: 800 !important;
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