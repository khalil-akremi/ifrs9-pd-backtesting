# dashboard/pages/montecarlo_page.py

import streamlit as st
import requests
import plotly.graph_objects as go
import numpy as np

API_URL = "http://127.0.0.1:8000"

def show():
    
    st.markdown("## 📈 Monte Carlo — Simulation ECL")
    st.markdown("""
    La simulation Monte Carlo génère **10,000 scénarios possibles** pour estimer 
    la distribution de l'ECL en modélisant l'incertitude sur PD, LGD et EAD.
    
    $$ECL = PD \\times LGD \\times EAD$$
    """)
    st.markdown("---")
    
    # ── Formulaire ─────────────────────────────────────────────────────────────
    with st.form("mc_form"):
        
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
            n_sim        = st.selectbox("Nombre de simulations", 
                                        [1000, 5000, 10000, 50000], index=2)
        
        submitted = st.form_submit_button("📈 Lancer la simulation",
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
        
        with st.spinner(f"Simulation de {n_sim:,} scénarios en cours..."):
            response = requests.post(
                f"{API_URL}/monte-carlo?n_sim={n_sim}", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            st.markdown("---")
            st.markdown("### 📊 Résultats")
            
            # ── KPIs ───────────────────────────────────────────────────────────
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ECL Moyen",        f"${result['ecl_mean']:,.2f}")
            col2.metric("ECL Déterministe", f"${result['ecl_deterministic']:,.2f}")
            col3.metric("VaR 95%",          f"${result['ecl_var_95']:,.2f}")
            col4.metric("VaR 99%",          f"${result['ecl_var_99']:,.2f}")
            
            col1, col2 = st.columns(2)
            col1.metric("Expected Shortfall (95%)", f"${result['ecl_es_95']:,.2f}")
            col2.metric("Unexpected Loss", 
                        f"${result['ecl_var_99'] - result['ecl_mean']:,.2f}")
            
            st.markdown("---")
            
            # ── Distribution ECL ───────────────────────────────────────────────
            st.markdown("### 📉 Distribution de l'ECL")
            
            ecl_dist = result['ecl_distribution']
            
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x         = ecl_dist,
                nbinsx    = 80,
                name      = 'Distribution ECL',
                marker_color = 'steelblue',
                opacity   = 0.7
            ))
            
            # Lignes de référence
            fig.add_vline(x=result['ecl_mean'], line_color='black', 
                         line_width=2,
                         annotation_text=f"ECL moyen: ${result['ecl_mean']:,.0f}",
                         annotation_position="top right")
            fig.add_vline(x=result['ecl_var_95'], line_color='red', 
                         line_width=2, line_dash='dash',
                         annotation_text=f"VaR 95%: ${result['ecl_var_95']:,.0f}",
                         annotation_position="top right")
            fig.add_vline(x=result['ecl_var_99'], line_color='darkred', 
                         line_width=2, line_dash='dot',
                         annotation_text=f"VaR 99%: ${result['ecl_var_99']:,.0f}",
                         annotation_position="top right")
            
            # Zone Unexpected Loss
            fig.add_vrect(
                x0=result['ecl_mean'], x1=result['ecl_var_99'],
                fillcolor='red', opacity=0.1,
                annotation_text="Unexpected Loss",
                annotation_position="top left"
            )
            
            fig.update_layout(
                title  = f"Distribution ECL — {n_sim:,} simulations Monte Carlo",
                xaxis_title = "ECL ($)",
                yaxis_title = "Fréquence",
                height = 450,
                showlegend = False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ── Tableau résumé ─────────────────────────────────────────────────
            st.markdown("### 📋 Résumé statistique")
            
            import pandas as pd
            df_stats = pd.DataFrame({
                'Métrique'     : ['ECL Moyen', 'ECL Médian', 'ECL Std', 
                                  'VaR 95%', 'VaR 99%', 
                                  'Expected Shortfall 95%',
                                  'ECL Déterministe', 'Unexpected Loss'],
                'Valeur ($)'   : [
                    f"${result['ecl_mean']:,.2f}",
                    f"${result['ecl_median']:,.2f}",
                    f"${result['ecl_std']:,.2f}",
                    f"${result['ecl_var_95']:,.2f}",
                    f"${result['ecl_var_99']:,.2f}",
                    f"${result['ecl_es_95']:,.2f}",
                    f"${result['ecl_deterministic']:,.2f}",
                    f"${result['ecl_var_99'] - result['ecl_mean']:,.2f}"
                ],
                'Interprétation' : [
                    'Provision IFRS 9 recommandée',
                    '50% des scénarios en dessous',
                    'Incertitude de la simulation',
                    'Perte max dans 95% des scénarios',
                    'Perte max dans 99% des scénarios',
                    'Perte moyenne dans les 5% pires cas',
                    'ECL sans simulation (PD x LGD x EAD)',
                    'Capital économique additionnel'
                ]
            })
            
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            
            # ── Note IFRS 9 ────────────────────────────────────────────────────
            st.info("""
            💡 **Note IFRS 9** : La provision à constituer est l'**ECL moyen** 
            (Expected Loss). L'**Unexpected Loss** représente le capital 
            économique supplémentaire que la banque doit maintenir pour 
            absorber les scénarios défavorables au-delà des provisions.
            """)
        
        else:
            st.error(f"Erreur API : {response.status_code}")