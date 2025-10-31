import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Constants & Helpers
# -----------------------------
ACTIVITY_MULT = {
    "Sedentary": 1.20,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extra Active": 1.90,
    # French aliases (for flexibility)
    "Sédentaire": 1.20,
    "Légèrement actif": 1.375,
    "Modérément actif": 1.55,
    "Très actif": 1.725,
    "Extrêmement actif": 1.90,
}

def kg_to_lbs(x): return x * 2.2046226218
def lbs_to_kg(x): return x / 2.2046226218

def bmr_mifflin_st_jeor(sex, age, height_cm, weight_kg):
    s = 5 if sex in ["Male", "M", "Homme", "male"] else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def adherence_level(deficit_kcal_per_day, weeks):
    score = 0.5 * min(deficit_kcal_per_day, 900) / 900 + 0.5 * min(weeks, 16) / 16
    if score < 0.40:
        return "Easy 🟢", "A realistic and sustainable goal."
    elif score < 0.70:
        return "Moderate 🟠", "Achievable with consistency (watch out for deviations)."
    else:
        return "Challenging 🔴", "Ambitious — consider lowering the deficit or extending the duration."

def plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level,
                min_deficit=300, max_deficit=900):
    bmr = bmr_mifflin_st_jeor(sex, age, height_cm, weight_start)
    tdee = bmr * ACTIVITY_MULT.get(activity_level, 1.55)
    target_loss_kg = abs(weight_start - weight_goal)
    target_loss_lbs = kg_to_lbs(target_loss_kg)
    days = max(1, int(weeks * 7))

    # Theoretical daily calorie deficit (in kcal)
    deficit_req = (target_loss_lbs * 3500) / days
    deficit_req = float(np.clip(deficit_req, min_deficit, max_deficit))

    calories_goal = tdee - deficit_req
    min_intake = 1200 if sex in ["Female", "F", "Femme", "female"] else 1500
    calories_goal = max(calories_goal, min_intake)

    # Theoretical weight loss (kg)
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
    return pd.DataFrame({"Week": t, "Weight (kg)": w})

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="FitPath — Physiological MVP", page_icon="🏋️", layout="centered")
st.title("🏋️ FitPath — Physiological MVP")
st.caption("BMR → TDEE → Deficit → Calories → Projection. No ML (dataset too small).")

with st.sidebar:
    st.header("User Settings")
    sex = st.selectbox("Gender", ["Male", "Female"])
    age = st.number_input("Age", 18, 80, 26)
    height_cm = st.number_input("Height (cm)", 140, 210, 180)
    weight_start = st.number_input("Current weight (kg)", 40.0, 200.0, 84.0, step=0.5)
    weight_goal = st.number_input("Target weight (kg)", 40.0, 200.0, 79.0, step=0.5)
    weeks = st.number_input("Duration (weeks)", 1, 52, 8)
    activity_level = st.selectbox("Activity level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"])

out = plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level)

st.subheader("📊 Plan Summary")
col1, col2 = st.columns(2)
with col1:
    st.metric("BMR (kcal/day)", f"{out['bmr']:.0f}")
    st.metric("TDEE (kcal/day)", f"{out['tdee']:.0f}")
with col2:
    st.metric("Deficit (kcal/day)", f"{out['deficit']:.0f}")
    st.metric("Recommended intake (kcal/day)", f"{out['kcal']:.0f}")

st.write(f"**Target loss:** {out['target_loss_kg']:.1f} kg over {weeks} weeks")
st.write(f"**Theoretical loss:** {out['physio_total_kg']:.1f} kg")
st.info(f"**Feasibility:** {out['level']} — {out['comment']}")

dfp = projection(weight_start, weight_goal, weeks)
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(dfp['Week'], dfp['Weight (kg)'], marker='o')
ax.set_title("Weight projection (theoretical objective)")
ax.set_xlabel("Weeks")
ax.set_ylabel("Weight (kg)")
ax.grid(True, alpha=0.3)
st.pyplot(fig)

with st.expander("🧠 How it’s calculated"):
    st.markdown(
        "- **BMR (Mifflin–St Jeor)**: `10*weight + 6.25*height - 5*age + s` (s=5 for men / s=-161 for women)\n"
        "- **TDEE** = BMR × activity factor\n"
        "- **Required daily deficit** = `(loss(lbs) * 3500) / (weeks * 7)` (bounded between 300–900 kcal/day)\n"
        "- **Recommended intake** = TDEE − deficit\n"
        "- **Theoretical loss** = `(deficit*7)/7700` kg/week × number of weeks"
    )
