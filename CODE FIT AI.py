import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from datetime import date

# ==============
# Constants
# ==============
ACTIVITY_MULT = {
    "Sedentary": 1.20, "Lightly Active": 1.375, "Moderately Active": 1.55,
    "Very Active": 1.725, "Extra Active": 1.90,
    # FR aliases
    "Sédentaire": 1.20, "Légèrement actif": 1.375, "Modérément actif": 1.55,
    "Très actif": 1.725, "Extrêmement actif": 1.90,
}

PALETTE = {
    "deep": "#240046", "mid": "#7B2CBF", "accent": "#FF5E78", "sun": "#FFD100",
    "ink": "#222222", "muted": "#555555", "grid": "#DADCE0", "panel": "#F9F9FB",
}

# ==============
# Helpers
# ==============
def kg_to_lbs(x): return x * 2.2046226218

def bmr_mifflin_st_jeor(sex, age, height_cm, weight_kg):
    s = 5 if sex in ["Male", "M", "Homme", "male"] else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def adherence_level(deficit_kcal_per_day, weeks):
    score = 0.5 * min(deficit_kcal_per_day, 900) / 900 + 0.5 * min(weeks, 16) / 16
    if score < 0.40:
        return "Easy 🟢", "Objectif réaliste et durable."
    elif score < 0.70:
        return "Moderate 🟠", "Faisable avec régularité (attention aux écarts)."
    else:
        return "Challenging 🔴", "Ambitieux — réduis le déficit ou allonge la durée."

def plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level,
                min_deficit=300, max_deficit=900):
    bmr = bmr_mifflin_st_jeor(sex, age, height_cm, weight_start)
    tdee = bmr * ACTIVITY_MULT.get(activity_level, 1.55)

    target_loss_kg  = abs(weight_start - weight_goal)
    target_loss_lbs = kg_to_lbs(target_loss_kg)
    days = max(1, int(weeks * 7))

    # Déficit "requis" borné 300–900
    deficit_req = (target_loss_lbs * 3500) / days
    deficit_req = float(np.clip(deficit_req, min_deficit, max_deficit))

    # Plancher calorique (sécurité)
    min_intake = 1200 if sex in ["Female", "F", "Femme", "female"] else 1500
    calories_goal_raw = tdee - deficit_req
    calories_goal = max(calories_goal_raw, min_intake)

    # Déficit effectif (après plancher)
    effective_deficit = max(0.0, tdee - calories_goal)  # == min(deficit_req, TDEE - floor)
    floor_triggered = calories_goal > calories_goal_raw + 1e-9

    # Projection au rythme effectif
    physio_loss_per_week_kg = (effective_deficit * 7.0) / 7700.0
    physio_total_kg = physio_loss_per_week_kg * weeks

    weeks_needed_safe = (
        (target_loss_lbs * 3500) / max(effective_deficit, 1e-9) / 7.0
        if effective_deficit > 0 else float("inf")
    )

    level, msg = adherence_level(effective_deficit, weeks)

    return dict(
        bmr=bmr, tdee=tdee,
        deficit_req=deficit_req, deficit_eff=effective_deficit,
        kcal=calories_goal, min_intake=min_intake,
        target_loss_kg=target_loss_kg, physio_total_kg=physio_total_kg,
        weeks_needed_safe=weeks_needed_safe, floor_triggered=floor_triggered,
        level=level, comment=msg
    )

def projection_effective(weight_start, target_loss_kg, physio_total_kg, weeks):
    """Projection vers le poids atteignable au bout de N semaines (pas forcément le goal)."""
    achievable_loss = min(target_loss_kg, physio_total_kg)
    end_weight = weight_start - achievable_loss
    t = np.arange(0, int(np.ceil(weeks)) + 1)
    w = weight_start + (end_weight - weight_start) * (t / max(1, weeks))
    return pd.DataFrame({"Week": t, "Weight (kg)": w})

