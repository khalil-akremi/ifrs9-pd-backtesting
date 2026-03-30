# dashboard/pages/report.py

import streamlit as st
import requests
from fpdf import FPDF
import tempfile
from datetime import datetime

# Nouvelle ligne — dans chaque page
from config import API_URL

# ── Classe PDF personnalisée ───────────────────────────────────────────────────
class IFRS9Report(FPDF):
    
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(31, 78, 121)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'IFRS 9 - Model Validation Report', 
                  ln=True, fill=True, align='C')
        self.set_text_color(0, 0, 0)
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Khalil Akremi - ESSAI 2026', 
                  align='C')
    
    def title_page(self):
        self.add_page()
        self.ln(30)
        self.set_font('Arial', 'B', 28)
        self.set_text_color(31, 78, 121)
        self.cell(0, 15, 'IFRS 9', ln=True, align='C')
        self.cell(0, 15, 'Model Validation Report', ln=True, align='C')
        self.ln(10)
        self.set_font('Arial', '', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Probability of Default (PD) Backtesting', 
                  ln=True, align='C')
        self.ln(5)
        self.cell(0, 10, 'Dataset : Give Me Some Credit - Kaggle', 
                  ln=True, align='C')
        self.ln(20)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'Date : {datetime.now().strftime("%B %Y")}', 
                  ln=True, align='C')
        self.cell(0, 10, 'Auteur : Khalil Akremi', ln=True, align='C')
        self.cell(0, 10, 'Institution : ESSAI - Tunis', ln=True, align='C')
    
    def section_title(self, title):
        self.ln(5)
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(31, 78, 121)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(3)
    
    def body_text(self, text):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 7, text)
        self.ln(3)
    
    def metrics_table(self, headers, rows):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(200, 220, 240)
        col_width = 190 / len(headers)
        
        for h in headers:
            self.cell(col_width, 8, h, border=1, fill=True, align='C')
        self.ln()
        
        self.set_font('Arial', '', 10)
        for i, row in enumerate(rows):
            fill = i % 2 == 0
            self.set_fill_color(240, 248, 255) if fill else self.set_fill_color(255, 255, 255)
            for cell in row:
                self.cell(col_width, 8, str(cell), border=1, 
                         fill=fill, align='C')
            self.ln()
        self.ln(3)


