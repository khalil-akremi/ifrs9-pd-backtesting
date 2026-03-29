# api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import ClientFeatures, PredictionResponse, PortfolioResponse
from predict import predict_single, get_metrics, explain_client, monte_carlo_client, stress_test_client

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
    - **/shap** — valeurs SHAP pour un client
    - **/monte-carlo** — simulation ECL Monte Carlo
    - **/stress-test** — stress testing IFRS 9
    - **/metrics** — métriques de backtesting
    - **/health** — statut de l'API
    """,
    version     = "2.0.0",
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
    return {
        "status"  : "✅ API opérationnelle",
        "version" : "2.0.0",
        "modeles" : ["Régression LR", "Scorecard WoE", "XGBoost"],
        "endpoints": ["/predict", "/predict/batch", "/shap", 
                      "/monte-carlo", "/stress-test", "/metrics"]
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(client: ClientFeatures):
    """Prédit la PD pour un client unique"""
    try:
        return predict_single(client.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=PortfolioResponse)
def predict_batch(clients: list[ClientFeatures]):
    """Prédit la PD pour un portefeuille de clients"""
    try:
        if len(clients) == 0:
            raise HTTPException(status_code=400, detail="Liste de clients vide")
        if len(clients) > 10000:
            raise HTTPException(status_code=400, detail="Maximum 10,000 clients")
        
        results      = [predict_single(c.model_dump()) for c in clients]
        pd_moyenne   = round(sum(r['PD_moyenne'] for r in results) / len(results), 4)
        ecl_total    = round(sum(r['ECL_estime'] for r in results), 2)
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
    """Retourne les métriques de backtesting IFRS 9"""
    try:
        return get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shap")
def shap_explanation(client: ClientFeatures):
    """
    Calcule les valeurs SHAP pour un client.
    Retourne la contribution de chaque feature à la PD.
    """
    try:
        return explain_client(client.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monte-carlo")
def monte_carlo(client: ClientFeatures, n_sim: int = 10000):
    """
    Simule la distribution ECL — 10,000 scénarios par défaut.
    Retourne VaR 95%, VaR 99%, Expected Shortfall.
    """
    try:
        if n_sim > 50000:
            raise HTTPException(status_code=400, detail="Maximum 50,000 simulations")
        return monte_carlo_client(client.model_dump(), n_sim)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stress-test")
def stress_testing(client: ClientFeatures):
    """
    Applique 3 scénarios de stress IFRS 9 :
    Baseline / Adverse (PD x1.5) / Severely Adverse (PD x2.5)
    """
    try:
        return stress_test_client(client.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))