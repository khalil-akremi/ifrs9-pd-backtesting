# dashboard/pages/backtest.py

import streamlit as st
import requests
import plotly.graph_objects as go
import numpy as np

# Nouvelle ligne — dans chaque page
from config import API_URL

def show():
    
    st.markdown("## 📊 Backtesting IFRS 9")
    st.markdown("Résultats complets de la validation du modèle PD.")
    st.markdown("---")
    
    # ── Chargement des métriques ───────────────────────────────────────────────
    try:
        metrics = requests.get(f"{API_URL}/metrics").json()
    except:
        st.error("❌ API non disponible")
        return
    
    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "🎯 Discrimination", 
        "📐 Calibration", 
        "📉 Stabilité PSI"
    ])
    
    # ── Tab 1 — Discrimination ─────────────────────────────────────────────────
    with tab1:
        
        st.markdown("### Métriques de discrimination")
        st.markdown("""
        La discrimination mesure la capacité du modèle à **séparer** 
        les bons et mauvais payeurs.
        """)
        
        # Tableau des métriques
        col1, col2, col3 = st.columns(3)
        
        for col, (name, key, color) in zip(
            [col1, col2, col3],
            [("🔵 Régression LR", "LR", "steelblue"),
             ("🟢 Scorecard WoE", "WoE", "seagreen"),
             ("🔴 XGBoost",       "XGB", "salmon")]
        ):
            with col:
                st.markdown(f"#### {name}")
                auc  = metrics['discrimination'][key]['AUC']
                gini = metrics['discrimination'][key]['Gini']
                ks   = metrics['discrimination'][key]['KS']
                
                st.metric("AUC",  f"{auc:.4f}",  
                          delta="✅ Excellent" if auc > 0.80 else "⚠️ Acceptable")
                st.metric("Gini", f"{gini:.4f}", 
                          delta="✅ Excellent" if gini > 0.60 else "⚠️ Acceptable")
                st.metric("KS",   f"{ks:.4f}",   
                          delta="✅ Excellent" if ks > 0.40 else "⚠️ Acceptable")
        
        st.markdown("---")
        
        # Graphique comparaison
        fig = go.Figure()
        
        modeles   = ['Régression LR', 'Scorecard WoE', 'XGBoost']
        auc_vals  = [metrics['discrimination'][k]['AUC']  for k in ['LR','WoE','XGB']]
        gini_vals = [metrics['discrimination'][k]['Gini'] for k in ['LR','WoE','XGB']]
        ks_vals   = [metrics['discrimination'][k]['KS']   for k in ['LR','WoE','XGB']]
        
        fig.add_trace(go.Bar(name='AUC',  x=modeles, y=auc_vals,  
                             marker_color='steelblue'))
        fig.add_trace(go.Bar(name='Gini', x=modeles, y=gini_vals, 
                             marker_color='seagreen'))
        fig.add_trace(go.Bar(name='KS',   x=modeles, y=ks_vals,   
                             marker_color='salmon'))
        
        # Lignes de seuil
        fig.add_hline(y=0.80, line_dash="dash", line_color="blue",
                      annotation_text="Seuil AUC (0.80)")
        fig.add_hline(y=0.60, line_dash="dash", line_color="green",
                      annotation_text="Seuil Gini (0.60)")
        fig.add_hline(y=0.40, line_dash="dash", line_color="red",
                      annotation_text="Seuil KS (0.40)")
        
        fig.update_layout(
            barmode     = 'group',
            title       = 'Comparaison des métriques de discrimination',
            yaxis_range = [0, 1.1],
            height      = 450
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ── Tab 2 — Calibration ────────────────────────────────────────────────────
    with tab2:
        
        st.markdown("### Métriques de calibration")
        st.markdown("""
        La calibration vérifie que les **probabilités prédites** 
        correspondent aux taux de défaut réellement observés.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        for col, (name, key) in zip(
            [col1, col2, col3],
            [("🔵 Régression LR", "LR"),
             ("🟢 Scorecard WoE", "WoE"),
             ("🔴 XGBoost",       "XGB")]
        ):
            with col:
                st.markdown(f"#### {name}")
                brier = metrics['calibration'][key]['Brier']
                st.metric("Brier Score", f"{brier:.4f}",
                          delta="✅ Bon" if brier < 0.10 else "⚠️ Acceptable")
        
        st.markdown("---")
        st.info("""
        💡 **Note** : Les modèles ont été recalibrés via **Platt Scaling** 
        pour corriger la surestimation des PD due au class_weight='balanced'.
        Le Brier Score a été réduit de ~65% après recalibration.
        """)
    
    # ── Tab 3 — Stabilité PSI ──────────────────────────────────────────────────
    with tab3:
        
        st.markdown("### Population Stability Index (PSI)")
        st.markdown("""
        Le PSI mesure si la population du **test** ressemble à celle 
        sur laquelle le modèle a été entraîné.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        for col, (name, key) in zip(
            [col1, col2, col3],
            [("🔵 Régression LR", "LR"),
             ("🟢 Scorecard WoE", "WoE"),
             ("🔴 XGBoost",       "XGB")]
        ):
            with col:
                st.markdown(f"#### {name}")
                psi = metrics['stability'][key]['PSI']
                st.metric("PSI", f"{psi:.4f}",
                          delta="✅ Stable" if psi < 0.10 else "⚠️ Surveiller")
        
        st.markdown("---")
        
        # Graphique seuils PSI
        fig = go.Figure()
        
        modeles  = ['Régression LR', 'Scorecard WoE', 'XGBoost']
        psi_vals = [metrics['stability'][k]['PSI'] for k in ['LR','WoE','XGB']]
        
        fig.add_trace(go.Bar(
            x            = modeles,
            y            = psi_vals,
            marker_color = ['steelblue', 'seagreen', 'salmon'],
            text         = [f"{v:.4f}" for v in psi_vals],
            textposition = 'outside'
        ))
        
        fig.add_hline(y=0.10, line_dash="dash", line_color="orange",
                      annotation_text="Seuil attention (0.10)")
        fig.add_hline(y=0.25, line_dash="dash", line_color="red",
                      annotation_text="Seuil critique (0.25)")
        
        fig.update_layout(
            title       = 'PSI — Stabilité des 3 modèles',
            yaxis_title = 'PSI',
            yaxis_range = [0, 0.30],
            height      = 400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        💡 **Note** : Les PSI très faibles s'expliquent par le fait que 
        le train et le test Kaggle proviennent de la même source et période. 
        Dans un contexte bancaire réel, des valeurs entre 0.05 et 0.15 
        seraient typiques.
        """)