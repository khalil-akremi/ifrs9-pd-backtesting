# dashboard/pages/shap_page.py

import streamlit as st
import requests
import plotly.graph_objects as go

# Nouvelle ligne — dans chaque page
from config import API_URL

def show():
    
    st.markdown("## 🔬 SHAP — Explicabilité du Modèle XGBoost")
    st.markdown("""
    SHAP (SHapley Additive exPlanations) explique **pourquoi** le modèle 
    prédit une PD spécifique pour chaque client en décomposant la prédiction 
    en contributions individuelles de chaque feature.
    """)
    st.markdown("---")
    
    # ── Formulaire client ──────────────────────────────────────────────────────
    with st.form("shap_form"):
        
        st.markdown("### 👤 Caractéristiques du client")
        col1, col2 = st.columns(2)
        
        with col1:
            age            = st.slider("Age", 18, 110, 45)
            monthly_income = st.number_input("Revenu mensuel ($)", 0, 50000, 6500)
            debt_ratio     = st.slider("Debt Ratio", 0.0, 1.0, 0.4, 0.01)
            revolving      = st.slider("Utilisation crédit", 0.0, 1.0, 0.35, 0.01)
            dependents     = st.number_input("Personnes à charge", 0, 20, 2)
        
        with col2:
            open_credits = st.number_input("Lignes de crédit", 0, 60, 8)
            real_estate  = st.number_input("Prêts immobiliers", 0, 54, 1)
            late_30_59   = st.number_input("Retards 30-59j", 0, 20, 0)
            late_60_89   = st.number_input("Retards 60-89j", 0, 20, 0)
            late_90      = st.number_input("Retards 90j+", 0, 20, 0)
        
        submitted = st.form_submit_button("🔬 Analyser avec SHAP",
                                          use_container_width=True)
    
    if submitted:
        
        payload = {
            "RevolvingUtilizationOfUnsecuredLines" : revolving,
            "age"                                  : age,
            "NumberOfTime30_59DaysPastDueNotWorse" : late_30_59,
            "DebtRatio"                            : debt_ratio,
            "MonthlyIncome"                        : monthly_income,
            "NumberOfOpenCreditLinesAndLoans"      : open_credits,
            "NumberOfTimes90DaysLate"              : late_90,
            "NumberRealEstateLoansOrLines"         : real_estate,
            "NumberOfTime60_89DaysPastDueNotWorse" : late_60_89,
            "NumberOfDependents"                   : dependents
        }
        
        with st.spinner("Calcul des valeurs SHAP..."):
            response = requests.post(f"{API_URL}/shap", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            st.markdown("---")
            st.markdown("### 📊 Résultats SHAP")
            
            # ── Métriques principales ──────────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            col1.metric("PD Prédite (XGBoost)", 
                        f"{result['pd_predicted']*100:.2f}%")
            col2.metric("Valeur de base", 
                        f"{result['base_value']*100:.2f}%")
            col3.metric("Facteur de risque principal", 
                        result['top_risk_factor'].replace('NumberOf', ''))
            
            st.markdown("---")
            
            # ── Waterfall Chart ────────────────────────────────────────────────
            st.markdown("### 🌊 Waterfall Chart — Contribution de chaque feature")
            st.markdown("""
            - **Barres rouges** → augmentent la PD
            - **Barres bleues** → diminuent la PD
            - La somme des contributions = PD prédite - valeur de base
            """)
            
            contributions = result['contributions']
            features      = list(contributions.keys())
            shap_vals     = [contributions[f]['shap_value'] for f in features]
            directions    = [contributions[f]['direction'] for f in features]
            
            colors = ['#e74c3c' if d == 'augmente le risque' 
                     else '#2ecc71' for d in directions]
            
            fig = go.Figure(go.Bar(
                x          = shap_vals,
                y          = [f.replace('NumberOf', '') for f in features],
                orientation= 'h',
                marker_color = colors,
                text       = [f"{v:+.4f}" for v in shap_vals],
                textposition = 'outside'
            ))
            
            fig.add_vline(x=0, line_color='black', line_width=1)
            fig.update_layout(
                title  = f"Contributions SHAP — PD = {result['pd_predicted']*100:.2f}%",
                xaxis_title = "Contribution SHAP",
                height = 500,
                xaxis  = dict(zeroline=True)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ── Tableau détaillé ───────────────────────────────────────────────
            st.markdown("### 📋 Détail des contributions")
            
            import pandas as pd
            df_shap = pd.DataFrame([
                {
                    'Feature'       : f,
                    'Valeur SHAP'   : f"{contributions[f]['shap_value']:+.4f}",
                    'Direction'     : contributions[f]['direction'],
                    'Impact'        : '🔴 Risque' if contributions[f]['direction'] == 'augmente le risque' else '🟢 Protection'
                }
                for f in features
            ])
            
            st.dataframe(df_shap, use_container_width=True, hide_index=True)
            
            # ── Explication narrative ──────────────────────────────────────────
            st.markdown("### 💡 Interprétation")
            
            top_risk = [f for f in features 
                       if contributions[f]['direction'] == 'augmente le risque'][:3]
            top_prot = [f for f in features 
                       if contributions[f]['direction'] == 'diminue le risque'][:2]
            
            st.info(f"""
            **Facteurs qui augmentent le risque :**
            {', '.join([f.replace('NumberOf', '') for f in top_risk])}
            
            **Facteurs protecteurs :**
            {', '.join([f.replace('NumberOf', '') for f in top_prot]) if top_prot else 'Aucun'}
            
            **Valeur de base :** {result['base_value']*100:.2f}% (PD moyenne du portefeuille)
            **PD finale :** {result['pd_predicted']*100:.2f}%
            """)
        
        else:
            st.error(f"Erreur API : {response.status_code}")