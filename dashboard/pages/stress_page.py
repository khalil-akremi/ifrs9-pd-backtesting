# dashboard/pages/stress_page.py

import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

API_URL = "http://127.0.0.1:8000"

def show():
    
    st.markdown("## ⚡ Stress Testing IFRS 9")
    st.markdown("""
    Le stress testing simule l'impact de **scénarios macroéconomiques défavorables** 
    sur la PD et l'ECL d'un client — exigence réglementaire IFRS 9 forward-looking.
    """)
    
    # ── Description des scénarios ──────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background:#e8f5e9; padding:15px; border-radius:10px; 
                    border-left:5px solid #27ae60'>
        <h4>✅ Baseline</h4>
        <p>Conditions économiques normales</p>
        <ul>
        <li>PD × 1.0</li>
        <li>Revenus : 0%</li>
        <li>Crédit : +0%</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background:#fff3e0; padding:15px; border-radius:10px;
                    border-left:5px solid #f39c12'>
        <h4>⚠️ Adverse</h4>
        <p>Récession modérée</p>
        <ul>
        <li>PD × 1.5</li>
        <li>Revenus : -20%</li>
        <li>Crédit : +15%</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background:#ffebee; padding:15px; border-radius:10px;
                    border-left:5px solid #e74c3c'>
        <h4>❌ Severely Adverse</h4>
        <p>Crise financière</p>
        <ul>
        <li>PD × 2.5</li>
        <li>Revenus : -40%</li>
        <li>Crédit : +30%</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── Formulaire ─────────────────────────────────────────────────────────────
    with st.form("stress_form"):
        
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
        
        submitted = st.form_submit_button("⚡ Lancer le Stress Test",
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
        
        with st.spinner("Application des scénarios de stress..."):
            response = requests.post(f"{API_URL}/stress-test", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            st.markdown("---")
            st.markdown("### 📊 Résultats du Stress Test")
            
            # ── KPIs par scénario ──────────────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            
            scenario_colors = {
                'Baseline'         : '#27ae60',
                'Adverse'          : '#f39c12',
                'Severely Adverse' : '#e74c3c'
            }
            
            for col, (scenario, data) in zip(
                [col1, col2, col3], result.items()
            ):
                with col:
                    delta_str = f"+{data['delta_vs_baseline']:.1f}%" \
                                if data['delta_vs_baseline'] > 0 \
                                else f"{data['delta_vs_baseline']:.1f}%"
                    
                    st.markdown(f"#### {scenario}")
                    st.metric("PD",  f"{data['pd']*100:.2f}%")
                    st.metric("ECL", f"${data['ecl']:,.2f}",
                              delta=delta_str if scenario != 'Baseline' else None)
                    st.metric("EAD", f"${data['ead']:,.2f}")
            
            st.markdown("---")
            
            # ── Graphique ECL par scénario ─────────────────────────────────────
            st.markdown("### 📈 Impact sur l'ECL")
            
            scenarios  = list(result.keys())
            ecl_values = [result[s]['ecl'] for s in scenarios]
            pd_values  = [result[s]['pd'] * 100 for s in scenarios]
            colors     = [scenario_colors[s] for s in scenarios]
            
            fig = go.Figure()
            
            # Barres ECL
            fig.add_trace(go.Bar(
                name         = 'ECL ($)',
                x            = scenarios,
                y            = ecl_values,
                marker_color = colors,
                opacity      = 0.8,
                text         = [f"${v:,.0f}" for v in ecl_values],
                textposition = 'outside',
                yaxis        = 'y'
            ))
            
            # Ligne PD
            fig.add_trace(go.Scatter(
                name      = 'PD (%)',
                x         = scenarios,
                y         = pd_values,
                mode      = 'lines+markers+text',
                line      = dict(color='navy', width=2),
                marker    = dict(size=10),
                text      = [f"{v:.1f}%" for v in pd_values],
                textposition = 'top center',
                yaxis     = 'y2'
            ))
            
            fig.update_layout(
                title    = 'Impact des scénarios sur ECL et PD',
                yaxis    = dict(title='ECL ($)', side='left'),
                yaxis2   = dict(title='PD (%)', side='right', 
                               overlaying='y', range=[0, 110]),
                height   = 450,
                barmode  = 'group',
                legend   = dict(x=0.7, y=0.9)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ── Tableau comparatif ─────────────────────────────────────────────
            st.markdown("### 📋 Tableau comparatif")
            
            baseline_ecl = result['Baseline']['ecl']
            
            df_stress = pd.DataFrame([
                {
                    'Scénario'         : scenario,
                    'PD'               : f"{data['pd']*100:.2f}%",
                    'EAD'              : f"${data['ead']:,.2f}",
                    'ECL'              : f"${data['ecl']:,.2f}",
                    'Delta vs Baseline': f"+{data['delta_vs_baseline']:.1f}%" 
                                         if data['delta_vs_baseline'] > 0 
                                         else f"{data['delta_vs_baseline']:.1f}%",
                    'ECL Additionnel'  : f"${data['ecl'] - baseline_ecl:,.2f}"
                }
                for scenario, data in result.items()
            ])
            
            st.dataframe(df_stress, use_container_width=True, hide_index=True)
            
            # ── Provision forward-looking ──────────────────────────────────────
            st.markdown("### 💡 Provision Forward-Looking IFRS 9")
            
            # Pondération des scénarios (BCE standard)
            w_baseline = 0.50
            w_adverse  = 0.35
            w_severe   = 0.15
            
            ecl_weighted = (
                w_baseline * result['Baseline']['ecl'] +
                w_adverse  * result['Adverse']['ecl'] +
                w_severe   * result['Severely Adverse']['ecl']
            )
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ECL Baseline (50%)", 
                        f"${result['Baseline']['ecl']*w_baseline:,.2f}")
            col2.metric("ECL Adverse (35%)", 
                        f"${result['Adverse']['ecl']*w_adverse:,.2f}")
            col3.metric("ECL Sévère (15%)", 
                        f"${result['Severely Adverse']['ecl']*w_severe:,.2f}")
            col4.metric("ECL Forward-Looking Total", 
                        f"${ecl_weighted:,.2f}",
                        delta=f"+{((ecl_weighted/result['Baseline']['ecl'])-1)*100:.1f}% vs Baseline")
            
            st.info(f"""
            💡 **Provision Forward-Looking IFRS 9**
            
            En pondérant les 3 scénarios selon les probabilités BCE 
            (50% Baseline / 35% Adverse / 15% Severely Adverse) :
            
            **ECL Forward-Looking = ${ecl_weighted:,.2f}**
            
            vs ECL Baseline = ${result['Baseline']['ecl']:,.2f}
            
            La provision forward-looking est supérieure de 
            **${ecl_weighted - result['Baseline']['ecl']:,.2f}** 
            par rapport au scénario de base.
            """)
        
        else:
            st.error(f"Erreur API : {response.status_code}")