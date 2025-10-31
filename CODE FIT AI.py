import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Constants & Helpers
# -----------------------------
ACTIVITY_MULT = {
    "Sédentaire": 1.20,
    "Légèrement actif": 1.375,
    "Modérément actif": 1.55,
    "Très actif": 1.725,
    "Extrêmement actif": 1.90,
    "Sedentary": 1.20,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extra Active": 1.90,
}

def kg_to_lbs(x): return x * 2.2046226218
def lbs_to_kg(x): return x / 2.2046226218

def bmr_mifflin_st_jeor(sex, age, height_cm, weight_kg):
    s = 5 if sex in ["Homme", "M", "Male", "male"] else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def adherence_level(deficit_kcal_per_day, weeks):
    score = 0.5 * min(deficit_kcal_per_day, 900) / 900 + 0.5 * min(weeks, 16) / 16
    if score < 0.40:
        return "Facile 🟢", "Objectif réaliste et tenable."
    elif score < 0.70:
        return "Modéré 🟠", "Faisable avec régularité (attention aux écarts)."
    else:
        return "Difficile 🔴", "Ambitieux : réduire le déficit ou allonger la durée."

def plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level,
                min_deficit=300, max_deficit=900):
    bmr = bmr_mifflin_st_jeor(sex, age, height_cm, weight_start)
    tdee = bmr * ACTIVITY_MULT.get(activity_level, 1.55)
    target_loss_kg  = abs(weight_start - weight_goal)
    target_loss_lbs = kg_to_lbs(target_loss_kg)
    days = max(1, int(weeks * 7))

    deficit_req = (target_loss_lbs * 3500) / days
    deficit_req = float(np.clip(deficit_req, min_deficit, max_deficit))

    calories_goal = tdee - deficit_req
    min_intake = 1200 if sex in ["Femme", "F", "Female", "female"] else 1500
    calories_goal = max(calories_goal, min_intake)

    physio_loss_per_week_kg = (deficit_req * 7.0) / 7700.0
    physio_total_kg = physio_loss_per_week_kg * weeks

    level, msg = adherence_level(deficit_req, weeks)

    return dict(
        bmr=bmr, tdee=tdee,
        deficit=deficit_req, kcal=calories_goal,
        target_loss_kg=target_loss_kg, physio_total_kg=physio_total_kg,
        level=level, comment=msg
    )

def projection(weight_start, weight_goal, weeks):
    t = np.arange(0, int(np.ceil(weeks)) + 1)
    w = weight_start + (weight_goal - weight_start) * (t / max(1, weeks))
    return pd.DataFrame({"Semaine": t, "Poids (kg)": w})

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="FitPath — MVP Physio", page_icon="🏋️", layout="centered")
st.title("🏋️ FitPath — MVP Physiologique")
st.caption("BMR → TDEE → Déficit → Calories → Projection. Sans ML (dataset insuffisant).")

with st.sidebar:
    st.header("Paramètres utilisateur")
    sex = st.selectbox("Sexe", ["Homme", "Femme"])
    age = st.number_input("Âge", 18, 80, 26)
    height_cm = st.number_input("Taille (cm)", 140, 210, 180)
    weight_start = st.number_input("Poids actuel (kg)", 40.0, 200.0, 84.0, step=0.5)
    weight_goal = st.number_input("Poids objectif (kg)", 40.0, 200.0, 79.0, step=0.5)
    weeks = st.number_input("Durée (semaines)", 1, 52, 8)
    activity_level = st.selectbox("Niveau d'activité", ["Sédentaire", "Légèrement actif", "Modérément actif", "Très actif", "Extrêmement actif"])

out = plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level)

st.subheader("📊 Résumé du plan")
col1, col2 = st.columns(2)
with col1:
    st.metric("BMR (kcal/j)", f"{out['bmr']:.0f}")
    st.metric("TDEE (kcal/j)", f"{out['tdee']:.0f}")
with col2:
    st.metric("Déficit (kcal/j)", f"{out['deficit']:.0f}")
    st.metric("Apport conseillé (kcal/j)", f"{out['kcal']:.0f}")

st.write(f"**Perte visée :** {out['target_loss_kg']:.1f} kg en {weeks} semaines")
st.write(f"**Perte théorique :** {out['physio_total_kg']:.1f} kg")
st.info(f"**Faisabilité : {out['level']}** — {out['comment']}")

dfp = projection(weight_start, weight_goal, weeks)
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(dfp['Semaine'], dfp['Poids (kg)'], marker='o')
ax.set_title("Projection (objectif théorique)")
ax.set_xlabel("Semaines")
ax.set_ylabel("Poids (kg)")
ax.grid(True, alpha=0.3)
st.pyplot(fig)

with st.expander("🧠 Comment c'est calculé ?"):
    st.markdown(
        "- **BMR (Mifflin–St Jeor)** : `10*poids + 6.25*taille - 5*âge + s` (s=5 H / s=-161 F)\n"
        "- **TDEE** = BMR × facteur activité\n"
        "- **Déficit requis/j** = `(perte(lbs) * 3500) / (semaines*7)` (borné 300–900 kcal/j)\n"
        "- **Apport conseillé** = TDEE − déficit\n"
        "- **Perte théorique** = `(déficit*7)/7700` kg/sem × nombre de semaines"
    )
