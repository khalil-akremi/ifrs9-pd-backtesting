# api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from schemas import ClientFeatures, PredictionResponse, PortfolioResponse
from predict import predict_single, get_metrics

# ── Initialisation ─────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "IFRS 9 — PD Backtesting API",
    description = """
    API de prédiction de la Probabilité de Défaut (PD) selon IFRS 9.
    
    ## Modèles disponibles
    - **Régression Logistique** — modèle de référence IFRS 9
    - **Scorecard WoE/IV** — standard bancaire
    - **XGBoost** — meilleure performance
    
    ## Endpoints
    - **/predict** — prédiction pour un client
    - **/predict/batch** — prédiction pour un portefeuille
    - **/metrics** — métriques de backtesting
    - **/health** — statut de l'API
    """,
    version     = "1.0.0",
    contact     = {
        "name"  : "Khalil Akremi",
        "email" : "khalil.akremi@essai.ucar.tn"
    }
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Vérifie que l'API est opérationnelle"""
    return {
        "status"  : "✅ API opérationnelle",
        "version" : "1.0.0",
        "modeles" : ["Régression LR", "Scorecard WoE", "XGBoost"]
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(client: ClientFeatures):
    """
    Prédit la PD pour un client unique.
    
    Retourne :
    - PD selon les 3 modèles
    - Niveau de risque
    - ECL estimé
    - Interprétation des facteurs de risque
    """
    try:
        result = predict_single(client.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=PortfolioResponse)
def predict_batch(clients: list[ClientFeatures]):
    """
    Prédit la PD pour un portefeuille de clients.
    
    Retourne :
    - Nombre de clients
    - PD moyenne du portefeuille
    - ECL total estimé
    - Distribution par niveau de risque
    """
    try:
        if len(clients) == 0:
            raise HTTPException(status_code=400, detail="Liste de clients vide")
        
        if len(clients) > 10000:
            raise HTTPException(status_code=400, detail="Maximum 10,000 clients par requête")
        
        results = [predict_single(c.model_dump()) for c in clients]
        
        pd_moyenne  = round(sum(r['PD_moyenne'] for r in results) / len(results), 4)
        ecl_total   = round(sum(r['ECL_estime'] for r in results), 2)
        
        distribution = {
            "Très faible" : sum(1 for r in results if r['niveau_risque'] == "Très faible"),
            "Faible"      : sum(1 for r in results if r['niveau_risque'] == "Faible"),
            "Modéré"      : sum(1 for r in results if r['niveau_risque'] == "Modéré"),
            "Élevé"       : sum(1 for r in results if r['niveau_risque'] == "Élevé"),
            "Très élevé"  : sum(1 for r in results if r['niveau_risque'] == "Très élevé"),
        }
        
        return {
            "nombre_clients"      : len(results),
            "PD_moyenne"          : pd_moyenne,
            "ECL_total_estime"    : ecl_total,
            "distribution_risque" : distribution
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def backtesting_metrics():
    """
    Retourne les métriques de backtesting IFRS 9.
    
    Inclut :
    - Métriques de discrimination (AUC, Gini, KS)
    - Métriques de calibration (Brier Score)
    - Métriques de stabilité (PSI)
    """
    try:
        return get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))