# ---- Tracking schema (évite le crash data_editor) ----
def ensure_tracking_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise le schema: Date (datetime64[ns]), Weight (float), Calories (float)."""
    if df is None:
        df = pd.DataFrame()
    out = pd.DataFrame()
    out["Date"] = pd.to_datetime(df.get("Date", pd.Series([], dtype="datetime64[ns]")), errors="coerce")
    out["Weight (kg)"] = pd.to_numeric(df.get("Weight (kg)", pd.Series([], dtype="float")), errors="coerce")
    out["Calories"] = pd.to_numeric(df.get("Calories", pd.Series([], dtype="float")), errors="coerce")
    return out[["Date", "Weight (kg)", "Calories"]]

# ---- “FAKE-IA” nutrition ----
def macro_split(calories, p_ratio=0.30, c_ratio=0.40, f_ratio=0.30):
    p_cal, c_cal, f_cal = calories * p_ratio, calories * c_ratio, calories * f_ratio
    return dict(protein_g=round(p_cal/4), carbs_g=round(c_cal/4), fat_g=round(f_cal/9))

def scaled_grams(target_cals, base_cals, grams):
    factor = target_cals / base_cals
    return {k: round(v * factor) for k, v in grams.items()}

TEMPLATES = [
    dict(
        name="Lean & Simple", base_cals=1600,
        meals=[
            ("Breakfast", "Skyr 0% 200g + oats 50g + banana 1", {"skyr_g":200,"oats_g":50,"banana":1}),
            ("Lunch", "Chicken 150g + quinoa 70g (dry) + veg", {"chicken_g":150,"quinoa_dry_g":70,"veg_serv":2}),
            ("Snack", "Cottage cheese 200g + berries 100g", {"cottage_g":200,"berries_g":100}),
            ("Dinner","Salmon 140g + rice 75g (dry) + salad + olive oil",
             {"salmon_g":140,"rice_dry_g":75,"olive_oil_tbsp":1,"salad_serv":2}),
        ],
        swaps=["Swap salmon ↔️ tofu 200g","Swap quinoa ↔️ whole-wheat pasta","Add 1 tbsp peanut butter if hunger"]
    ),
    dict(
        name="Balanced Med", base_cals=2000,
        meals=[
            ("Breakfast","Eggs 3 + whole bread 2 slices + fruit",{"eggs":3,"bread_slices":2,"fruit":1}),
            ("Lunch","Turkey 160g + couscous 90g (dry) + veg",{"turkey_g":160,"couscous_dry_g":90,"veg_serv":2}),
            ("Snack","Greek yogurt 250g + honey 10g + nuts 20g",{"yogurt_g":250,"honey_g":10,"nuts_g":20}),
            ("Dinner","Beef 150g + potatoes 300g + green beans",{"beef_g":150,"potatoes_g":300,"beans_serv":2}),
        ],
        swaps=["Honey ↔️ jam","Beef ↔️ chicken 170g","Add olive oil 1 tbsp if low on calories"]
    ),
    dict(
        name="High-Energy", base_cals=2400,
        meals=[
            ("Breakfast","Oats 80g + whey 30g + milk 300ml + berries",{"oats_g":80,"whey_g":30,"milk_ml":300,"berries_g":100}),
            ("Lunch","Pasta 110g (dry) + tuna 1 can + tomato sauce",{"pasta_dry_g":110,"tuna_can":1,"sauce_serv":1}),
            ("Snack","Protein bar + banana + almonds 25g",{"bar":1,"banana":1,"almonds_g":25}),
            ("Dinner","Chicken 200g + rice 100g (dry) + olive oil 1tbsp",{"chicken_g":200,"rice_dry_g":100,"olive_oil_tbsp":1,"veg_serv":2}),
        ],
        swaps=["Tuna ↔️ lentils 200g (cooked)","Almonds ↔️ cashews","Add parmesan 15g if needed"]
    ),
]

def pick_template(cal_target):
    idx = np.argmin([abs(cal_target - t["base_cals"]) for t in TEMPLATES])
    return TEMPLATES[idx]

def render_meal_plan(cal_target):
    macros = macro_split(cal_target)
    tpl = pick_template(cal_target)
    st.subheader(f"🍽️ Plan auto pour ~{int(cal_target)} kcal/j")
    st.caption(f"Template: **{tpl['name']}** (scalé depuis {tpl['base_cals']} kcal) • "
               f"≈ {macros['protein_g']}g P / {macros['carbs_g']}g C / {macros['fat_g']}g F")

    for title, desc, grams in tpl["meals"]:
        scaled = scaled_grams(cal_target, tpl["base_cals"], grams)
        st.markdown(f"**{title}** — {desc}")
        st.code("\n".join([f"- {k}: {v}" for k, v in scaled.items()]))

    with st.expander("Swaps & tips"):
        for s in tpl["swaps"]:
            st.write(f"• {s}")
        st.write("• Protéines ≈ 1.6–2.2 g/kg de poids de corps. Ajuste si training ↑.")

# ==============
# App
# ==============
st.set_page_config(page_title="FitPath — Physiological MVP", page_icon="🏋️", layout="centered")
st.markdown(f"""
<style>
  .stApp {{ background: {PALETTE['panel']}; }}
  h1, h2, h3 {{ color: {PALETTE['deep']} !important; }}
  .metric-value, .metric-label {{ color: {PALETTE['ink']} !important; }}
  .st-emotion-cache-ue6h4q {{ color: {PALETTE['muted']} !important; }}
