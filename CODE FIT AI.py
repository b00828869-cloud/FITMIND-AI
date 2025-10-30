# main.py
import json, os, math
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="SportFit AI — Classement mondial", page_icon="🏃", layout="centered")

# =============== Chargement du JSON ===============
@st.cache_data(show_spinner=True)
def load_percentiles():
    """
    Cherche percentiles_running.json à différents emplacements (racine, data/, cwd)
    Sinon, tente une URL dans st.secrets['PERC_URL'].
    """
    here = Path(__file__).parent
    candidates = [
        here / "percentiles_running.json",
        here / "data" / "percentiles_running.json",
        Path.cwd() / "percentiles_running.json",
        Path.cwd() / "data" / "percentiles_running.json",
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text())

    url = st.secrets.get("PERC_URL", "")
    if url:
        import requests
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return r.json()

    raise FileNotFoundError(
        "percentiles_running.json introuvable. Place-le à la racine du repo "
        "ou dans un dossier 'data/', ou fournis st.secrets['PERC_URL']."
    )

PERC = load_percentiles()

# =============== Helpers ===============
def available_distances():
    """Distances présentes dans le JSON."""
    dset = set()
    for k in PERC.keys():
        dset.add(float(k.split("|")[0]))
    return sorted(dset)

def available_age_bins(distance, sex_code):
    """Tranches d'âge dispos (pour info/robustesse)."""
    bins = set()
    d_key = f"{float(distance):.5f}"
    for k in PERC.keys():
        d, s, a = k.split("|")
        if d == d_key and int(s) == sex_code:
            bins.add(int(a))
    return sorted(bins)

def fmt_hms(seconds: float) -> str:
    s = int(round(max(0, seconds)))
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_time_to_seconds(time_str: str):
    """Accepte 'mm:ss' ou 'hh:mm:ss' (les décimales de secondes sont ok)."""
    time_str = (time_str or "").strip()
    if not time_str:
        return None
    try:
        parts = [float(x) for x in time_str.split(":")]
        if len(parts) == 2:
            m, s = parts
            return m * 60 + s
        if len(parts) == 3:
            h, m, s = parts
            return h * 3600 + m * 60 + s
    except Exception:
        return None
    return None

def percentile_from_quantiles(t_pred: float, qdict: dict) -> float:
    """
    Approxime le percentile (0-100) par interpolation linéaire
    depuis les clés p1..p99 si présentes, sinon utilise p10..p90/p25..p75.
    """
    # p1..p99 préférés
    pairs = [(int(k[1:]), v) for k, v in qdict.items() if k.startswith("p") and k[1:].isdigit()]
    if not pairs:
        return 50.0
    pairs.sort(key=lambda x: x[0])

    # bornes
    if t_pred <= pairs[0][1]:
        return float(pairs[0][0])
    if t_pred >= pairs[-1][1]:
        return float(pairs[-1][0])

    # interpolation
    for i in range(len(pairs) - 1):
        pL, vL = pairs[i]
        pR, vR = pairs[i + 1]
        if vL <= t_pred <= vR:
            if vR == vL:
                return float(pR)
            w = (t_pred - vL) / (vR - vL)
            return float(pL + w * (pR - pL))
    return 50.0

def rank_label(pct: float) -> str:
    if pct <= 10: return "Top 10 % (excellent)"
    if pct <= 25: return "Top 25 % (très bon)"
    if pct <= 50: return "Top 50 % (bon)"
    if pct <= 75: return "Dans la moyenne (50–75 %)"
    if pct <= 90: return "Sous la moyenne (75–90 %)"
    return "Dernier décile (> 90 %)"

def closest_available_key(distance, sex_code, age):
    """Si la clé exacte n'existe pas, on prend la tranche d'âge la plus proche pour (distance, sexe)."""
    d_key = f"{float(distance):.5f}"
    age_bin = int((age // 5) * 5)
    exact = f"{d_key}|{sex_code}|{age_bin}"
    if exact in PERC:
        return exact, age_bin, True

    # chercher le bin d'âge le plus proche
    bins = available_age_bins(distance, sex_code)
    if not bins:
        return None, age_bin, False
    nearest = min(bins, key=lambda b: abs(b - age_bin))
    return f"{d_key}|{sex_code}|{nearest}", nearest, False

# =============== UI ===============
st.title("🏃 SportFit AI — Classement mondial")
st.caption("Compare ta performance au monde (quantiles compacts, sans gros dataset).")

distances = available_distances()
c1, c2 = st.columns(2)
with c1:
    distance = st.selectbox("Distance (km)", distances, index=min(1, len(distances)-1), format_func=lambda d: f"{d:g} km")
    sex_label = st.selectbox("Sexe", ["Homme", "Femme"])
with c2:
    age = st.number_input("Âge", min_value=10, max_value=90, value=30, step=1)
    time_input = st.text_input("Ton temps (mm:ss ou hh:mm:ss)", "22:30")

if st.button("Calculer mon classement"):
    secs = parse_time_to_seconds(time_input)
    if secs is None:
        st.error("Temps invalide. Utilise mm:ss ou hh:mm:ss (ex: 22:30 ou 01:35:00).")
        st.stop()

    sex_code = 0 if sex_label == "Homme" else 1
    key, used_bin, exact = closest_available_key(distance, sex_code, age)
    if key is None or key not in PERC:
        st.warning("Pas de quantiles disponibles pour cette distance/sexe. Vérifie ton JSON.")
        st.stop()

    qdict = PERC[key]
    pct = percentile_from_quantiles(secs, qdict)
    st.metric("Ton temps", fmt_hms(secs))
    st.success(f"🎯 Position estimée : **{rank_label(pct)}** — ~p{pct:.1f}")

    # Info tranche d'âge réellement utilisée
    if not exact:
        st.caption(f"(Quantiles de la tranche {used_bin}-{used_bin+4} ans utilisés — plus proche disponible)")

    # Afficher les repères de quartiles si présents
    p25 = qdict.get("p25"); p50 = qdict.get("p50"); p75 = qdict.get("p75")
    if p25 and p50 and p75:
        st.write(f"**Quartiles repères** — Q1: {fmt_hms(p25)} | Médiane: {fmt_hms(p50)} | Q3: {fmt_hms(p75)}")
    else:
        # montrer qq percentiles si quartiles absents
        show = []
        for p in (10, 25, 50, 75, 90):
            val = qdict.get(f"p{p}")
            if val:
                show.append(f"p{p}: {fmt_hms(val)}")
        if show:
            st.write("Repères : " + " | ".join(show))

st.caption("⚠️ Interprétation : plus ton temps est bas, plus tu es rapide (percentiles calculés sur données réelles).")

