# dashboard/app.py

import streamlit as st
from config import API_URL

st.set_page_config(
    page_title            = "IFRS 9 — PD Backtesting",
    page_icon             = "🏦",
    layout                = "wide",
    initial_sidebar_state = "expanded"
)

st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        padding: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.image("https://img.icons8.com/color/96/bank.png", width=80)
st.sidebar.title("IFRS 9 — PD Backtesting")
st.sidebar.markdown("---")

# ── Navigation avec selectbox ──────────────────────────────────────────────────
page = st.sidebar.selectbox(
    "Navigation",
    ["🏠 Accueil",
     "🔍 Prédiction Client",
     "📊 Backtesting",
     "📁 Portefeuille",
     "🔬 SHAP Explicabilité",
     "📈 Monte Carlo ECL",
     "⚡ Stress Testing",
     "📄 Rapport PDF"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Modèles disponibles :**")
st.sidebar.markdown("✅ Régression Logistique")
st.sidebar.markdown("✅ Scorecard WoE/IV")
st.sidebar.markdown("✅ XGBoost")
st.sidebar.markdown("---")
st.sidebar.markdown("**Auteur :** Khalil Akremi")
st.sidebar.markdown("**ESSAI — 2026**")

if page == "🏠 Accueil":
    from pages.home            import show
elif page == "🔍 Prédiction Client":
    from pages.predict         import show
elif page == "📊 Backtesting":
    from pages.backtest        import show
elif page == "📁 Portefeuille":
    from pages.portfolio       import show
elif page == "🔬 SHAP Explicabilité":
    from pages.shap_page       import show
elif page == "📈 Monte Carlo ECL":
    from pages.montecarlo_page import show
elif page == "⚡ Stress Testing":
    from pages.stress_page     import show
elif page == "📄 Rapport PDF":
    from pages.report          import show

show()