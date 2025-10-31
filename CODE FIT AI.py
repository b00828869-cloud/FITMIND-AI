import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# =========================
# Constants & Helpers
# =========================
ACTIVITY_MULT = {
    "Sedentary": 1.20,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extra Active": 1.90,
    # Alias FR
    "Sédentaire": 1.20,
    "Légèrement actif": 1.375,
    "Modérément actif": 1.55,
    "Très actif": 1.725,
    "Extrêmement actif": 1.90,
}

PALETTE = {
    "deep": "#240046",
    "mid": "#7B2CBF",
    "accent": "#FF5E78",
    "sun": "#FFD100",
    "ink": "#222222",
    "muted": "#555555",
    "grid": "#DADCE0",
    "panel": "#F9F9FB",
}

def kg_to_lbs(x): return x * 2.2046226218

def bmr_mifflin_st_jeor(sex, age, height_cm, weight_kg):
    """Mifflin–St Jeor: 10w + 6.25h − 5a + s (s=+5 men / −161 women)"""
    s = 5 if sex in ["Male", "M", "Homme", "male"] else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def adherence_level(deficit_kcal_per_day, weeks):
    """Indice simple de charge perçue, pour colorer le feedback."""
    score = 0.5 * min(deficit_kcal_per_day, 900) / 900 + 0.5 * min(weeks, 16) / 16
    if score < 0.40:
        return "Easy 🟢", "Objectif réaliste et durable."
    elif score < 0.70:
        return "Moderate 🟠", "Faisable avec régularité (attention aux écarts)."
    else:
        return "Challenging 🔴", "Ambitieux — réduis le déficit ou allonge la durée."

def plan_physio(
    sex, age, height_cm, weight_start, weight_goal, weeks, activity_level,
    min_deficit=300, max_deficit=900
):
    """Calcule BMR, TDEE, déficit requis & effectif (plancher calorique), projections."""
    bmr = bmr_mifflin_st_jeor(sex, age, height_cm, weight_start)
    tdee = bmr * ACTIVITY_MULT.get(activity_level, 1.55)

    target_loss_kg  = abs(weight_start - weight_goal)
    target_loss_lbs = kg_to_lbs(target_loss_kg)
    days = max(1, int(weeks * 7))

    # Déficit "requis" par objectif/temps, borné 300–900
    deficit_req = (target_loss_lbs * 3500) / days
    deficit_req = float(np.clip(deficit_req, min_deficit, max_deficit))

    # Plancher calorique
    min_intake = 1200 if sex in ["Female", "F", "Femme", "female"] else 1500
    calories_goal_raw = tdee - deficit_req
    calories_goal = max(calories_goal_raw, min_intake)

    # Déficit effectif après plancher
    effective_deficit = max(0.0, tdee - calories_goal)  # == min(def_req, TDEE - floor)
    floor_triggered = calories_goal > calories_goal_raw + 1e-9

    # Perte théorique au déficit effectif
    physio_loss_per_week_kg = (effective_deficit * 7.0) / 7700.0
    physio_total_kg = physio_loss_per_week_kg * weeks

    # Durée nécessaire si on garde ce rythme "safe"
    weeks_needed_safe = (
        (target_loss_lbs * 3500) / max(effective_deficit, 1e-9) / 7.0
        if effective_deficit > 0 else float("inf")
    )

    level, msg = adherence_level(effective_deficit, weeks)

    return dict(
        bmr=bmr, tdee=tdee,
        deficit_req=deficit_req,
        deficit_eff=effective_deficit,
        kcal=calories_goal, min_intake=min_intake,
        target_loss_kg=target_loss_kg, physio_total_kg=physio_total_kg,
        weeks_needed_safe=weeks_needed_safe,
        floor_triggered=floor_triggered,
        level=level, comment=msg
    )

def projection_effective(weight_start, target_loss_kg, physio_total_kg, weeks):
    """Projection linéaire vers le poids atteignable au bout de N semaines (pas forcément le goal)."""
    achievable_loss = min(target_loss_kg, physio_total_kg)
    end_weight = weight_start - achievable_loss
    t = np.arange(0, int(np.ceil(weeks)) + 1)
    w = weight_start + (end_weight - weight_start) * (t / max(1, weeks))
    return pd.DataFrame({"Week": t, "Weight (kg)": w})

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="FitPath — Physiological MVP", page_icon="🏋️", layout="centered")

