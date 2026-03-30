# dashboard/pages/home.py

import streamlit as st
import requests
import plotly.graph_objects as go

# Nouvelle ligne — dans chaque page
from config import API_URL

def show():
    
    st.markdown('<p class="main-title">🏦 IFRS 9 — Backtesting PD</p>', 
                unsafe_allow_html=True)
    st.markdown("### Projet de validation de modèle de Probabilité de Défaut")
    st.markdown("---")
    
    # ── Statut API ─────────────────────────────────────────────────────────────
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.status_code == 200:
            st.success("✅ API connectée et opérationnelle")
        else:
            st.error("❌ API non disponible")
    except:
        st.error("❌ API non disponible — lancez uvicorn avant le dashboard")
        return
    
    st.markdown("---")
    
    # ── Métriques clés ─────────────────────────────────────────────────────────
    st.markdown("### 📊 Résultats du Backtesting IFRS 9")
    
    try:
        metrics = requests.get(f"{API_URL}/metrics").json()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔵 Régression Logistique")
            st.metric("AUC",  f"{metrics['discrimination']['LR']['AUC']:.4f}")
            st.metric("Gini", f"{metrics['discrimination']['LR']['Gini']:.4f}")
            st.metric("KS",   f"{metrics['discrimination']['LR']['KS']:.4f}")
        
        with col2:
            st.markdown("#### 🟢 Scorecard WoE/IV")
            st.metric("AUC",  f"{metrics['discrimination']['WoE']['AUC']:.4f}")
            st.metric("Gini", f"{metrics['discrimination']['WoE']['Gini']:.4f}")
            st.metric("KS",   f"{metrics['discrimination']['WoE']['KS']:.4f}")
        
        with col3:
            st.markdown("#### 🔴 XGBoost")
            st.metric("AUC",  f"{metrics['discrimination']['XGB']['AUC']:.4f}")
            st.metric("Gini", f"{metrics['discrimination']['XGB']['Gini']:.4f}")
            st.metric("KS",   f"{metrics['discrimination']['XGB']['KS']:.4f}")
    
    except Exception as e:
        st.error(f"Erreur chargement métriques : {e}")
    
    st.markdown("---")
    
    # ── Graphique comparaison ──────────────────────────────────────────────────
    st.markdown("### 📈 Comparaison des modèles")
    
    fig = go.Figure()
    
    modeles  = ['Régression LR', 'Scorecard WoE', 'XGBoost']
    auc_vals = [
        metrics['discrimination']['LR']['AUC'],
        metrics['discrimination']['WoE']['AUC'],
        metrics['discrimination']['XGB']['AUC']
    ]
    gini_vals = [
        metrics['discrimination']['LR']['Gini'],
        metrics['discrimination']['WoE']['Gini'],
        metrics['discrimination']['XGB']['Gini']
    ]
    ks_vals = [
        metrics['discrimination']['LR']['KS'],
        metrics['discrimination']['WoE']['KS'],
        metrics['discrimination']['XGB']['KS']
    ]
    
    fig.add_trace(go.Bar(name='AUC',  x=modeles, y=auc_vals,  marker_color='steelblue'))
    fig.add_trace(go.Bar(name='Gini', x=modeles, y=gini_vals, marker_color='seagreen'))
    fig.add_trace(go.Bar(name='KS',   x=modeles, y=ks_vals,   marker_color='salmon'))
    
    fig.update_layout(
        barmode     = 'group',
        title       = 'Métriques de discrimination — 3 modèles',
        yaxis_range = [0, 1],
        height      = 400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ── Contexte IFRS 9 ────────────────────────────────────────────────────────
    st.markdown("### 📖 Contexte IFRS 9")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **IFRS 9** impose aux banques de calculer les pertes de crédit 
        attendues (ECL) selon :
        
        $$ECL = PD \\times LGD \\times EAD$$
        
        Ce projet valide la composante **PD** selon 3 dimensions :
        - ✅ **Discrimination** — AUC, Gini, KS, CAP
        - ✅ **Calibration** — Brier Score, analyse par décile
        - ✅ **Stabilité** — Population Stability Index (PSI)
        """)
    
    with col2:
        st.markdown("""
        **Dataset** : Give Me Some Credit — Kaggle
        
        | Caractéristique | Valeur |
        |---|---|
        | Observations train | 149,999 |
        | Observations test | 101,503 |
        | Features | 11 |
        | Taux de défaut | 6.68% |
        """)