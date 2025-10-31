import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# Constants & Helpers
# =========================
ACTIVITY_MULT = {
    "Sedentary": 1.20,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extra Active": 1.90,
    # French aliases accepted too (for flexibility)
    "Sédentaire": 1.20,
    "Légèrement actif": 1.375,
    "Modérément actif": 1.55,
    "Très actif": 1.725,
    "Extrêmement actif": 1.90,
}

PALETTE = {
    "deep": "#240046",     # deep purple
    "mid": "#7B2CBF",      # purple
    "accent": "#FF5E78",   # coral
    "sun": "#FFD100",      # yellow
    "ink": "#222222",
    "muted": "#555555",
    "grid": "#DADCE0",
    "panel": "#F9F9FB",
}

def kg_to_lbs(x): return x * 2.2046226218
def lbs_to_kg(x): return x / 2.2046226218

def bmr_mifflin_st_jeor(sex, age, height_cm, weight_kg):
    # s = 5 (male) / -161 (female)
    s = 5 if sex in ["Male", "M", "Homme", "male"] else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def adherence_level(deficit_kcal_per_day, weeks):
    # simple perceived “load” score = large deficit + long duration => harder
    score = 0.5 * min(deficit_kcal_per_day, 900) / 900 + 0.5 * min(weeks, 16) / 16
    if score < 0.40:
        return "Easy 🟢", "A realistic and sustainable goal."
    elif score < 0.70:
        return "Moderate 🟠", "Achievable with consistency (watch out for deviations)."
    else:
        return "Challenging 🔴", "Ambitious — consider reducing the deficit or extending the duration."

def plan_physio(
    sex, age, height_cm, weight_start, weight_goal, weeks, activity_level,
    min_deficit=300, max_deficit=900
):
    bmr = bmr_mifflin_st_jeor(sex, age, height_cm, weight_start)
    tdee = bmr * ACTIVITY_MULT.get(activity_level, 1.55)

    target_loss_kg  = abs(weight_start - weight_goal)
    target_loss_lbs = kg_to_lbs(target_loss_kg)
    days = max(1, int(weeks * 7))

    # Theoretical deficit (kcal/day) to reach the target in the given time
    deficit_req = (target_loss_lbs * 3500) / days
    deficit_req = float(np.clip(deficit_req, min_deficit, max_deficit))

    # Recommended calories (with safety floor)
    calories_goal = tdee - deficit_req
    min_intake = 1200 if sex in ["Female", "F", "Femme", "female"] else 1500
    calories_goal = max(calories_goal, min_intake)

    # Theoretical loss in kg
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

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="FitPath — Physiological MVP", page_icon="🏋️", layout="centered")

# Small CSS touch for a cleaner look
st.markdown(f"""
<style>
  .stApp {{ background: {PALETTE['panel']}; }}
  .metric-value, .metric-label {{ color: {PALETTE['ink']} !important; }}
  h1, h2, h3 {{ color: {PALETTE['deep']} !important; }}
  .st-emotion-cache-ue6h4q {{ color: {PALETTE['muted']} !important; }}
</style>
""", unsafe_allow_html=True)

st.title("🏋️ FitPath — Physiological MVP")
st.caption("BMR → TDEE → Deficit → Calories → Projection. No ML (dataset too small).")

# Sidebar inputs
with st.sidebar:
    st.header("User Settings")
    sex = st.selectbox("Gender", ["Male", "Female"])
    age = st.number_input("Age", 18, 80, 26)
    height_cm = st.number_input("Height (cm)", 140, 210, 180)
    weight_start = st.number_input("Current weight (kg)", 40.0, 200.0, 84.0, step=0.5)
    weight_goal = st.number_input("Target weight (kg)", 40.0, 200.0, 79.0, step=0.5)
    weeks = st.number_input("Duration (weeks)", 1, 52, 8)
    activity_level = st.selectbox(
        "Activity level",
        ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"]
    )

out = plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level)

# Summary metrics
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

# =========================
# Modern chart (clean aesthetic)
# =========================
# =========================
# Modern chart (clean aesthetic) — no forced zero on Y
# =========================
from matplotlib.ticker import MaxNLocator

dfp = projection(weight_start, weight_goal, weeks)
y = dfp["Weight (kg)"].values
y_min, y_max = float(y.min()), float(y.max())
# padding pour respirer autour de la courbe
pad = max(0.5, (y_max - y_min) * 0.15)

fig, ax = plt.subplots(figsize=(8, 4))

# Line + markers avec couleurs modernes
ax.plot(
    dfp["Week"],
    dfp["Weight (kg)"],
    color=PALETTE["accent"],
    linewidth=3,
    marker="o",
    markersize=6,
    markerfacecolor=PALETTE["sun"],
    markeredgecolor="white",
    alpha=0.95,
    label="Theoretical objective"
)

# Soft area fill
ax.fill_between(
    dfp["Week"],
    dfp["Weight (kg)"],
    color=PALETTE["mid"],
    alpha=0.15
)

# Axes & grille propres
ax.set_facecolor(PALETTE["panel"])
fig.patch.set_facecolor(PALETTE["panel"])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(PALETTE["grid"])
ax.spines["bottom"].set_color(PALETTE["grid"])
ax.grid(alpha=0.18, color=PALETTE["grid"], linewidth=0.8)

# >>> Clé: limites Y dynamiques (pas d’ancrage à zéro)
ax.set_ylim(y_min - pad, y_max + pad)

# Ticks semaines = entiers
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

ax.set_title("🏋️ Weight Projection", fontsize=14, fontweight="bold", color=PALETTE["deep"], pad=12)
ax.set_xlabel("Weeks", fontsize=11, color=PALETTE["muted"])
ax.set_ylabel("Weight (kg)", fontsize=11, color=PALETTE["muted"])
ax.legend(frameon=False)

st.pyplot(fig)


# Explanation
with st.expander("🧠 How it’s calculated"):
    st.markdown(
        "- **BMR (Mifflin–St Jeor)**: `10*weight + 6.25*height - 5*age + s` (s=5 for men / s=-161 for women)\n"
        "- **TDEE** = BMR × activity factor\n"
        "- **Required daily deficit** = `(loss(lbs) * 3500) / (weeks * 7)` (bounded between 300–900 kcal/day)\n"
        "- **Recommended intake** = TDEE − deficit\n"
        "- **Theoretical loss** = `(deficit*7)/7700` kg/week × number of weeks"
    )


