# CODE FIT AI.py
import json, math
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="SportFit AI — Classement mondial", page_icon="🏃", layout="centered")

# ========= Chargement du JSON (à la RACINE, même niveau que ce fichier) =========
@st.cache_data(show_spinner=True)
def load_percentiles():
    here = Path(__file__).resolve().parent  # dossier contenant "CODE FIT AI.py"
    json_path = here / "percentiles_running.json"  # même niveau que le script

    if json_path.exists():
        # petit message de debug utile la 1re fois
        st.info(f"📄 JSON chargé : {json_path.name}")
        return json.loads(json_path.read_text(encoding="utf-8"))

    # si jamais le fichier n’est pas trouvé, on affiche ce qu’il voit au même niveau
    files_here = [p.name for p in here.iterdir()]
    raise FileNotFoundError(
        "percentiles_running.json introuvable à la racine du repo.\n"
        f"Emplacement attendu : {json_path}\n"
        "Fichiers vus au même niveau que le script :\n- " + "\n- ".join(files_here)
    )

PERC = load_percentiles()

# ========= Helpers =========
def available_distances():
    dset = {float(k.split("|")[0]) for k in PERC.keys()}
    return sorted(dset)

def fmt_hms(seconds: float) -> str:
    s = int(round(max(0, seconds)))
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_time_to_seconds(txt: str):
    """Accepte mm:ss ou hh:mm:ss (ex: '22:30' ou '1:35:00')."""
    if not txt:
        return None
    try:
        parts = [float(x) for x in txt.strip().split(":")]
        if len(parts) == 2:
            m, s = parts
            return m * 60 + s
        if len(parts) == 3:
            h, m, s = parts
            return h * 3600 + m * 60 + s
    except Exception:
        return None
    return None

def percentile_from_quantiles(t_val: float, qdict: dict) -> float:
    """Interpolation linéaire sur les clés p1..p99 si présentes."""
    pairs = [(int(k[1:]), v) for k, v in qdict.items() if k.startswith("p") and k[1:].isdigit()]
    if not pairs:
        return 50.0
    pairs.sort(key=lambda x: x[0])

    if t_val <= pairs[0][1]:
        return float(pairs[0][0])
    if t_val >= pairs[-1][1]:
        return float(pairs[-1][0])

    for i in range(len(pairs) - 1):
        pL, vL = pairs[i]
        pR, vR = pairs[i + 1]
        if vL <= t_val <= vR:
            if vR == vL:
                return float(pR)
            w = (t_val - vL) / (vR - vL)
            return float(pL + w * (pR - pL))
    return 50.0

def rank_label(pct: float) -> str:
    if pct <= 10: return "Top 10 % (excellent)"
    if pct <= 25: return "Top 25 % (très bon)"
    if pct <= 50: return "Top 50 % (bon)"
    if pct <= 75: return "Dans la moyenne (50–75 %)"
    if pct <= 90: return "Sous la moyenne (75–90 %)"
    return "Dernier décile (> 90 %)"

def closest_available_key(distance: float, sex_code: int, age: int):
    """Prend la tranche d’âge la plus proche si la clé exacte n’existe pas."""
    d_key = f"{float(distance):.5f}"
    age_bin = int((age // 5) * 5)
    exact_key = f"{d_key}|{sex_code}|{age_bin}"
    if exact_key in PERC:
        return exact_key, age_bin, True

    # chercher le bin d’âge voisin pour cette distance et ce sexe
    candidates = [k for k in PERC.keys() if k.startswith(d_key + "|" + str(sex_code) + "|")]
    if not candidates:
        return None, age_bin, False
    bins = [int(k.split("|")[2]) for k in candidates]
    nearest = min(bins, key=lambda b: abs(b - age_bin))
    return f"{d_key}|{sex_code}|{nearest}", nearest, False

# ========= UI =========
st.title("🏃 SportFit AI — Classement mondial")
st.caption("Entre ta perf et vois ton rang mondial (JSON de percentiles, pas de gros dataset).")

distances = available_distances()
c1, c2 = st.columns(2)
with c1:
    distance = st.selectbox("Distance (km)", distances, index=min(1, len(distances)-1), format_func=lambda d: f"{d:g} km")
    sex_label = st.selectbox("Sexe", ["Homme", "Femme"])
with c2:
    age = st.number_input("Âge", min_value=10, max_value=90, value=30, step=1)
    time_txt = st.text_input("Ton temps (mm:ss ou hh:mm:ss)", "22:30")

if st.button("Calculer mon classement"):
    secs = parse_time_to_seconds(time_txt)
    if secs is None:
        st.error("Temps invalide. Utilise mm:ss ou hh:mm:ss (ex: 22:30 ou 01:35:00).")
        st.stop()

    sex_code = 0 if sex_label == "Homme" else 1
    key, used_bin, exact = closest_available_key(distance, sex_code, age)
    if key is None or key not in PERC:
        st.warning("Pas de quantiles disponibles pour cette distance/sexe. Vérifie le JSON.")
        st.stop()

    qdict = PERC[key]
    pct = percentile_from_quantiles(secs, qdict)

    st.metric("Ton temps", fmt_hms(secs))
    st.success(f"🎯 Position estimée : **{rank_label(pct)}** — ~p{pct:.1f}")
    if not exact:
        st.caption(f"(Tranche d’âge utilisée : {used_bin}-{used_bin+4} ans — plus proche disponible)")

    # Quartiles s'ils existent
    p25, p50, p75 = qdict.get("p25"), qdict.get("p50"), qdict.get("p75")
    if p25 and p50 and p75:
        st.write(f"**Quartiles repères** — Q1: {fmt_hms(p25)} | Médiane: {fmt_hms(p50)} | Q3: {fmt_hms(p75)}")
    else:
        # sinon afficher quelques percentiles utiles
        rep = []
        for p in (5, 10, 25, 50, 75, 90, 95):
            v = qdict.get(f"p{p}")
            if v:
                rep.append(f"p{p}: {fmt_hms(v)}")
        if rep:
            st.write("Repères : " + " | ".join(rep))

st.caption("⚠️ Lecture : plus ton temps est bas, meilleur est ton rang (percentiles calculés sur données réelles).")

