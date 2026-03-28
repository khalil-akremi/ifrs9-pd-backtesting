# dashboard/app.py

import streamlit as st

# ── Configuration de la page ───────────────────────────────────────────────────
st.set_page_config(
    page_title = "IFRS 9 — PD Backtesting",
    page_icon  = "🏦",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ── Style CSS personnalisé ─────────────────────────────────────────────────────
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        padding: 20px 0;
    }
    .metric-card {
        background-color: #f0f4f8;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border-left: 5px solid #1f4e79;
    }
    .risk-very-low  { color: #27ae60; font-weight: bold; font-size: 1.5rem; }
    .risk-low       { color: #2ecc71; font-weight: bold; font-size: 1.5rem; }
    .risk-moderate  { color: #f39c12; font-weight: bold; font-size: 1.5rem; }
    .risk-high      { color: #e67e22; font-weight: bold; font-size: 1.5rem; }
    .risk-very-high { color: #e74c3c; font-weight: bold; font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

# ── Navigation ─────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/bank.png", width=80)
st.sidebar.title("IFRS 9 — PD Backtesting")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Accueil",
     "🔍 Prédiction Client",
     "📊 Backtesting",
     "📁 Portefeuille",
     "📄 Rapport PDF"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Modèles disponibles :**")
st.sidebar.markdown("✅ Régression Logistique")
st.sidebar.markdown("✅ Scorecard WoE/IV")
st.sidebar.markdown("✅ XGBoost")
st.sidebar.markdown("---")
st.sidebar.markdown("**Auteur :** Khalil Akremi")
st.sidebar.markdown("**ESSAI — 2026**")

# ── Import des pages ───────────────────────────────────────────────────────────
if page == "🏠 Accueil":
    from pages.home     import show
elif page == "🔍 Prédiction Client":
    from pages.predict  import show
elif page == "📊 Backtesting":
    from pages.backtest import show
elif page == "📁 Portefeuille":
    from pages.portfolio import show
elif page == "📄 Rapport PDF":
    from pages.report   import show

show()