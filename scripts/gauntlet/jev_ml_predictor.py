#!/usr/bin/env python3
"""
jev_ml_predictor.py — ML model for Jev signal scoring

Trains a logistic regression model on historical trade features to predict
expected R per signal. Outputs feature importance to help Jev understand
WHICH characteristics drive performance (not just aggregate stats).

Model: LogisticRegression with L2 regularization (fast, interpretable).
Retrains on demand, caches to disk.

Usage:
    from jev_ml_predictor import MLPredictor
    pred = MLPredictor()
    result = pred.predict_signal(signal_dict)
    # result: {expected_r, win_prob, feature_importance: {...}, model_confidence}
"""

from __future__ import annotations

import json
import os
import pickle
import time
from datetime import datetime
from typing import Optional

import numpy as np

from jev_feature_extractor import extract_features, extract_signal_features

MODEL_CACHE = os.path.join(os.path.dirname(__file__), ".jev_ml_model.pkl")
STALE_AFTER_HOURS = 24  # Retrain daily


class MLPredictor:
    """Logistic regression predictor for signal expected R."""
    
    def __init__(self):
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        self.feature_names: list[str] = []
        self.feature_importance: dict[str, float] = {}
        self.n_samples = 0
        self.trained_at: Optional[datetime] = None
        self._load_or_train()
    
    def _load_or_train(self):
        """Load cached model or train from scratch."""
        if os.path.exists(MODEL_CACHE):
            try:
                with open(MODEL_CACHE, "rb") as f:
                    data = pickle.load(f)
                age_h = (time.time() - data.get("trained_at_ts", 0)) / 3600
                if age_h < STALE_AFTER_HOURS:
                    self.model = data["model"]
                    self.scaler_mean = data["scaler_mean"]
                    self.scaler_std = data["scaler_std"]
                    self.feature_names = data["feature_names"]
                    self.feature_importance = data["feature_importance"]
                    self.n_samples = data["n_samples"]
                    self.trained_at = data.get("trained_at")
                    return
            except Exception:
                pass  # Retrain on failure
        
        self._train()
    
    def _train(self):
        """Train logistic regression on historical trades."""
        from sklearn.linear_model import LogisticRegression
        
        X, y, self.feature_names = extract_features()
        
        if len(y) < 10:
            self.model = None
            self.n_samples = 0
            return
        
        # Binary target: win (R > 0) vs loss
        y_binary = (y > 0).astype(int)
        
        # Standardize
        self.scaler_mean = X.mean(axis=0)
        self.scaler_std = X.std(axis=0)
        self.scaler_std[self.scaler_std < 1e-8] = 1.0  # avoid div by zero
        X_scaled = (X - self.scaler_mean) / self.scaler_std
        
        # Train
        self.model = LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            class_weight="balanced",
        )
        self.model.fit(X_scaled, y_binary)
        
        self.n_samples = len(y)
        self.trained_at = datetime.now()
        
        # Feature importance from coefficients
        coefs = self.model.coef_[0]
        self.feature_importance = {}
        for name, coef in zip(self.feature_names, coefs):
            self.feature_importance[name] = float(coef)
        
        # Sort by absolute importance
        self.feature_importance = dict(
            sorted(self.feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
        )
        
        # Cache
        try:
            with open(MODEL_CACHE, "wb") as f:
                pickle.dump({
                    "model": self.model,
                    "scaler_mean": self.scaler_mean,
                    "scaler_std": self.scaler_std,
                    "feature_names": self.feature_names,
                    "feature_importance": self.feature_importance,
                    "n_samples": self.n_samples,
                    "trained_at_ts": time.time(),
                    "trained_at": self.trained_at,
                }, f)
        except OSError:
            pass
    
    def predict_signal(self, signal: dict) -> dict:
        """
        Predict expected performance for a live signal.
        
        Returns:
            {
                "available": bool,
                "win_probability": float,     # 0-1 probability of winning
                "expected_r": float,          # rough expected R (scaled)
                "top_features": [...],        # top 3 most influential features
                "n_training_samples": int,
                "model_age_hours": float,
            }
        """
        if self.model is None or self.n_samples < 10:
            return {
                "available": False,
                "reason": f"Insufficient training data ({self.n_samples} samples)" 
                          if self.n_samples > 0 else "No training data",
                "n_training_samples": self.n_samples,
            }
        
        # Extract features for this signal
        X = extract_signal_features(signal)
        if X.shape[0] != len(self.feature_names):
            return {"available": False, "reason": "Feature dimension mismatch"}
        
        # Scale
        X_scaled = (X - self.scaler_mean) / self.scaler_std
        
        # Predict
        win_prob = float(self.model.predict_proba(X_scaled.reshape(1, -1))[0][1])
        
        # Expected R: rough estimate from win_prob (calibrated)
        # win_prob * avg_win_R + (1-win_prob) * avg_loss_R
        # Use coarse values: avg win ~+1.8R, avg loss ~-1.2R
        expected_r = win_prob * 1.8 + (1 - win_prob) * (-1.2)
        
        # Top 3 features for this signal (by absolute coefficient)
        top_features = []
        for name, importance in list(self.feature_importance.items())[:5]:
            # Get the actual value for this signal
            idx = self.feature_names.index(name) if name in self.feature_names else -1
            val = float(X[idx]) if idx >= 0 else 0
            direction = "positive" if importance > 0 else "negative"
            top_features.append({
                "feature": name,
                "importance": round(abs(importance), 4),
                "direction": direction,
                "signal_value": round(val, 3),
            })
        
        age_h = (datetime.now() - self.trained_at).total_seconds() / 3600 if self.trained_at else 0
        
        return {
            "available": True,
            "win_probability": round(win_prob, 4),
            "expected_r": round(expected_r, 4),
            "top_features": top_features,
            "n_training_samples": self.n_samples,
            "model_age_hours": round(age_h, 1),
        }
    
    def retrain(self) -> dict:
        """Force retrain and return summary."""
        self._train()
        return self.summary()
    
    def summary(self) -> dict:
        """Model summary for reporting."""
        if self.model is None:
            return {"trained": False, "n_samples": 0}
        
        return {
            "trained": True,
            "n_samples": self.n_samples,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "top_features": list(self.feature_importance.items())[:5],
            "feature_count": len(self.feature_names),
        }


# ── Quick test ──

if __name__ == "__main__":
    p = MLPredictor()
    s = p.summary()
    print(f"Trained: {s['trained']}")
    print(f"Samples: {s['n_samples']}")
    print(f"Trained at: {s['trained_at']}")
    print(f"\nTop 10 feature importances:")
    for name, imp in s["top_features"]:
        direction = "↑" if imp > 0 else "↓"
        print(f"  {direction} {name}: {imp:.4f}")
    
    # Test on a live signal
    sig = {
        "strategy_id": "STR-Q-liquidity-sweep",
        "ticker": "BTC",
        "direction": "long",
        "entry_price": "87200",
        "stop_price": "86900",
        "target_price": "88100",
        "asset_class": "crypto",
        "quality_tier": "high",
        "confirmation_level": "3",
        "weekly_gate_scaling": "1.0",
    }
    pred = p.predict_signal(sig)
    print(f"\n─── BTC Long Signal Prediction ───")
    print(f"Win probability: {pred.get('win_probability', 'N/A'):.1%}" if pred.get('available') else f"Not available: {pred.get('reason')}")
    print(f"Expected R: {pred.get('expected_r', 'N/A')}")
    if pred.get("top_features"):
        print(f"Top features:")
        for f in pred["top_features"][:3]:
            print(f"  {f['direction']} {f['feature']}: importance={f['importance']:.4f}, value={f['signal_value']}")