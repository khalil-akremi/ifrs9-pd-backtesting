# api/predict.py
import numpy as np
import joblib
import pandas as pd
from pathlib import Path
import shap

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


def _extract_class1_value(value) -> float:
    """Normalise les sorties SHAP (scalaire, liste, ndarray) vers la classe positive."""
    if isinstance(value, str):
        return float(value.strip("[]"))

    arr = np.asarray(value)
    if arr.dtype.kind in {"U", "S", "O"}:
        return float(str(arr.reshape(-1)[-1]).strip("[]"))

    if arr.ndim == 0:
        return float(arr)
    return float(arr.reshape(-1)[-1])


def _extract_shap_vector(shap_raw) -> np.ndarray:
    """Convertit les sorties SHAP multi-format vers un vecteur 1D de contributions."""
    if isinstance(shap_raw, list):
        arr = np.asarray(shap_raw[-1])
    else:
        arr = np.asarray(shap_raw)

    if arr.ndim == 1:
        return arr
    if arr.ndim == 2:
        return arr[0]
    if arr.ndim == 3:
        return arr[0, :, -1]

    return arr.reshape(-1)


# ── Chargement SHAP ────────────────────────────────────────────────────────────
# L'explainer est initialisé à la demande pour éviter un crash au démarrage API.
xgb_model = calibrated_xgb.calibrated_classifiers_[0].estimator
feature_names = joblib.load(BASE_DIR / 'feature_names.pkl')
shap_explainer = None


def _get_shap_explainer():
    """Construit un explainer SHAP avec fallback si TreeExplainer est incompatible."""
    global shap_explainer
    if shap_explainer is None:
        try:
            shap_explainer = shap.TreeExplainer(xgb_model)
        except Exception:
            # Fallback robuste: KernelExplainer basé sur la proba calibrée.
            background = np.zeros((25, len(FEATURE_COLS)))
            shap_explainer = shap.KernelExplainer(calibrated_xgb.predict_proba, background)
    return shap_explainer

# ── SHAP pour un client ────────────────────────────────────────────────────────
def explain_client(client: dict) -> dict:
    """Calcule les valeurs SHAP pour un client"""
    
    df        = prepare_features(client)
    df_scaled = scaler.transform(df[FEATURE_COLS])
    
    explainer = _get_shap_explainer()

    # Valeurs SHAP (format robuste selon les versions SHAP)
    if explainer.__class__.__name__ == 'KernelExplainer':
        shap_raw = explainer.shap_values(df_scaled, nsamples=100)
    else:
        shap_raw = explainer.shap_values(df_scaled)
    shap_vals = _extract_shap_vector(shap_raw)
    
    # Trier par valeur absolue décroissante
    sorted_idx = np.argsort(np.abs(shap_vals))[::-1]
    
    contributions = {}
    for idx in sorted_idx:
        contributions[feature_names[idx]] = {
            'shap_value'   : round(float(shap_vals[idx]), 4),
            'feature_value': round(float(df_scaled[0][idx]), 4),
            'direction'    : 'augmente le risque' if shap_vals[idx] > 0 else 'diminue le risque'
        }
    
    # PD de base
    base_value = _extract_class1_value(explainer.expected_value)
    pd_client  = float(calibrated_xgb.predict_proba(df_scaled)[:, 1][0])
    
    return {
        'base_value'    : round(base_value, 4),
        'pd_predicted'  : round(pd_client, 4),
        'contributions' : contributions,
        'top_risk_factor': feature_names[sorted_idx[0]]
    }