# Un peu de style
st.markdown(f"""
<style>
  .stApp {{ background: {PALETTE['panel']}; }}
  h1, h2, h3 {{ color: {PALETTE['deep']} !important; }}
  .metric-value, .metric-label {{ color: {PALETTE['ink']} !important; }}
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

# Compute plan
out = plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level)

# Summary metrics
st.subheader("📊 Plan Summary")
col1, col2 = st.columns(2)
with col1:
    st.metric("BMR (kcal/day)", f"{out['bmr']:.0f}")
    st.metric("TDEE (kcal/day)", f"{out['tdee']:.0f}")
with col2:
    suffix = " (capped)" if out["floor_triggered"] else ""
    st.metric(f"Deficit (kcal/day){suffix}", f"{out['deficit_eff']:.0f}")
    st.metric("Recommended intake (kcal/day)", f"{out['kcal']:.0f}")

st.write(f"**Target loss:** {out['target_loss_kg']:.1f} kg over {weeks} weeks")
st.write(f"**Theoretical loss at safe intake:** {out['physio_total_kg']:.1f} kg")

if out["floor_triggered"]:
    st.warning(
        f"The required deficit was **{out['deficit_req']:.0f} kcal/day**, "
        f"but intake is capped at **{out['min_intake']} kcal/day** → effective deficit **{out['deficit_eff']:.0f} kcal/day**. "
        f"At this pace, reaching the target would take about **{out['weeks_needed_safe']:.1f} weeks**. "
        "Consider extending the duration or increasing activity."
    )

st.info(f"**Feasibility:** {out['level']} — {out['comment']}")

# =========================
# Chart (zoomed Y, pas d’ancrage à 0)
# =========================
dfp = projection_effective(weight_start, out["target_loss_kg"], out["physio_total_kg"], weeks)
y = dfp["Weight (kg)"].values
y_min, y_max = float(y.min()), float(y.max())
pad = max(0.5, (y_max - y_min) * 0.15)

fig, ax = plt.subplots(figsize=(8, 4))
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
    label="Projection (achievable)"
)
ax.fill_between(dfp["Week"], dfp["Weight (kg)"], color=PALETTE["mid"], alpha=0.15)

ax.set_facecolor(PALETTE["panel"])
fig.patch.set_facecolor(PALETTE["panel"])
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.spines["left"].set_color(PALETTE["grid"])
ax.spines["bottom"].set_color(PALETTE["grid"])
ax.grid(alpha=0.18, color=PALETTE["grid"], linewidth=0.8)

# Y dynamique + ticks X entiers
ax.set_ylim(y_min - pad, y_max + pad)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

ax.set_title("🏋️ Weight Projection", fontsize=14, fontweight="bold", color=PALETTE["deep"], pad=12)
ax.set_xlabel("Weeks", fontsize=11, color=PALETTE["muted"])
ax.set_ylabel("Weight (kg)", fontsize=11, color=PALETTE["muted"])
ax.legend(frameon=False)

# Annotation si objectif non atteignable dans la durée
goal_reached = np.isclose(out["physio_total_kg"], out["target_loss_kg"], atol=1e-6) or (out["physio_total_kg"] >= out["target_loss_kg"])
if not goal_reached:
    ax.text(
        0.02, 0.02,
        f"Goal not reachable in {weeks} weeks at safe intake.\n~{out['weeks_needed_safe']:.1f} weeks needed.",
        transform=ax.transAxes,
        fontsize=10, color=PALETTE["mid"]
    )

st.pyplot(fig)

# =========================
# Notes de calcul
# =========================
with st.expander("🧠 How it’s calculated"):
    st.markdown(
        "- **BMR (Mifflin–St Jeor)**: `10*weight + 6.25*height - 5*age + s` (s=+5 men / −161 women)\n"
        "- **TDEE** = BMR × activity factor\n"
        "- **Required daily deficit** = `(loss(lbs)*3500)/(weeks*7)` → bounded 300–900 kcal/day\n"
        "- **Safety floor** = 1500 kcal (men) / 1200 kcal (women)\n"
        "- **Effective deficit** = `min(required_deficit, TDEE - floor)`\n"
        "- **Loss estimate** = `(def_eff*7)/7700` kg/week, then × weeks\n"
        "- Chart projects to the **achievable** end weight in the chosen duration."
    )
