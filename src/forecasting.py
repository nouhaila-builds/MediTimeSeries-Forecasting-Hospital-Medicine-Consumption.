"""Entraînement et comparaison des modèles de prévision."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.arima.model import ARIMA

from .data_preprocessing import PROJECT_ROOT, DataPreprocessor

OUTPUT_DIR = PROJECT_ROOT / "outputs"


def mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.where(np.abs(y_true) < 1e-8, np.nan, np.abs(y_true))
    return float(np.nanmean(np.abs((y_true - y_pred) / denom)) * 100)


def metrics_row(name: str, y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return {
        "Model": name,
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE": mape(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
    }


def _align(pred, n: int) -> np.ndarray:
    arr = np.asarray(pred, dtype=float).flatten()
    if len(arr) < n:
        pad = np.full(n - len(arr), arr[-1] if len(arr) else np.nan)
        arr = np.concatenate([arr, pad])
    return arr[:n]


def _maybe_lstm(y_train: np.ndarray, n_test: int, seq_len: int = 14) -> Optional[np.ndarray]:
    try:
        import tensorflow as tf
        from tensorflow.keras import Sequential
        from tensorflow.keras.layers import Dense, Dropout, LSTM
        from sklearn.preprocessing import MinMaxScaler
    except ImportError:
        return None

    if len(y_train) <= seq_len + 5:
        return None

    scaler = MinMaxScaler()
    y_s = scaler.fit_transform(y_train.reshape(-1, 1))
    xs, ys = [], []
    for i in range(seq_len, len(y_s)):
        xs.append(y_s[i - seq_len : i, 0])
        ys.append(y_s[i, 0])
    xs = np.array(xs)[..., np.newaxis]
    ys = np.array(ys)

    tf.keras.utils.set_random_seed(42)
    model = Sequential(
        [
            LSTM(32, return_sequences=True, input_shape=(seq_len, 1)),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation="relu"),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    model.fit(xs, ys, epochs=8, batch_size=16, verbose=0)

    window = y_s[-seq_len:].flatten().tolist()
    preds = []
    for _ in range(n_test):
        x = np.array(window[-seq_len:]).reshape(1, seq_len, 1)
        yhat = float(model.predict(x, verbose=0)[0, 0])
        preds.append(yhat)
        window.append(yhat)
    return scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()


def run_pipeline(
    data_path: Optional[str] = None,
    use_lstm: bool = False,
    save_outputs: bool = True,
) -> dict:
    prep = DataPreprocessor()
    raw = prep.load_data(data_path)
    daily = prep.to_daily_series(raw)
    featured = prep.add_time_features(daily)
    train, val, test = prep.chronological_split(featured)
    feature_cols = prep.feature_columns(featured)

    y_train = train["volume_consomme"].values
    y_val = val["volume_consomme"].values
    y_test = test["volume_consomme"].values
    n_test = len(y_test)
    y_hist = np.concatenate([y_train, y_val])

    scaler = StandardScaler()
    X_train = scaler.fit_transform(train[feature_cols])
    X_val = scaler.transform(val[feature_cols])
    X_test = scaler.transform(test[feature_cols])

    lin = LinearRegression().fit(X_train, y_train)
    ridge = Ridge(alpha=1.0).fit(X_train, y_train)
    rf = RandomForestRegressor(
        n_estimators=100, max_depth=10, min_samples_split=5, random_state=42, n_jobs=-1
    ).fit(X_train, y_train)

    try:
        from xgboost import XGBRegressor

        xgb = XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1,
        )
        xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        xgb_pred = xgb.predict(X_test)
    except Exception:
        xgb = None
        xgb_pred = rf.predict(X_test)

    t_idx = np.arange(len(y_hist) + n_test).reshape(-1, 1)
    lta = LinearRegression().fit(t_idx[: len(y_hist)], y_hist)
    lta_pred = lta.predict(t_idx[len(y_hist) :])

    ses = SimpleExpSmoothing(y_hist, initialization_method="estimated").fit()
    ses_pred = _align(ses.forecast(n_test), n_test)
    des = ExponentialSmoothing(
        y_hist, trend="add", seasonal=None, initialization_method="estimated"
    ).fit()
    des_pred = _align(des.forecast(n_test), n_test)

    try:
        arima = ARIMA(y_hist, order=(1, 1, 1)).fit()
        arima_pred = _align(arima.forecast(n_test), n_test)
    except Exception:
        arima_pred = ses_pred.copy()

    baseline = np.full(n_test, np.mean(y_hist[-7:]))
    lin_pred = lin.predict(X_test)
    ridge_pred = ridge.predict(X_test)
    rf_pred = rf.predict(X_test)
    hybrid = 0.4 * arima_pred + 0.6 * xgb_pred
    hybrid_mlr_des = 0.6 * ridge_pred + 0.4 * des_pred

    preds = {
        "Valeurs_Réelles": y_test,
        "Régression_Linéaire": lin_pred,
        "Random_Forest": rf_pred,
        "XGBoost": xgb_pred,
        "ARIMA": arima_pred,
        "Hybrid": hybrid,
    }

    rows = [
        metrics_row("Baseline (Moyenne Mobile 7j)", y_test, baseline),
        metrics_row("Linear Trend Analysis (LTA)", y_test, lta_pred),
        metrics_row("Single Exponential Smoothing (SES)", y_test, ses_pred),
        metrics_row("Double Exponential Smoothing (DES)", y_test, des_pred),
        metrics_row("ARIMA(1,1,1)", y_test, arima_pred),
        metrics_row("Régression Linéaire", y_test, lin_pred),
        metrics_row("Multiple Linear Regression (MLR)", y_test, ridge_pred),
        metrics_row("Random Forest", y_test, rf_pred),
        metrics_row("XGBoost", y_test, xgb_pred),
        metrics_row("Hybrid (ARIMA + XGBoost)", y_test, hybrid),
        metrics_row("Hybrid (MLR + DES)", y_test, hybrid_mlr_des),
    ]

    lstm_pred = _maybe_lstm(y_hist, n_test) if use_lstm else None
    if lstm_pred is not None:
        preds["LSTM"] = lstm_pred
        rows.append(metrics_row("LSTM", y_test, lstm_pred))

    results = pd.DataFrame(rows).sort_values("MAPE").reset_index(drop=True)
    comparison = pd.DataFrame(preds)

    if save_outputs:
        OUTPUT_DIR.mkdir(exist_ok=True)
        results.to_csv(OUTPUT_DIR / "model_results.csv", index=False)
        comparison.to_csv(OUTPUT_DIR / "comparison_real_vs_predicted.csv", index=False)

    return {
        "prep": prep,
        "raw": raw,
        "daily": daily,
        "featured": featured,
        "train": train,
        "val": val,
        "test": test,
        "results": results,
        "comparison": comparison,
        "data_path": str(prep.data_path),
        "n_features": len(feature_cols),
    }
