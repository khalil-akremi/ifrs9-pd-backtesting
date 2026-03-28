# api/predict.py

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# ── Chargement des modèles ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent / 'models'

calibrated_lr  = joblib.load(BASE_DIR / 'calibrated_lr.pkl')
calibrated_woe = joblib.load(BASE_DIR / 'calibrated_woe.pkl')
calibrated_xgb = joblib.load(BASE_DIR / 'calibrated_xgb.pkl')
scaler         = joblib.load(BASE_DIR / 'scaler.pkl')
woe_maps       = joblib.load(BASE_DIR / 'woe_maps.pkl')
woe_configs    = joblib.load(BASE_DIR / 'woe_configs.pkl')
metrics        = joblib.load(BASE_DIR / 'metrics.pkl')

# ── Colonnes dans le bon ordre ─────────────────────────────────────────────────
FEATURE_COLS = [
    'RevolvingUtilizationOfUnsecuredLines',
    'age',
    'NumberOfTime30-59DaysPastDueNotWorse',
    'DebtRatio',
    'MonthlyIncome',
    'NumberOfOpenCreditLinesAndLoans',
    'NumberOfTimes90DaysLate',
    'NumberRealEstateLoansOrLines',
    'NumberOfTime60-89DaysPastDueNotWorse',
    'NumberOfDependents',
    'MonthlyIncome_missing'
]


def prepare_features(client: dict) -> pd.DataFrame:
    """Prépare les features d'un client pour la prédiction"""
    
    # Renommer les colonnes (Pydantic utilise _ au lieu de -)
    df = pd.DataFrame([{
        'RevolvingUtilizationOfUnsecuredLines' : client['RevolvingUtilizationOfUnsecuredLines'],
        'age'                                  : client['age'],
        'NumberOfTime30-59DaysPastDueNotWorse' : client['NumberOfTime30_59DaysPastDueNotWorse'],
        'DebtRatio'                            : client['DebtRatio'],
        'MonthlyIncome'                        : client['MonthlyIncome'],
        'NumberOfOpenCreditLinesAndLoans'      : client['NumberOfOpenCreditLinesAndLoans'],
        'NumberOfTimes90DaysLate'              : client['NumberOfTimes90DaysLate'],
        'NumberRealEstateLoansOrLines'         : client['NumberRealEstateLoansOrLines'],
        'NumberOfTime60-89DaysPastDueNotWorse' : client['NumberOfTime60_89DaysPastDueNotWorse'],
        'NumberOfDependents'                   : client['NumberOfDependents'],
        'MonthlyIncome_missing'                : 0
    }])
    
    return df


def apply_woe_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Applique la transformation WoE sur un client"""
    
    df_woe = pd.DataFrame(index=df.index)
    
    pastdue_bins   = [-1, 0, 1, 2, float('inf')]
    pastdue_labels = ['0 retards', '1 retard', '2 retards', '3+ retards']
    
    for feature, config in woe_configs.items():
        if config.get('manual_bins') is not None:
            buckets = pd.cut(df[feature],
                            bins=pastdue_bins,
                            labels=pastdue_labels)
        else:
            import numpy as np
            _, bin_edges = pd.qcut(df[feature], q=config['bins'],
                                   duplicates='drop', retbins=True)
            bin_edges[0]  = -np.inf
            bin_edges[-1] =  np.inf
            buckets = pd.cut(df[feature], bins=bin_edges)
        
        df_woe[feature] = buckets.map(woe_maps[feature])
    
    return df_woe.astype(float).fillna(0)


def get_risk_level(pd_mean: float) -> str:
    """Détermine le niveau de risque selon la PD moyenne"""
    if pd_mean < 0.02:
        return "Très faible"
    elif pd_mean < 0.05:
        return "Faible"
    elif pd_mean < 0.10:
        return "Modéré"
    elif pd_mean < 0.20:
        return "Élevé"
    else:
        return "Très élevé"


def get_interpretation(df: pd.DataFrame, pd_mean: float) -> dict:
    """Génère une interprétation des facteurs de risque"""
    
    interpretation = {}
    
    revolving = df['RevolvingUtilizationOfUnsecuredLines'].values[0]
    if revolving > 0.75:
        interpretation['RevolvingUtilization'] = "⚠️ Utilisation élevée du crédit — facteur de risque majeur"
    elif revolving > 0.40:
        interpretation['RevolvingUtilization'] = "⚠️ Utilisation modérée du crédit"
    else:
        interpretation['RevolvingUtilization'] = "✅ Utilisation faible du crédit"
    
    age = df['age'].values[0]
    if age < 30:
        interpretation['age'] = "⚠️ Client jeune — risque statistiquement plus élevé"
    elif age > 55:
        interpretation['age'] = "✅ Client senior — risque statistiquement plus faible"
    else:
        interpretation['age'] = "✅ Tranche d'âge neutre"
    
    retards = df['NumberOfTime30-59DaysPastDueNotWorse'].values[0]
    if retards > 2:
        interpretation['retards'] = f"❌ {retards} retards détectés — signal de détresse financière"
    elif retards > 0:
        interpretation['retards'] = f"⚠️ {retards} retard(s) détecté(s)"
    else:
        interpretation['retards'] = "✅ Aucun retard de paiement"
    
    income = df['MonthlyIncome'].values[0]
    if income < 3000:
        interpretation['revenu'] = "⚠️ Revenu mensuel faible"
    elif income > 8000:
        interpretation['revenu'] = "✅ Revenu mensuel élevé — facteur protecteur"
    else:
        interpretation['revenu'] = "✅ Revenu mensuel correct"
    
    return interpretation


def predict_single(client: dict) -> dict:
    """Prédit la PD pour un seul client"""
    
    # Préparer les features
    df = prepare_features(client)
    
    # Standardiser pour LR et XGBoost
    df_scaled = scaler.transform(df[FEATURE_COLS])
    
    # Transformer en WoE pour Scorecard
    df_woe = apply_woe_transform(df)
    
    # Prédictions
    pd_lr  = float(calibrated_lr.predict_proba(df_scaled)[:, 1][0])
    pd_woe = float(calibrated_woe.predict_proba(df_woe)[:, 1][0])
    pd_xgb = float(calibrated_xgb.predict_proba(df_scaled)[:, 1][0])
    pd_mean = round((pd_lr + pd_woe + pd_xgb) / 3, 4)
    
    # ECL estimé (LGD supposé = 0.45, EAD = MonthlyIncome * 12)
    lgd = 0.45
    ead = client['MonthlyIncome'] * 12
    ecl = round(pd_mean * lgd * ead, 2)
    
    return {
        'PD_logistic'   : round(pd_lr, 4),
        'PD_scorecard'  : round(pd_woe, 4),
        'PD_xgboost'    : round(pd_xgb, 4),
        'PD_moyenne'    : pd_mean,
        'niveau_risque' : get_risk_level(pd_mean),
        'ECL_estime'    : ecl,
        'interpretation': get_interpretation(df, pd_mean)
    }


def get_metrics() -> dict:
    """Retourne les métriques de backtesting"""
    return metrics