# api/schemas.py

from pydantic import BaseModel, Field
from typing import Optional

class ClientFeatures(BaseModel):
    """Caractéristiques d'un client pour la prédiction PD"""
    
    RevolvingUtilizationOfUnsecuredLines : float = Field(..., ge=0, le=1,
        description="Utilisation du crédit renouvelable (0-1)")
    age                                  : int   = Field(..., ge=18, le=110,
        description="Age du client")
    NumberOfTime30_59DaysPastDueNotWorse : int   = Field(..., ge=0,
        description="Nombre de retards 30-59 jours")
    DebtRatio                            : float = Field(..., ge=0, le=1,
        description="Ratio dette/revenu (0-1)")
    MonthlyIncome                        : float = Field(..., ge=0,
        description="Revenu mensuel en $")
    NumberOfOpenCreditLinesAndLoans      : int   = Field(..., ge=0,
        description="Nombre de lignes de crédit ouvertes")
    NumberOfTimes90DaysLate              : int   = Field(..., ge=0,
        description="Nombre de retards > 90 jours")
    NumberRealEstateLoansOrLines         : int   = Field(..., ge=0,
        description="Nombre de prêts immobiliers")
    NumberOfTime60_89DaysPastDueNotWorse : int   = Field(..., ge=0,
        description="Nombre de retards 60-89 jours")
    NumberOfDependents                   : int   = Field(..., ge=0,
        description="Nombre de personnes à charge")

    class Config:
        json_schema_extra = {
            "example": {
                "RevolvingUtilizationOfUnsecuredLines" : 0.35,
                "age"                                  : 45,
                "NumberOfTime30_59DaysPastDueNotWorse" : 0,
                "DebtRatio"                            : 0.40,
                "MonthlyIncome"                        : 6500,
                "NumberOfOpenCreditLinesAndLoans"      : 8,
                "NumberOfTimes90DaysLate"              : 0,
                "NumberRealEstateLoansOrLines"         : 1,
                "NumberOfTime60_89DaysPastDueNotWorse" : 0,
                "NumberOfDependents"                   : 2
            }
        }


class PredictionResponse(BaseModel):
    """Résultat de la prédiction PD"""
    
    PD_logistic  : float
    PD_scorecard : float
    PD_xgboost   : float
    PD_moyenne   : float
    niveau_risque: str
    ECL_estime   : float
    interpretation: dict


class PortfolioResponse(BaseModel):
    """Résultat pour un portefeuille de clients"""
    
    nombre_clients   : int
    PD_moyenne       : float
    ECL_total_estime : float
    distribution_risque : dict