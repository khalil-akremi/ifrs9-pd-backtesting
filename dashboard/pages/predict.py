# dashboard/pages/predict.py

import streamlit as st
import requests
import plotly.graph_objects as go

API_URL = "http://127.0.0.1:8000"

def show():
    
    st.markdown("## 🔍 Prédiction — Probabilité de Défaut")
    st.markdown("Entrez les caractéristiques d'un client pour obtenir sa PD.")
    st.markdown("---")
    
    # ── Formulaire client ──────────────────────────────────────────────────────
    with st.form("prediction_form"):
        
        st.markdown("### 👤 Informations client")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.slider("Age", min_value=18, max_value=110, value=45)
            monthly_income = st.number_input("Revenu mensuel ($)", 
                                             min_value=0, max_value=50000, value=6500)
            debt_ratio = st.slider("Debt Ratio", min_value=0.0, 
                                   max_value=1.0, value=0.4, step=0.01)
            revolving = st.slider("Utilisation crédit renouvelable", 
                                  min_value=0.0, max_value=1.0, 
                                  value=0.35, step=0.01)
            dependents = st.number_input("Nombre de personnes à charge", 
                                         min_value=0, max_value=20, value=2)
        
        with col2:
            open_credits = st.number_input("Lignes de crédit ouvertes", 
                                           min_value=0, max_value=60, value=8)
            real_estate = st.number_input("Prêts immobiliers", 
                                          min_value=0, max_value=54, value=1)
            late_30_59 = st.number_input("Retards 30-59 jours", 
                                         min_value=0, max_value=20, value=0)
            late_60_89 = st.number_input("Retards 60-89 jours", 
                                         min_value=0, max_value=20, value=0)
            late_90    = st.number_input("Retards 90+ jours", 
                                         min_value=0, max_value=20, value=0)
        
        submitted = st.form_submit_button("🔮 Calculer la PD", 
                                          use_container_width=True)
    
    # ── Résultats ──────────────────────────────────────────────────────────────
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
        
        with st.spinner("Calcul en cours..."):
            response = requests.post(f"{API_URL}/predict", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            st.markdown("---")
            st.markdown("### 📊 Résultats")
            
            # ── Niveau de risque ───────────────────────────────────────────────
            risk_colors = {
                "Très faible" : "🟢",
                "Faible"      : "🟢",
                "Modéré"      : "🟡",
                "Élevé"       : "🟠",
                "Très élevé"  : "🔴"
            }
            
            emoji = risk_colors.get(result['niveau_risque'], "⚪")
            st.markdown(f"## {emoji} Niveau de risque : **{result['niveau_risque']}**")
            
            # ── Métriques principales ──────────────────────────────────────────
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("PD Moyenne",    f"{result['PD_moyenne']*100:.2f}%")
            col2.metric("PD Logistique", f"{result['PD_logistic']*100:.2f}%")
            col3.metric("PD Scorecard",  f"{result['PD_scorecard']*100:.2f}%")
            col4.metric("PD XGBoost",    f"{result['PD_xgboost']*100:.2f}%")
            
            st.metric("ECL Estimé", f"${result['ECL_estime']:,.2f}")
            
            # ── Graphique PD par modèle ────────────────────────────────────────
            fig = go.Figure(go.Bar(
                x     = ['Régression LR', 'Scorecard WoE', 'XGBoost', 'Moyenne'],
                y     = [result['PD_logistic'], result['PD_scorecard'], 
                         result['PD_xgboost'],  result['PD_moyenne']],
                marker_color = ['steelblue', 'seagreen', 'salmon', 'gold'],
                text  = [f"{v*100:.2f}%" for v in [
                    result['PD_logistic'], result['PD_scorecard'],
                    result['PD_xgboost'],  result['PD_moyenne']]],
                textposition = 'outside'
            ))
            
            fig.update_layout(
                title       = 'PD par modèle',
                yaxis_title = 'Probabilité de Défaut',
                yaxis_range = [0, 1],
                height      = 400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ── Interprétation ─────────────────────────────────────────────────
            st.markdown("### 🔎 Facteurs de risque")
            for key, value in result['interpretation'].items():
                st.markdown(f"- {value}")
        
        else:
            st.error(f"Erreur API : {response.status_code}")