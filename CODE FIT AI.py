# CODE FIT AI.py
import json, math
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="SportFit AI — Classement + IA", page_icon="🏃", layout="centered")

# ====== Chargement du JSON de percentiles (racine du repo) ======
@st.cache_data(show_spinner=True)
def load_percentiles() -> Dict[str, Dict[str, float]]:
    here = Path(__file__).resolve().parent
    json_path = here / "percentiles_running.json"
    if not json_path.exists():
        files_here = [p.name for p in here.iterdir()]
        raise FileNotFoundError(
            f"percentiles_running.json manquant à la racine.\nVu à côté du script : {files_here}"
        )
    return json.loads(json_path.read_text(encoding="utf-8"))

PERC = load_percentiles()

# ====== Coefficients ML (formule log-linéaire) ======
# ln(T) = b0 + b1*ln(D) + b2*Age + b3*Age^2 + b4*Sex + b5*(lnD*Sex) + b6*(lnD*Age)
COEF = {
    "b0": 5.615032434973884,
    "b1": 1.0695479049806564,
    "b2": -0.008907716922585001,
    "b3": 0.00010565062075637132,
    "b4": 0.34989857595883395,
    "b5": -0.07783908999979514,
    "b6": 0.0011495499693939615,
}

# ====== Helpers ======
def available_distances() -> List[float]:
    return sorted({float(k.split("|")[0]) for k in PERC})

def fmt_hms(seconds: float) -> str:
    s = int(round(max(0, seconds)))
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_time_to_seconds(txt: str):
    if not txt: return None
    try:
        parts = [float(x) for x in txt.strip().split(":")]
        if len(parts) == 2:  # mm:ss
            m, s = parts; return m*60 + s
        if len(parts) == 3:  # hh:mm:ss
            h, m, s = parts; return h*3600 + m*60 + s
    except Exception:
        return None
    return None

def predict_time_seconds(distance_km: float, age: int, sex_code: int) -> float:
    lnD = math.log(distance_km)
    x = (COEF["b0"] + COEF["b1"]*lnD + COEF["b2"]*age + COEF["b3"]*(age**2)
         + COEF["b4"]*sex_code + COEF["b5"]*lnD*sex_code + COEF["b6"]*lnD*age)
    return float(math.exp(x))

def percentile_from_quantiles(t_val: float, qdict: Dict[str, float]) -> float:
    pairs = [(int(k[1:]), v) for k, v in qdict.items() if k.startswith("p") and k[1:].isdigit()]
    if not pairs: return 50.0
    pairs.sort(key=lambda x: x[0])
    if t_val <= pairs[0][1]: return float(pairs[0][0])
    if t_val >= pairs[-1][1]: return float(pairs[-1][0])
    for i in range(len(pairs)-1):
        pL, vL = pairs[i]; pR, vR = pairs[i+1]
        if vL <= t_val <= vR:
            if vR == vL: return float(pR)
            w = (t_val - vL) / (vR - vL)
            return float(pL + w*(pR - pL))
    return 50.0

def rank_label(pct: float) -> str:
    if pct <= 10: return "Top 10 % (excellent)"
    if pct <= 25: return "Top 25 % (très bon)"
    if pct <= 50: return "Top 50 % (bon)"
    if pct <= 75: return "Dans la moyenne (50–75 %)"
    if pct <= 90: return "Sous la moyenne (75–90 %)"
    return "Dernier décile (> 90 %)"

