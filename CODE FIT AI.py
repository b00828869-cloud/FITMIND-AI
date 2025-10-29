# main.py
import io
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

st.set_page_config(page_title="SportFit AI — Multi-distances", page_icon="🏃", layout="centered")

# --------------------------
# Fonctions utilitaires
# --------------------------
@st.cache_data(show_spinner=False)
def load_excel_to_df(filepath: Path) -> pd.DataFrame:
    sheets = pd.read_excel(filepath, sheet_name=None)
    frames = []
    for name, df in sheets.items():
        if df is None or df.empty:
            continue
        tmp = df.copy()
        tmp.columns = tmp.columns.str.lower().str.strip()
        tmp["distance_km"] = name  # onglet = distance
        frames.append(tmp)
    df_all = pd.concat(frames, ignore_index=True)

    # Nettoyage colonnes
    df_all["distance_km"] = (
        df_all["distance_km"]
        .astype(str)
        .str.lower()
        .str.replace("km", "", regex=False)
        .str.replace("halfmarathon", "21.0975", regex=False)
        .str.replace("marathon", "42.195", regex=False)
        .str.replace("ultra", "50", regex=False)
    )
    df_all["distance_km"] = pd.to_numeric(df_all["distance_km"], errors="coerce")

    if "time" in df_all.columns:
        df_all["time_sec"] = pd.to_timedelta(df_all["time"]).dt.total_seconds()

    if "sex" in df_all.columns:
        df_all["sex"] = df_all["sex"].astype(str).str[0].str.upper().map({"M": 0, "F": 1})

    for c in ["age", "year"]:
        if c in df_all.columns:
            df_all[c] = pd.to_numeric(df_all[c], errors="coerce")

    df_all["pace_sec_per_km"] = df_all["time_sec"] / df_all["distance_km"]

    df_all = df_all.dropna(subset=["distance_km", "time_sec", "age", "sex"])
    df_all = df_all[(df_all["time_sec"] > 10 * 60) & (df_all["time_sec"] < 6 * 3600)]
    df_all = df_all[(df_all["age"] >= 10) & (df_all["age"] <= 90)]
    df_all = df_all[(df_all["distance_km"] >= 5) & (df_all["distance_km"] <= 50)]

    return df_all.reset_index(drop=True)

@st.cache_resource(show_spinner=False)
def train_model(df: pd.DataFrame):
    X = df[["distance_km", "age", "sex"]]
    y = df["time_sec"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return model, {
        "MAE (s)": float(mean_absolute_error(y_test, y_pred)),
        "R²": float(r2_score(y_test, y_pred)),
    }

def format_hms(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# --------------------------
# Chargement de la base par défaut
# --------------------------
st.title("🏃 SportFit AI — Analyse & Prédiction de performance")
st.caption("Données issues de la base mondiale des courses (5 km à marathon).")

BASE_PATH = Path(__file__).parent / "data" / "pone.0311268.s007.xlsx"

if not BASE_PATH.exists():
    st.error("❌ La base par défaut est introuvable. Vérifie le chemin : data/pone.0311268.s007.xlsx")
    st.stop()

with st.spinner("Chargement et préparation de la base mondiale..."):
    df = load_excel_to_df(BASE_PATH)

st.success(f"✅ Base chargée : {len(df):,} lignes, {df['distance_km'].nunique()} distances disponibles")

# --------------------------
# Entraînement du modèle
# --------------------------
with st.spinner("Entraînement du modèle..."):
    model, metrics = train_model(df)

st.write(f"**Performance modèle : MAE = {metrics['MAE (s)']:.1f}s | R² = {metrics['R²']:.3f}**")

# --------------------------
# Interface de prédiction
# --------------------------
st.header("🎯 Prédiction personnalisée")

c1, c2 = st.columns(2)
with c1:
    age = st.number_input("Âge", min_value=10, max_value=90, value=30)
    sex_str = st.selectbox("Sexe", ["Homme (M)", "Femme (F)"])
    sex = 0 if sex_str.startswith("Homme") else 1
with c2:
    distances = sorted(df["distance_km"].unique())
    distance_km = st.selectbox("Distance (km)", distances, index=0)

if st.button("Prédire mon temps"):
    t_pred = float(model.predict([[distance_km, age, sex]])[0])
    st.metric("⏱ Temps estimé", format_hms(t_pred))
    st.success("Prédiction effectuée à partir de la base mondiale intégrée.")

st.caption("⚠️ Cette application utilise uniquement la base intégrée — aucun upload utilisateur n’est permis.")
