# main.py
import math
import streamlit as st

st.set_page_config(page_title="SportFit AI — Formule intégrée", page_icon="🏃", layout="centered")

# ---- Coefficients appris hors-ligne (ton export) ----
COEF = {
    "b0": 5.615032434973884,
    "b1": 1.0695479049806564,       # effet ln(distance)
    "b2": -0.008907716922585001,    # âge
    "b3": 0.00010565062075637132,   # âge^2
    "b4": 0.34989857595883395,      # sexe (F=1, H=0)
    "b5": -0.07783908999979514,     # interaction lnD*sexe
    "b6": 0.0011495499693939615,    # interaction lnD*âge
}

def predict_time_seconds(distance_km: float, age: float, sex_label: str) -> float:
    """ln(T) = b0 + b1*ln(D) + b2*Age + b3*Age^2 + b4*Sex + b5*(lnD*Sex) + b6*(lnD*Age) ; T en secondes"""
    sex = 0 if sex_label.lower().startswith("h") else 1  # Homme -> 0 ; Femme -> 1
    lnD = math.log(distance_km)
    x = (COEF["b0"]
         + COEF["b1"] * lnD
         + COEF["b2"] * age
         + COEF["b3"] * (age ** 2)
         + COEF["b4"] * sex
         + COEF["b5"] * lnD * sex
         + COEF["b6"] * lnD * age)
    return float(math.exp(x))

def fmt_hms(seconds: float) -> str:
    s = int(round(max(0, seconds)))
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def fmt_pace(seconds: float, km: float) -> str:
    """min/km"""
    pace = seconds / max(km, 1e-9)
    m = int(pace // 60)
    s = int(round(pace % 60))
    return f"{m:02d}:{s:02d} /km"

st.title("🏃 SportFit AI — Prédiction par formule ML (sans dataset)")
st.caption("Modèle log-linéaire entraîné hors-ligne, coefficients intégrés.")

# ---- UI ----
c1, c2 = st.columns(2)
with c1:
    age = st.number_input("Âge", min_value=10, max_value=90, value=30, step=1)
    sex = st.selectbox("Sexe", ["Homme (M)", "Femme (F)"])
with c2:
    distance = st.selectbox("Distance", [5.0, 10.0, 21.0975, 42.195, 50.0], index=1, format_func=lambda d: f"{d:g} km")

if st.button("Prédire"):
    t = predict_time_seconds(distance, age, sex)
    st.metric("⏱ Temps estimé", fmt_hms(t), help="Prédiction issue de la formule ML intégrée")
    st.write(f"Allure estimée : **{fmt_pace(t, distance)}**")

    st.divider()
    st.subheader("Extrapolation automatique sur d'autres distances")
    cols = st.columns(4)
    targets = [5.0, 10.0, 21.0975, 42.195]
    for i, d in enumerate(targets):
        tt = predict_time_seconds(d, age, sex)
        with cols[i % 4]:
            st.metric(f"{d:g} km", fmt_hms(tt), help=f"Allure ~ {fmt_pace(tt, d)}")

st.caption("⚠️ Outil informatif. Pas un avis médical. Formule : ln(T)=b0+b1 ln(D)+b2 Age+b3 Age²+b4 Sex+b5 ln(D)·Sex+b6 ln(D)·Age.")

