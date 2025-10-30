import json
import streamlit as st

st.set_page_config(page_title="SportFit AI — Classement mondial", page_icon="🏃", layout="centered")

# --- Chargement du JSON (en cache pour rapidité) ---
@st.cache_data
def load_percentiles():
    with open("percentiles_running.json", "r") as f:
        return json.load(f)

PERC = load_percentiles()

# --- Distances disponibles ---
CANON = [5.0, 10.0, 21.0975, 42.195, 50.0]

def canonize_distance(d: float) -> float:
    return min(CANON, key=lambda x: abs(x - d))

def fmt_hms(seconds: float) -> str:
    s = int(round(max(0, seconds)))
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- Interface Streamlit ---
st.title("🏃 SportFit AI — Classement mondial")
st.caption("Compare ta performance à celles du monde entier (basé sur des données de course réelles)")

distance = st.selectbox("Distance (km)", CANON, index=1)
age = st.number_input("Âge", min_value=10, max_value=90, value=30)
sex = st.selectbox("Sexe", ["Homme", "Femme"])
temps_str = st.text_input("Ton temps (format mm:ss ou hh:mm:ss)", "22:30")

# --- Conversion du temps saisi en secondes ---
def parse_time_to_seconds(time_str):
    parts = [float(x) for x in time_str.split(":")]
    if len(parts) == 2:
        m, s = parts
        return m * 60 + s
    elif len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s
    else:
        return None

temps_sec = parse_time_to_seconds(temps_str)

if temps_sec is not None and st.button("Calculer mon classement"):
    sex_code = 0 if sex == "Homme" else 1
    age_bin = int((age // 5) * 5)
    d_key = f"{canonize_distance(distance):.5f}"
    key = f"{d_key}|{sex_code}|{age_bin}"

    if key not in PERC:
        st.warning("⚠️ Pas de données pour cette combinaison distance/sexe/âge.")
    else:
        qdict = PERC[key]
        # Approximation du percentile
        pairs = sorted(((int(k[1:]), v) for k, v in qdict.items()), key=lambda x: x[0])
        percentile = None
        for i in range(len(pairs)-1):
            pL, vL = pairs[i]
            pR, vR = pairs[i+1]
            if vL <= temps_sec <= vR:
                w = (temps_sec - vL) / (vR - vL)
                percentile = pL + w * (pR - pL)
                break
        percentile = percentile or 99.0

        # Affichage
        st.success(f"🎯 Tu es environ dans le **top {percentile:.1f}% mondial** pour {distance:g} km ({sex.lower()}, {age} ans)")
        st.metric("Ton temps", fmt_hms(temps_sec))
        st.metric("Quartile", f"{int(percentile//25)+1}ᵉ quartile")

        # Affiche les bornes des quartiles
        p25, p50, p75 = qdict.get("p25"), qdict.get("p50"), qdict.get("p75")
        if p25 and p50 and p75:
            st.write(f"**Q1 (25%)** : {fmt_hms(p25)} — **Q2 (médiane)** : {fmt_hms(p50)} — **Q3 (75%)** : {fmt_hms(p75)}")
else:
    st.info("Entre ton temps pour voir ton classement mondial.")


