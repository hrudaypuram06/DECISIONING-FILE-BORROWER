import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def generate_synthetic_dataset(n_samples=1000):
    np.random.seed(42)
    income = np.random.uniform(15000, 150000, n_samples)
    expenses = income * np.random.uniform(0.3, 0.8, n_samples)
    rent_ratio = np.random.uniform(0.6, 1.0, n_samples)
    utility_ratio = np.random.uniform(0.5, 1.0, n_samples)
    telecom_ratio = np.random.uniform(0.5, 1.0, n_samples)
    cash_flow_stability = np.random.uniform(0.2, 1.0, n_samples)
    gig_income = np.random.uniform(0, 30000, n_samples)
    platform_rating = np.random.uniform(3.0, 5.0, n_samples)
    
    score = (
        (income - expenses) / 10000 * 0.2 +
        rent_ratio * 2.5 +
        utility_ratio * 1.5 +
        telecom_ratio * 1.0 +
        cash_flow_stability * 2.0 +
        (gig_income / 5000) * 0.5 +
        platform_rating * 0.8
    )
    prob = 1 / (1 + np.exp(score - 7.5))
    default = (prob > 0.45).astype(int)
    
    df = pd.DataFrame({
        "monthly_income": income,
        "monthly_expense": expenses,
        "rent_payment_ratio": rent_ratio * 100,
        "utility_payment_ratio": utility_ratio * 100,
        "telecom_payment_ratio": telecom_ratio * 100,
        "cash_flow_stability": cash_flow_stability,
        "gig_income": gig_income,
        "platform_rating": platform_rating,
        "default": default
    })
    return df

class CreditRiskEngine:
    def __init__(self):
        self.model_version = "v1.2.0"
        self.features = [
            "monthly_income", "monthly_expense", "rent_payment_ratio", 
            "utility_payment_ratio", "telecom_payment_ratio", 
            "cash_flow_stability", "gig_income", "platform_rating"
        ]
        self.active_features = list(self.features)
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=60, max_depth=5, random_state=42)
        self._train()
        
    def _train(self, prohibited_features=None):
        df = generate_synthetic_dataset(1200)
        if prohibited_features:
            self.active_features = [f for f in self.features if f not in prohibited_features]
        else:
            self.active_features = list(self.features)
            
        X = df[self.active_features]
        y = df["default"]
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

    def retrain_without_features(self, prohibited_features):
        self._train(prohibited_features=prohibited_features)
        self.model_version += "-h8-retrained"
        return self.model_version

    def predict_risk(self, input_dict):
        clean_data, warnings = self.validate_input(input_dict)
        
        feat_vals = [clean_data.get(f, 0) for f in self.active_features]
        feat_array = np.array(feat_vals).reshape(1, -1)
        feat_scaled = self.scaler.transform(feat_array)
        
        risk_prob = float(self.model.predict_proba(feat_scaled)[0][1])
        risk_score = int((1.0 - risk_prob) * 100)
        
        reasons = self.generate_reasons(clean_data, risk_prob)
        attribution = self.compute_attribution(clean_data)
        
        return risk_score, risk_prob, clean_data, warnings, reasons, attribution

    def validate_input(self, data):
        warnings = []
        clean = dict(data)
        
        if clean.get("monthly_income", 0) <= 0:
            warnings.append("Monthly income invalid. Defaulted to base threshold.")
            clean["monthly_income"] = 15000.0
            
        if clean.get("rent_payment_ratio", 100) > 100 or clean.get("rent_payment_ratio", 0) < 0:
            warnings.append("Rent payment timeliness out of bounds. Clipped to range [0-100%].")
            clean["rent_payment_ratio"] = max(0, min(100, clean.get("rent_payment_ratio", 90)))
            
        return clean, warnings

    def generate_reasons(self, data, risk_prob):
        reasons = []
        if risk_prob > 0.35:
            reasons.append("High predicted repayment default risk score.")
        if data.get("cash_flow_stability", 1.0) < 0.6:
            reasons.append("Unstable recent bank cash flow volatility.")
        if data.get("rent_payment_ratio", 100) < 85:
            reasons.append("Below target rent payment timeliness ratio.")
        if (data.get("monthly_income", 0) - data.get("monthly_expense", 0)) < 10000:
            reasons.append("Low net discretionary income buffer.")
        if data.get("utility_payment_ratio", 100) < 80:
            reasons.append("Irregular utility bill payment history.")
            
        if not reasons:
            reasons.append("Satisfactory credit profile and alternate data metrics.")
            
        return reasons[:4]

    def compute_attribution(self, data):
        # Simulated SHAP-style attribution for frontend charts
        return [
            {"feature": "Rent Payment Timeliness", "impact": round((data.get('rent_payment_ratio', 90) - 80) * 0.15, 2)},
            {"feature": "Utility Payment Timeliness", "impact": round((data.get('utility_payment_ratio', 90) - 80) * 0.1, 2)},
            {"feature": "Cash Flow Stability", "impact": round((data.get('cash_flow_stability', 0.7) - 0.5) * 18, 2)},
            {"feature": "Net Income Buffer", "impact": round(((data.get('monthly_income', 30000) - data.get('monthly_expense', 15000)) - 10000) / 5000, 2)},
            {"feature": "Gig Earnings Level", "impact": round(data.get('gig_income', 10000) / 4000, 2)}
        ]

def check_watchlist(applicant_name):
    watchlist_db = ["JOHN DOE", "SANCTIONS_USER_01", "FRAUD_TEST_99", "CRIMINAL_RECORD_X", "BAD_ACTOR_007"]
    name_upper = applicant_name.strip().upper()
    if name_upper in watchlist_db:
        return "MATCH (FLAGGED)"
    return "CLEAR"