def generate_validation_report(metrics):
    """Genere le rapport de validation complet"""
    
    pdf = IFRS9Report()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ── Page de titre ──────────────────────────────────────────────────────────
    pdf.title_page()
    
    # ── Page 2 - Resume executif ───────────────────────────────────────────────
    pdf.add_page()
    pdf.section_title("1. Resume Executif")
    pdf.body_text(
        "Ce rapport presente les resultats du backtesting IFRS 9 d'un modele "
        "de Probabilite de Defaut (PD) developpe sur le dataset Give Me Some "
        "Credit (Kaggle). Trois modeles ont ete construits et valides selon "
        "les trois dimensions du backtesting IFRS 9 : discrimination, "
        "calibration et stabilite."
    )
    pdf.body_text(
        "Les trois modeles - Regression Logistique, Scorecard WoE/IV et "
        "XGBoost - affichent des performances excellentes sur toutes les "
        "dimensions, avec des AUC superieurs a 0.84 et des Gini superieurs "
        "a 0.69. XGBoost obtient les meilleures performances globales, "
        "tandis que la Scorecard WoE/IV est recommandee pour un usage "
        "reglementaire IFRS 9 en raison de sa transparence maximale."
    )
    
    # ── Page 3 - Description des donnees ──────────────────────────────────────
    pdf.section_title("2. Description des Donnees")
    pdf.body_text("Dataset : Give Me Some Credit - Kaggle Competition")
    
    pdf.metrics_table(
        headers = ['Caracteristique', 'Valeur'],
        rows    = [
            ['Observations Train', f"{metrics['train_size']:,}"],
            ['Observations Test',  f"{metrics['val_size']:,}"],
            ['Features',           '11'],
            ['Taux de defaut',     f"{metrics['default_rate']*100:.2f}%"],
            ['Periode',            '2008-2009'],
            ['Source',             'Kaggle - Give Me Some Credit']
        ]
    )
    
    # ── Page 4 - Discrimination ────────────────────────────────────────────────
    pdf.section_title("3. Backtesting - Discrimination")
    pdf.body_text(
        "La discrimination mesure la capacite du modele a separer les bons "
        "et mauvais payeurs. Les metriques utilisees sont l'AUC-ROC, le "
        "coefficient de Gini, le test de Kolmogorov-Smirnov (KS) et "
        "l'Accuracy Ratio (AR) derive de la courbe CAP."
    )
    
    pdf.metrics_table(
        headers = ['Modele', 'AUC', 'Gini', 'KS', 'Statut'],
        rows    = [
            ['Regression LR',
             f"{metrics['discrimination']['LR']['AUC']:.4f}",
             f"{metrics['discrimination']['LR']['Gini']:.4f}",
             f"{metrics['discrimination']['LR']['KS']:.4f}",
             'Excellent'],
            ['Scorecard WoE',
             f"{metrics['discrimination']['WoE']['AUC']:.4f}",
             f"{metrics['discrimination']['WoE']['Gini']:.4f}",
             f"{metrics['discrimination']['WoE']['KS']:.4f}",
             'Excellent'],
            ['XGBoost',
             f"{metrics['discrimination']['XGB']['AUC']:.4f}",
             f"{metrics['discrimination']['XGB']['Gini']:.4f}",
             f"{metrics['discrimination']['XGB']['KS']:.4f}",
             'Excellent'],
        ]
    )
    
    pdf.body_text(
        "Seuils bancaires : AUC > 0.80, Gini > 0.60, KS > 0.40. "
        "Les trois modeles depassent largement ces seuils."
    )
    
    # ── Page 5 - Calibration ───────────────────────────────────────────────────
    pdf.section_title("4. Backtesting - Calibration")
    pdf.body_text(
        "La calibration verifie que les probabilites predites correspondent "
        "aux taux de defaut reellement observes. Un probleme de surestimation "
        "des PD a ete detecte et corrige via Platt Scaling (recalibration)."
    )
    
    pdf.metrics_table(
        headers = ['Modele', 'Brier Score', 'Statut'],
        rows    = [
            ['Regression LR',
             f"{metrics['calibration']['LR']['Brier']:.4f}",
             'Acceptable'],
            ['Scorecard WoE',
             f"{metrics['calibration']['WoE']['Brier']:.4f}",
             'Acceptable'],
            ['XGBoost',
             f"{metrics['calibration']['XGB']['Brier']:.4f}",
             'Bon'],
        ]
    )
    
    # ── Page 6 - Stabilite PSI ─────────────────────────────────────────────────
    pdf.section_title("5. Backtesting - Stabilite (PSI)")
    pdf.body_text(
        "Le Population Stability Index (PSI) mesure la stabilite de la "
        "distribution des scores entre le jeu d'entrainement et le jeu "
        "de test. Un PSI < 0.10 indique une population stable."
    )
    
    pdf.metrics_table(
        headers = ['Modele', 'PSI', 'Statut'],
        rows    = [
            ['Regression LR',
             f"{metrics['stability']['LR']['PSI']:.4f}",
             'Stable'],
            ['Scorecard WoE',
             f"{metrics['stability']['WoE']['PSI']:.4f}",
             'Stable'],
            ['XGBoost',
             f"{metrics['stability']['XGB']['PSI']:.4f}",
             'Stable'],
        ]
    )
    
    # ── Page 7 - Conclusion ────────────────────────────────────────────────────
    pdf.section_title("6. Conclusion et Recommandations")
    pdf.body_text(
        "Les trois modeles PD developpes dans ce projet ont ete valides "
        "avec succes sur les trois dimensions du backtesting IFRS 9. "
        "Les resultats sont excellents et comparables aux modeles utilises "
        "dans les institutions financieres."
    )
    pdf.body_text(
        "Recommandations :\n"
        "1. Scorecard WoE/IV - recommandee pour la validation reglementaire "
        "IFRS 9 en raison de sa transparence et auditabilite maximales.\n"
        "2. XGBoost - recommande pour le reporting interne et la surveillance "
        "du portefeuille en raison de ses meilleures performances.\n"
        "3. Recalibration - a effectuer periodiquement (tous les 6 mois) "
        "pour maintenir la qualite de la calibration dans le temps."
    )
    
    return pdf