# ── Monte Carlo ECL ────────────────────────────────────────────────────────────
def monte_carlo_client(client: dict, n_sim: int = 10000) -> dict:
    """Simule la distribution ECL pour un client"""
    
    pd_mean       = predict_single(client)['PD_moyenne']
    monthly_income = client['MonthlyIncome']
    
    # Clip pour éviter les erreurs numériques
    pd_mean        = np.clip(pd_mean, 0.001, 0.999)
    monthly_income = max(monthly_income, 500)
    
    # ── PD ~ Beta ──────────────────────────────────────────────────────────────
    pd_std   = pd_mean * (1 - pd_mean) * 0.3
    alpha_pd = max(pd_mean * ((pd_mean*(1-pd_mean)/pd_std**2) - 1), 0.1)
    beta_pd  = max((1-pd_mean) * ((pd_mean*(1-pd_mean)/pd_std**2) - 1), 0.1)
    pd_sim   = np.random.beta(alpha_pd, beta_pd, n_sim)
    
    # ── LGD ~ Beta ─────────────────────────────────────────────────────────────
    lgd_sim = np.random.beta(2, 3, n_sim)
    
    # ── EAD ~ LogNormal ────────────────────────────────────────────────────────
    ead_mean = monthly_income * 12
    ead_std  = ead_mean * 0.2
    mu_ln    = np.log(ead_mean**2 / np.sqrt(ead_std**2 + ead_mean**2))
    sig_ln   = np.sqrt(np.log(1 + (ead_std/ead_mean)**2))
    ead_sim  = np.random.lognormal(mu_ln, sig_ln, n_sim)
    
    # ── ECL simulé ─────────────────────────────────────────────────────────────
    ecl_sim = pd_sim * lgd_sim * ead_sim
    ecl_sim = ecl_sim[~np.isnan(ecl_sim)]
    
    return {
        'n_simulations'    : n_sim,
        'ecl_mean'         : round(float(np.mean(ecl_sim)), 2),
        'ecl_median'       : round(float(np.median(ecl_sim)), 2),
        'ecl_std'          : round(float(np.std(ecl_sim)), 2),
        'ecl_var_95'       : round(float(np.percentile(ecl_sim, 95)), 2),
        'ecl_var_99'       : round(float(np.percentile(ecl_sim, 99)), 2),
        'ecl_es_95'        : round(float(np.mean(ecl_sim[ecl_sim >= np.percentile(ecl_sim, 95)])), 2),
        'ecl_deterministic': round(float(predict_single(client)['ECL_estime']), 2),
        'ecl_distribution' : ecl_sim[:1000].tolist()  # 1000 points pour la visualisation
    }


# ── Stress Testing ─────────────────────────────────────────────────────────────
def stress_test_client(client: dict) -> dict:
    """Applique les 3 scénarios de stress sur un client"""
    
    scenarios = {
        'Baseline' : {
            'pd_multiplier'    : 1.0,
            'income_shock'     : 0.0,
            'revolving_shock'  : 0.0,
            'debt_ratio_shock' : 0.0
        },
        'Adverse' : {
            'pd_multiplier'    : 1.5,
            'income_shock'     : -0.20,
            'revolving_shock'  : +0.15,
            'debt_ratio_shock' : +0.10
        },
        'Severely Adverse' : {
            'pd_multiplier'    : 2.5,
            'income_shock'     : -0.40,
            'revolving_shock'  : +0.30,
            'debt_ratio_shock' : +0.20
        }
    }
    
    results = {}
    baseline_ecl = None
    
    for scenario_name, params in scenarios.items():
        
        # Appliquer les chocs sur le client
        client_stressed = client.copy()
        client_stressed['MonthlyIncome'] = max(
            client['MonthlyIncome'] * (1 + params['income_shock']), 100)
        client_stressed['RevolvingUtilizationOfUnsecuredLines'] = min(
            client['RevolvingUtilizationOfUnsecuredLines'] + params['revolving_shock'], 1.0)
        client_stressed['DebtRatio'] = min(
            client['DebtRatio'] + params['debt_ratio_shock'], 1.0)
        
        # Prédiction stressée
        pred     = predict_single(client_stressed)
        pd_stress = min(pred['PD_moyenne'] * params['pd_multiplier'], 0.999)
        
        # ECL stressé
        lgd = 0.45
        ead = client_stressed['MonthlyIncome'] * 12
        ecl = pd_stress * lgd * ead
        
        results[scenario_name] = {
            'pd'  : round(pd_stress, 4),
            'ecl' : round(ecl, 2),
            'ead' : round(ead, 2)
        }
        
        if scenario_name == 'Baseline':
            baseline_ecl = ecl
    
    # Calcul des deltas vs baseline
    for scenario_name in results:
        delta = ((results[scenario_name]['ecl'] - baseline_ecl) / baseline_ecl * 100)
        results[scenario_name]['delta_vs_baseline'] = round(delta, 2)
    
    return results