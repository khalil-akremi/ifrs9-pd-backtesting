# dashboard/pages/portfolio.py

import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Nouvelle ligne — dans chaque page
from config import API_URL

def show():
    
    st.markdown("## 📁 Analyse de Portefeuille")
    st.markdown("Uploadez un fichier CSV de clients pour scorer tout le portefeuille.")
    st.markdown("---")
    
    # ── Format attendu ─────────────────────────────────────────────────────────
    with st.expander("📋 Format du fichier CSV attendu"):
        st.markdown("""
        Le fichier CSV doit contenir les colonnes suivantes :
        
        | Colonne | Type | Description |
        |---|---|---|
        | `RevolvingUtilizationOfUnsecuredLines` | float (0-1) | Utilisation crédit |
        | `age` | int | Age du client |
        | `NumberOfTime30_59DaysPastDueNotWorse` | int | Retards 30-59j |
        | `DebtRatio` | float (0-1) | Ratio dette/revenu |
        | `MonthlyIncome` | float | Revenu mensuel $ |
        | `NumberOfOpenCreditLinesAndLoans` | int | Lignes de crédit |
        | `NumberOfTimes90DaysLate` | int | Retards 90j+ |
        | `NumberRealEstateLoansOrLines` | int | Prêts immobiliers |
        | `NumberOfTime60_89DaysPastDueNotWorse` | int | Retards 60-89j |
        | `NumberOfDependents` | int | Personnes à charge |
        """)
        
        # Exemple téléchargeable
        sample = pd.DataFrame([
            {
                'RevolvingUtilizationOfUnsecuredLines' : 0.35,
                'age'                                  : 45,
                'NumberOfTime30_59DaysPastDueNotWorse' : 0,
                'DebtRatio'                            : 0.40,
                'MonthlyIncome'                        : 6500,
                'NumberOfOpenCreditLinesAndLoans'      : 8,
                'NumberOfTimes90DaysLate'              : 0,
                'NumberRealEstateLoansOrLines'         : 1,
                'NumberOfTime60_89DaysPastDueNotWorse' : 0,
                'NumberOfDependents'                   : 2
            },
            {
                'RevolvingUtilizationOfUnsecuredLines' : 0.95,
                'age'                                  : 23,
                'NumberOfTime30_59DaysPastDueNotWorse' : 3,
                'DebtRatio'                            : 0.90,
                'MonthlyIncome'                        : 1800,
                'NumberOfOpenCreditLinesAndLoans'      : 12,
                'NumberOfTimes90DaysLate'              : 2,
                'NumberRealEstateLoansOrLines'         : 0,
                'NumberOfTime60_89DaysPastDueNotWorse' : 2,
                'NumberOfDependents'                   : 3
            }
        ])
        
        st.download_button(
            label     = "📥 Télécharger un exemple CSV",
            data      = sample.to_csv(index=False),
            file_name = "exemple_portefeuille.csv",
            mime      = "text/csv"
        )
    
    st.markdown("---")
    
    # ── Upload fichier ─────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader("📂 Uploadez votre portefeuille CSV", 
                                      type=['csv'])
    
    if uploaded_file is not None:
        
        df = pd.read_csv(uploaded_file)
        
        st.markdown(f"✅ **{len(df):,} clients chargés**")
        st.dataframe(df.head(5), use_container_width=True)
        
        if st.button("🚀 Scorer le portefeuille", use_container_width=True):
            
            with st.spinner(f"Scoring de {len(df):,} clients en cours..."):
                
                # Préparer le payload
                clients = df.to_dict(orient='records')
                
                # Scorer par batch de 1000
                all_results = []
                progress    = st.progress(0)
                
                for i in range(0, len(clients), 1000):
                    batch   = clients[i:i+1000]
                    payload = [
                        {
                            "RevolvingUtilizationOfUnsecuredLines" : min(float(c.get('RevolvingUtilizationOfUnsecuredLines', 0)), 1),
                            "age"                                  : max(int(c.get('age', 30)), 18),
                            "NumberOfTime30_59DaysPastDueNotWorse" : int(c.get('NumberOfTime30_59DaysPastDueNotWorse', 0)),
                            "DebtRatio"                            : min(float(c.get('DebtRatio', 0)), 1),
                            "MonthlyIncome"                        : float(c.get('MonthlyIncome', 5000)),
                            "NumberOfOpenCreditLinesAndLoans"      : int(c.get('NumberOfOpenCreditLinesAndLoans', 0)),
                            "NumberOfTimes90DaysLate"              : int(c.get('NumberOfTimes90DaysLate', 0)),
                            "NumberRealEstateLoansOrLines"         : int(c.get('NumberRealEstateLoansOrLines', 0)),
                            "NumberOfTime60_89DaysPastDueNotWorse" : int(c.get('NumberOfTime60_89DaysPastDueNotWorse', 0)),
                            "NumberOfDependents"                   : int(c.get('NumberOfDependents', 0))
                        }
                        for c in batch
                    ]
                    
                    response = requests.post(f"{API_URL}/predict/batch", json=payload)
                    
                    if response.status_code == 200:
                        all_results.append(response.json())
                    
                    progress.progress(min((i + 1000) / len(clients), 1.0))
                
                progress.empty()
            
            if all_results:
                
                # Agréger les résultats
                total_clients = sum(r['nombre_clients']    for r in all_results)
                pd_moyenne    = sum(r['PD_moyenne'] * r['nombre_clients'] 
                                    for r in all_results) / total_clients
                ecl_total     = sum(r['ECL_total_estime']  for r in all_results)
                
                distribution = {}
                for r in all_results:
                    for niveau, count in r['distribution_risque'].items():
                        distribution[niveau] = distribution.get(niveau, 0) + count
                
                st.markdown("---")
                st.markdown("### 📊 Résultats du portefeuille")
                
                # ── KPIs ──────────────────────────────────────────────────────
                col1, col2, col3 = st.columns(3)
                col1.metric("Clients scorés",  f"{total_clients:,}")
                col2.metric("PD moyenne",       f"{pd_moyenne*100:.2f}%")
                col3.metric("ECL total estimé", f"${ecl_total:,.0f}")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                # ── Distribution des risques ───────────────────────────────────
                with col1:
                    st.markdown("#### Distribution des niveaux de risque")
                    fig_pie = px.pie(
                        values = list(distribution.values()),
                        names  = list(distribution.keys()),
                        color  = list(distribution.keys()),
                        color_discrete_map = {
                            'Très faible' : '#27ae60',
                            'Faible'      : '#2ecc71',
                            'Modéré'      : '#f39c12',
                            'Élevé'       : '#e67e22',
                            'Très élevé'  : '#e74c3c'
                        }
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # ── Tableau distribution ───────────────────────────────────────
                with col2:
                    st.markdown("#### Détail par niveau de risque")
                    dist_df = pd.DataFrame({
                        'Niveau'     : list(distribution.keys()),
                        'Clients'    : list(distribution.values()),
                        'Pourcentage': [f"{v/total_clients*100:.1f}%" 
                                       for v in distribution.values()]
                    })
                    st.dataframe(dist_df, use_container_width=True, hide_index=True)
                
                # ── Export résultats ───────────────────────────────────────────
                st.markdown("---")
                st.markdown("#### 📥 Export des résultats")
                
                summary = pd.DataFrame({
                    'Métrique' : ['Clients scorés', 'PD moyenne', 'ECL total estimé'],
                    'Valeur'   : [total_clients, f"{pd_moyenne*100:.2f}%", 
                                  f"${ecl_total:,.0f}"]
                })
                
                st.download_button(
                    label     = "📥 Télécharger le résumé",
                    data      = summary.to_csv(index=False),
                    file_name = "resultats_portefeuille.csv",
                    mime      = "text/csv"
                )