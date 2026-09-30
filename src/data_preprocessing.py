"""Prétraitement Open Medic et construction d'une série quotidienne."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FULL_CSV = PROJECT_ROOT / "OPEN_MEDIC_2024" / "OPEN_MEDIC_2024.CSV"
SAMPLE_CSV = PROJECT_ROOT / "data" / "raw" / "open_medic_sample.csv"

NUMERIC_COLUMNS = ("BOITES", "REM", "BSE", "age", "sexe", "BEN_REG", "PSP_SPE")


def resolve_data_path(path: Optional[str | Path] = None) -> Path:
    """Prefer the full dump when present, otherwise the versioned sample."""
    if path is not None:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (PROJECT_ROOT / candidate).resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Fichier introuvable: {candidate}")
        return candidate
    if FULL_CSV.exists():
        return FULL_CSV
    if SAMPLE_CSV.exists():
        return SAMPLE_CSV
    raise FileNotFoundError(
        "Aucune donnée trouvée. Placez OPEN_MEDIC_2024.CSV dans OPEN_MEDIC_2024/ "
        "ou conservez data/raw/open_medic_sample.csv."
    )


def _to_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


class DataPreprocessor:
    """Load Open Medic, clean numeric fields, and build a daily series."""

    def __init__(self, n_days: int = 365, start_date: str = "2023-01-01"):
        self.n_days = n_days
        self.start_date = pd.Timestamp(start_date)
        self.data_path: Optional[Path] = None

    def load_data(
        self,
        path: Optional[str | Path] = None,
        nrows: Optional[int] = None,
    ) -> pd.DataFrame:
        self.data_path = resolve_data_path(path)
        last_error: Optional[Exception] = None
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(
                    self.data_path,
                    sep=";",
                    encoding=encoding,
                    nrows=nrows,
                    low_memory=False,
                )
                break
            except UnicodeDecodeError as exc:
                last_error = exc
        else:
            raise last_error or UnicodeDecodeError("utf-8", b"", 0, 1, "encodage inconnu")
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = _to_numeric(df[col])
        df = df.drop_duplicates()
        return df

    def explore_data(self, df: pd.DataFrame) -> None:
        print(f"Fichier : {self.data_path}")
        print(f"Lignes   : {len(df):,}")
        print(f"Colonnes : {list(df.columns)}")
        print("\nTypes :")
        print(df.dtypes)
        print("\nValeurs manquantes :")
        print(df.isna().sum())
        if "BOITES" in df.columns:
            print("\nBOITES (volume) :")
            print(df["BOITES"].describe())

    def cap_outliers(self, series: pd.Series, lower_q: float = 0.01, upper_q: float = 0.99) -> pd.Series:
        low, high = series.quantile(lower_q), series.quantile(upper_q)
        return series.clip(lower=low, upper=high)

    def to_daily_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Open Medic has no transaction date. Rows are mapped onto a calendar
        window then aggregated to a daily volume (same approach as the original notebook).
        """
        if "BOITES" not in df.columns:
            raise ValueError("Colonne BOITES absente.")

        work = df.dropna(subset=["BOITES"]).copy()
        work["BOITES"] = self.cap_outliers(work["BOITES"])
        offsets = np.arange(len(work)) % self.n_days
        work["date"] = self.start_date + pd.to_timedelta(offsets, unit="D")

        daily = (
            work.groupby("date", as_index=False)["BOITES"]
            .sum()
            .rename(columns={"BOITES": "volume_consomme"})
            .sort_values("date")
            .reset_index(drop=True)
        )
        daily = daily.set_index("date").asfreq("D")
        daily["volume_consomme"] = daily["volume_consomme"].interpolate(method="time").bfill().ffill()
        return daily.reset_index()

    def add_time_features(self, daily: pd.DataFrame) -> pd.DataFrame:
        out = daily.copy()
        out["date"] = pd.to_datetime(out["date"])
        out["dayofweek"] = out["date"].dt.dayofweek
        out["month"] = out["date"].dt.month
        out["quarter"] = out["date"].dt.quarter
        out["weekofyear"] = out["date"].dt.isocalendar().week.astype(int)
        out["dayofyear"] = out["date"].dt.dayofyear
        out["is_weekend"] = (out["dayofweek"] >= 5).astype(int)

        out["dow_sin"] = np.sin(2 * np.pi * out["dayofweek"] / 7)
        out["dow_cos"] = np.cos(2 * np.pi * out["dayofweek"] / 7)
        out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
        out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)

        target = out["volume_consomme"]
        for lag in (1, 7, 14, 30):
            out[f"lag_{lag}"] = target.shift(lag)
        for window in (7, 14, 30):
            rolled = target.shift(1).rolling(window, min_periods=max(2, window // 2))
            out[f"roll_mean_{window}"] = rolled.mean()
            out[f"roll_std_{window}"] = rolled.std()
            out[f"roll_min_{window}"] = rolled.min()
            out[f"roll_max_{window}"] = rolled.max()

        return out.dropna().reset_index(drop=True)

    def chronological_split(
        self,
        featured: pd.DataFrame,
        train_size: float = 0.70,
        val_size: float = 0.15,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        n = len(featured)
        i_train = int(n * train_size)
        i_val = int(n * (train_size + val_size))
        train = featured.iloc[:i_train].copy()
        val = featured.iloc[i_train:i_val].copy()
        test = featured.iloc[i_val:].copy()
        return train, val, test

    def feature_columns(self, featured: pd.DataFrame) -> list[str]:
        exclude = {"date", "volume_consomme"}
        return [c for c in featured.columns if c not in exclude]