</style>
""", unsafe_allow_html=True)

st.title("🏋️ FitPath — Physiological MVP")
st.caption("BMR → TDEE → Deficit → Calories → Projection • Fake-AI meal plans • Progress tracking")

# Sidebar (global inputs)
with st.sidebar:
    st.header("User Settings")
    sex = st.selectbox("Gender", ["Male", "Female"])
    age = st.number_input("Age", 18, 80, 26)
    height_cm = st.number_input("Height (cm)", 140, 210, 180)
    weight_start = st.number_input("Current weight (kg)", 40.0, 200.0, 200.0, step=0.5)
    weight_goal = st.number_input("Target weight (kg)", 40.0, 200.0, 79.0, step=0.5)
    weeks = st.number_input("Duration (weeks)", 1, 52, 8)
    activity_level = st.selectbox("Activity level",
                                  ["Sedentary","Lightly Active","Moderately Active","Very Active","Extra Active"])

# Calculs
out = plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level)
dfp = projection_effective(weight_start, out["target_loss_kg"], out["physio_total_kg"], weeks)  # dispo pour onglet 3

# Onglets
tab1, tab2, tab3 = st.tabs(["Plan", "Nutrition (auto)", "Suivi"])

# ---- Tab 1: Plan ----
with tab1:
    st.subheader("📊 Plan Summary")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("BMR (kcal/day)", f"{out['bmr']:.0f}")
        st.metric("TDEE (kcal/day)", f"{out['tdee']:.0f}")
    with c2:
        suffix = " (capped)" if out["floor_triggered"] else ""
        st.metric(f"Deficit (kcal/day){suffix}", f"{out['deficit_eff']:.0f}")
        st.metric("Recommended intake (kcal/day)", f"{out['kcal']:.0f}")

    st.write(f"**Target loss:** {out['target_loss_kg']:.1f} kg over {weeks} weeks")
    st.write(f"**Theoretical loss at safe intake:** {out['physio_total_kg']:.1f} kg")

    if out["floor_triggered"]:
        weeks_txt = (f"~**{out['weeks_needed_safe']:.1f} weeks**"
                     if np.isfinite(out["weeks_needed_safe"]) else "**unattainable at this intake**")
        st.warning(
            f"Required deficit **{out['deficit_req']:.0f} kcal/day** > safe limit. "
            f"Effective deficit **{out['deficit_eff']:.0f} kcal/day** at **{out['kcal']:.0f} kcal**. "
            f"{weeks_txt} needed to hit the target."
        )

    st.info(f"**Feasibility:** {out['level']} — {out['comment']}")

    # Chart
    y = dfp["Weight (kg)"].values
    y_min, y_max = float(y.min()), float(y.max())
    pad = max(0.5, (y_max - y_min) * 0.15)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dfp["Week"], dfp["Weight (kg)"],
            color=PALETTE["accent"], linewidth=3, marker="o",
            markersize=6, markerfacecolor=PALETTE["sun"],
            markeredgecolor="white", alpha=0.95, label="Projection (achievable)")
    ax.fill_between(dfp["Week"], dfp["Weight (kg)"], color=PALETTE["mid"], alpha=0.15)

    ax.set_facecolor(PALETTE["panel"]); fig.patch.set_facecolor(PALETTE["panel"])
    for sside in ("top","right"): ax.spines[sside].set_visible(False)
    ax.spines["left"].set_color(PALETTE["grid"]); ax.spines["bottom"].set_color(PALETTE["grid"])
    ax.grid(alpha=0.18, color=PALETTE["grid"], linewidth=0.8)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title("🏋️ Weight Projection", fontsize=14, fontweight="bold", color=PALETTE["deep"], pad=12)
    ax.set_xlabel("Weeks", fontsize=11, color=PALETTE["muted"])
    ax.set_ylabel("Weight (kg)", fontsize=11, color=PALETTE["muted"])
    ax.legend(frameon=False)

    goal_reached = out["physio_total_kg"] + 1e-6 >= out["target_loss_]()_