def closest_key(distance: float, sex_code: int, age: int) -> Tuple[str, int, bool]:
    d_key = f"{float(distance):.5f}"
    age_bin = int((age // 5) * 5)
    exact = f"{d_key}|{sex_code}|{age_bin}"
    if exact in PERC: return exact, age_bin, True
    # sinon, on prend la tranche d'âge la plus proche dispo
    cands = [k for k in PERC if k.startswith(d_key + "|" + str(sex_code) + "|")]
    if not cands: return None, age_bin, False
    bins = [int(k.split("|")[2]) for k in cands]
    nearest = min(bins, key=lambda b: abs(b - age_bin))
    return f"{d_key}|{sex_code}|{nearest}", nearest, False

def pace_str(total_sec: float, km: float) -> str:
    pace = total_sec / max(km, 1e-9)
    m = int(pace // 60); s = int(round(pace % 60))
    return f"{m:02d}:{s:02d} /km"

def build_splits(total_sec: float, distance_km: float) -> List[str]:
    pace = total_sec / distance_km
    splits = []
    for k in range(1, int(distance_km)+1):
        t = pace * k
        splits.append(f"{k} km — {fmt_hms(t)}")
    # dernier partiel si distance non entière (ex: 21.0975)
    frac = distance_km - int(distance_km)
    if frac > 1e-6:
        t = pace * distance_km
        splits.append(f"{distance_km:g} km — {fmt_hms(t)}")
    return splits

def draw_percentile_chart(qdict: Dict[str, float], t_user: float, distance: float):
    # Construire arrays percentiles (x) et temps (y minutes)
    pairs = [(int(k[1:]), v) for k, v in qdict.items() if k.startswith("p") and k[1:].isdigit()]
    pairs.sort(key=lambda x: x[0])
    if not pairs: 
        st.info("Pas assez de percentiles pour tracer la courbe.")
        return
    x = np.array([p for p, _ in pairs])
    y = np.array([v/60.0 for _, v in pairs])  # minutes

    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot(x, y, linewidth=2)  # courbe percentiles
    # point utilisateur
    pct_user = percentile_from_quantiles(t_user, qdict)
    ax.scatter([pct_user], [t_user/60.0], s=60, zorder=3)
    ax.axhline(t_user/60.0, linestyle="--", linewidth=1)
    ax.axvline(pct_user, linestyle="--", linewidth=1)

    ax.set_xlabel("Percentile (plus bas = plus rapide)")
    ax.set_ylabel("Temps (minutes)")
    ax.set_title(f"Distribution mondiale — {distance:g} km")
    st.pyplot(fig)

# ====== UI ======
st.title("🏃 SportFit AI — Classement + Prédiction IA + Allures")
st.caption("JSON de percentiles ultra-léger + formule ML intégrée (aucun gros dataset).")

distances = available_distances()
c1, c2 = st.columns(2)
with c1:
    distance = st.selectbox("Distance (km)", distances, index=min(1, len(distances)-1), format_func=lambda d: f"{d:g} km")
    sex_label = st.selectbox("Sexe", ["Homme (M)", "Femme (F)"])
with c2:
    age = st.number_input("Âge", 10, 90, 30, 1)
    mode = st.radio("Temps", ["Je saisis mon temps", "Estimer via IA (formule)"], horizontal=False)

time_input = None
secs = None
if mode == "Je saisis mon temps":
    time_input = st.text_input("Ton temps (mm:ss ou hh:mm:ss)", "22:30")

if st.button("Calculer"):
    sex_code = 0 if sex_label.startswith("Homme") else 1

    if mode == "Je saisis mon temps":
        secs = parse_time_to_seconds(time_input)
        if secs is None:
            st.error("Temps invalide. Utilise mm:ss ou hh:mm:ss (ex: 22:30 ou 01:35:00).")
            st.stop()
    else:
        secs = predict_time_seconds(distance, age, sex_code)

    # lookup percentiles
    key, used_bin, exact = closest_key(distance, sex_code, age)
    if key is None or key not in PERC:
        st.warning("Pas de quantiles pour cette distance/sexe. Vérifie le JSON.")
        st.stop()

    qdict = PERC[key]
    pct = percentile_from_quantiles(secs, qdict)

    # Résultats clés
    cA, cB, cC = st.columns(3)
    with cA: st.metric("Temps", fmt_hms(secs))
    with cB: st.metric("Allure", pace_str(secs, distance))
    with cC: st.metric("Rang estimé", f"{rank_label(pct)}  (p{pct:.1f})")

    if not exact:
        st.caption(f"(Tranche d’âge utilisée : {used_bin}-{used_bin+4} ans — plus proche disponible)")

    # Graphique de positionnement
    st.subheader("Courbe des percentiles — positionnement")
    draw_percentile_chart(qdict, secs, distance)

    # Splits
    with st.expander("Voir les splits (km par km)"):
        for row in build_splits(secs, distance):
            st.write("• " + row)

st.caption("Lecture : plus ton temps est bas, plus tu es rapide. La prédiction IA utilise une régression log-linéaire entraînée hors-ligne.")