def generate_client_report(payload, result):
    """Genere un rapport PDF d'une page pour un client"""
    
    pdf = IFRS9Report()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Titre
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 15, 'Rapport de Scoring Client', ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}", 
             ln=True, align='C')
    pdf.ln(5)
    
    # Niveau de risque
    pdf.section_title("Niveau de Risque")
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 12, f"Niveau : {result['niveau_risque']}", ln=True, align='C')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"PD Moyenne : {result['PD_moyenne']*100:.2f}%", 
             ln=True, align='C')
    pdf.cell(0, 10, f"ECL Estime : ${result['ECL_estime']:,.2f}", 
             ln=True, align='C')
    pdf.ln(5)
    
    # PD par modele
    pdf.section_title("Probabilite de Defaut par Modele")
    pdf.metrics_table(
        headers = ['Modele', 'PD', 'Interpretation'],
        rows    = [
            ['Regression LR',  f"{result['PD_logistic']*100:.2f}%",  'Modele de reference'],
            ['Scorecard WoE',  f"{result['PD_scorecard']*100:.2f}%", 'Standard bancaire'],
            ['XGBoost',        f"{result['PD_xgboost']*100:.2f}%",   'Meilleure performance'],
        ]
    )
    
    # Caracteristiques client
    pdf.section_title("Caracteristiques du Client")
    pdf.metrics_table(
        headers = ['Variable', 'Valeur'],
        rows    = [[k, str(v)] for k, v in payload.items()]
    )
    
    # Facteurs de risque
    pdf.section_title("Analyse des Facteurs de Risque")
    for key, value in result['interpretation'].items():
        clean_value = value.replace('✅', 'OK').replace('⚠️', '!').replace('❌', 'X')
        pdf.body_text(f"- {clean_value}")
    
    return pdf


def show():
    
    st.markdown("## Generation de Rapports PDF")
    st.markdown("---")
    
    tab1, tab2 = st.tabs([
        "Rapport de Validation",
        "Rapport par Client"
    ])
    
    # ── Tab 1 - Rapport de validation ─────────────────────────────────────────
    with tab1:
        
        st.markdown("### Rapport de Validation du Modele IFRS 9")
        st.markdown("""
        Ce rapport documente l'ensemble du processus de backtesting IFRS 9 :
        - Resume executif
        - Description des donnees
        - Resultats discrimination (AUC, Gini, KS)
        - Resultats calibration (Brier Score)
        - Resultats stabilite (PSI)
        - Conclusions et recommandations
        """)
        
        if st.button("Generer le Rapport de Validation", 
                     use_container_width=True):
            
            with st.spinner("Generation du rapport en cours..."):
                try:
                    metrics = requests.get(f"{API_URL}/metrics").json()
                    pdf     = generate_validation_report(metrics)
                    
                    with tempfile.NamedTemporaryFile(delete=False, 
                                                    suffix='.pdf') as f:
                        pdf.output(f.name)
                        with open(f.name, 'rb') as pdf_file:
                            pdf_bytes = pdf_file.read()
                    
                    st.success("Rapport genere avec succes !")
                    st.download_button(
                        label     = "Telecharger le Rapport de Validation",
                        data      = pdf_bytes,
                        file_name = f"IFRS9_Validation_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime      = "application/pdf"
                    )
                
                except Exception as e:
                    st.error(f"Erreur : {e}")
    
    # ── Tab 2 - Rapport par client ─────────────────────────────────────────────
    with tab2:
        
        st.markdown("### Rapport de Scoring Client")
        st.markdown("Entrez les caracteristiques d'un client pour generer son rapport PDF.")
        
        with st.form("client_report_form"):
            
            col1, col2 = st.columns(2)
            
            with col1:
                age            = st.slider("Age", 18, 110, 45)
                monthly_income = st.number_input("Revenu mensuel ($)", 0, 50000, 6500)
                debt_ratio     = st.slider("Debt Ratio", 0.0, 1.0, 0.4, 0.01)
                revolving      = st.slider("Utilisation credit", 0.0, 1.0, 0.35, 0.01)
                dependents     = st.number_input("Personnes a charge", 0, 20, 2)
            
            with col2:
                open_credits = st.number_input("Lignes de credit", 0, 60, 8)
                real_estate  = st.number_input("Prets immobiliers", 0, 54, 1)
                late_30_59   = st.number_input("Retards 30-59j", 0, 20, 0)
                late_60_89   = st.number_input("Retards 60-89j", 0, 20, 0)
                late_90      = st.number_input("Retards 90j+", 0, 20, 0)
            
            submitted = st.form_submit_button("Generer le Rapport Client",
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
            
            with st.spinner("Generation du rapport client..."):
                response = requests.post(f"{API_URL}/predict", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    pdf    = generate_client_report(payload, result)
                    
                    with tempfile.NamedTemporaryFile(delete=False, 
                                                    suffix='.pdf') as f:
                        pdf.output(f.name)
                        with open(f.name, 'rb') as pdf_file:
                            pdf_bytes = pdf_file.read()
                    
                    st.success("Rapport client genere !")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("PD Moyenne",    f"{result['PD_moyenne']*100:.2f}%")
                    col2.metric("Niveau risque",  result['niveau_risque'])
                    col3.metric("ECL Estime",    f"${result['ECL_estime']:,.2f}")
                    
                    st.download_button(
                        label     = "Telecharger le Rapport Client",
                        data      = pdf_bytes,
                        file_name = f"Client_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime      = "application/pdf"
                    )