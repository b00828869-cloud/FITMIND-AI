# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from datetime import date

# =========================
# Constants & Helpers
# =========================
ACTIVITY_MULT = {
    "Sedentary": 1.20,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extra Active": 1.90,
    # FR aliases
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

def plan_physio(
    sex, age, height_cm, weight_start, weight_goal, weeks, activity_level,
    min_deficit=300, max_deficit=900
):
    bmr = bmr_mifflin_st_jeor(sex, age, height_cm, weight_start)
    tdee = bmr * ACTIVITY_MULT.get(activity_level, 1.55)

    target_loss_kg  = abs(weight_start - weight_goal)
    target_loss_lbs = kg_to_lbs(target_loss_kg)
    days = max(1, int(weeks * 7))

    deficit_req = (target_loss_lbs * 3500) / days
    deficit_req = float(np.clip(deficit_req, min_deficit, max_deficit))

    min_intake = 1200 if sex in ["Female", "F", "Femme", "female"] else 1500
    calories_goal_raw = tdee - deficit_req
    calories_goal = max(calories_goal_raw, min_intake)

    effective_deficit = max(0.0, tdee - calories_goal)  # == min(deficit_req, TDEE - floor)
    floor_triggered = calories_goal > calories_goal_raw + 1e-9

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
        weeks_needed_safe=weeks_needed_safe,
        floor_triggered=floor_triggered,
        level=level, comment=msg
    )

def projection_effective(weight_start, target_loss_kg, physio_total_kg, weeks):
    achievable_loss = min(target_loss_kg, physio_total_kg)
    end_weight = weight_start - achievable_loss
    t = np.arange(0, int(np.ceil(weeks)) + 1)
    w = weight_start + (end_weight - weight_start) * (t / max(1, weeks))
    return pd.DataFrame({"Week": t, "Weight (kg)": w})

# ---------- “Fake-IA” Nutrition ----------
def macro_split(calories, p_ratio=0.3, c_ratio=0.4, f_ratio=0.3):
    p_cal = calories * p_ratio
    c_cal = calories * c_ratio
    f_cal = calories * f_ratio
    return dict(
        protein_g = round(p_cal / 4),
        carbs_g   = round(c_cal / 4),
        fat_g     = round(f_cal / 9),
    )

def scaled_grams(target_cals, base_cals, grams):
    # scale grams per meal from a template to match target calories
    factor = target_cals / base_cals
    return {k: round(v * factor) for k, v in grams.items()}

TEMPLATES = [
    # base around 1600 kcal
    dict(
        name="Lean & Simple",
        base_cals=1600,
        meals=[
            ("Breakfast",  "Skyr 0% 200g + oats 50g + banana 1",             {"skyr_g":200, "oats_g":50, "banana":1}),
            ("Lunch",      "Chicken 150g + quinoa 70g (dry) + veggies",       {"chicken_g":150, "quinoa_dry_g":70, "veg_serv":2}),
            ("Snack",      "Cottage cheese 200g + berries 100g",              {"cottage_g":200, "berries_g":100}),
            ("Dinner",     "Salmon 140g + rice 75g (dry) + salad + olive oil",{"salmon_g":140, "rice_dry_g":75, "olive_oil_tbsp":1, "salad_serv":2}),
        ],
        swaps=[
            "Swap salmon ↔️ tofu 200g",
            "Swap quinoa ↔️ whole-wheat pasta",
            "Add 1 tbsp peanut butter if hunger"
        ]
    ),
    # base around 2000 kcal
    dict(
        name="Balanced Med",
        base_cals=2000,
        meals=[
            ("Breakfast",  "Eggs 3 + whole bread 2 slices + fruit",           {"eggs":3, "bread_slices":2, "fruit":1}),
            ("Lunch",      "Turkey 160g + couscous 90g (dry) + veg",          {"turkey_g":160, "couscous_dry_g":90, "veg_serv":2}),
            ("Snack",      "Greek yogurt 250g + honey 10g + nuts 20g",        {"yogurt_g":250, "honey_g":10, "nuts_g":20}),
            ("Dinner",     "Beef 150g + potatoes 300g + green beans",         {"beef_g":150, "potatoes_g":300, "beans_serv":2}),
        ],
        swaps=[
            "Honey ↔️ jam",
            "Beef ↔️ chicken 170g",
            "Add olive oil 1 tbsp if low on calories"
        ]
    ),
    # base around 2400 kcal
    dict(
        name="High-Energy",
        base_cals=2400,
        meals=[
            ("Breakfast",  "Oats 80g + whey 30g + milk 300ml + berries",      {"oats_g":80, "whey_g":30, "milk_ml":300, "berries_g":100}),
            ("Lunch",      "Pasta 110g (dry) + tuna 1 can + tomato sauce",    {"pasta_dry_g":110, "tuna_can":1, "sauce_serv":1}),
            ("Snack",      "Protein bar + banana + almonds 25g",               {"bar":1, "banana":1, "almonds_g":25}),
            ("Dinner",     "Chicken 200g + rice 100g (dry) + olive oil 1tbsp", {"chicken_g":200, "rice_dry_g":100, "olive_oil_tbsp":1, "veg_serv":2}),
        ],
        swaps=[
            "Tuna ↔️ lentils 200g (cooked)",
            "Almonds ↔️ cashews",
            "Add parmesan 15g if needed"
        ]
    ),
]

def pick_template(cal_target):
    # choose the closest base_cals
    idx = np.argmin([abs(cal_target - t["base_cals"]) for t in TEMPLATES])
    return TEMPLATES[idx]

def render_meal_plan(cal_target):
    macros = macro_split(cal_target)
    tpl = pick_template(cal_target)
    st.subheader(f"🍽️ ‘AI-style’ plan for ~{int(cal_target)} kcal/day")
    st.caption(f"Template: **{tpl['name']}** (scaled from {tpl['base_cals']} kcal) • Macro target ≈ "
               f"{macros['protein_g']}g P / {macros['carbs_g']}g C / {macros['fat_g']}g F")

    for title, desc, grams in tpl["meals"]:
        scaled = scaled_grams(cal_target, tpl["base_cals"], grams)
        st.markdown(f"**{title}** — {desc}")
        st.code("\n".join([f"- {k}: {v}" for k, v in scaled.items()]))

    with st.expander("Swaps & Tips"):
        for s in tpl["swaps"]:
            st.write(f"• {s}")
        st.write("• Protein ≈ 1.6–2.2 g/kg bodyweight. Adjust portions if training volume ↑.")

# =========================
# Streamlit App Skeleton
# =========================
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
    weight_start = st.number_input("Current weight (kg)", 40.0, 200.0, 84.0, step=0.5)
    weight_goal = st.number_input("Target weight (kg)", 40.0, 200.0, 79.0, step=0.5)
    weeks = st.number_input("Duration (weeks)", 1, 52, 8)
    activity_level = st.selectbox(
        "Activity level",
        ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"]
    )

out = plan_physio(sex, age, height_cm, weight_start, weight_goal, weeks, activity_level)

# Tabs = 3 “pages”
tab1, tab2, tab3 = st.tabs(["Plan", "Nutrition (fake-AI)", "Suivi"])

# ---------- Tab 1: Plan ----------
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
        st.warning(
            f"Required deficit **{out['deficit_req']:.0f} kcal/day** > safe limit. "
            f"Effective deficit **{out['deficit_eff']:.0f} kcal/day** at **{out['kcal']:.0f} kcal**. "
            f"~**{out['weeks_needed_safe']:.1f} weeks** needed to hit the target at this pace."
        )

    st.info(f"**Feasibility:** {out['level']} — {out['comment']}")

    # Chart: projection to achievable weight
    dfp = projection_effective(weight_start, out["target_loss_kg"], out["physio_total_kg"], weeks)
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

    goal_reached = out["physio_total_kg"] + 1e-6 >= out["target_loss_kg"]
    if not goal_reached:
        ax.text(0.02, 0.02,
                f"Goal not reachable in {weeks} weeks at safe intake.\n~{out['weeks_needed_safe']:.1f} weeks needed.",
                transform=ax.transAxes, fontsize=10, color=PALETTE["mid"])
    st.pyplot(fig)

    with st.expander("🧠 How it’s calculated"):
        st.markdown(
            "- **BMR (Mifflin–St Jeor)**: `10*weight + 6.25*height - 5*age + s` (s=+5 men / −161 women)\n"
            "- **TDEE** = BMR × activity factor\n"
            "- **Required daily deficit** = `(loss(lbs)*3500)/(weeks*7)` → bounded 300–900 kcal/day\n"
            "- **Safety floor** = 1500 kcal (men) / 1200 kcal (women)\n"
            "- **Effective deficit** = `min(required_deficit, TDEE - floor)`\n"
            "- **Loss estimate** = `(def_eff*7)/7700` kg/week • chart → achievable end weight."
        )

# ---------- Tab 2: Nutrition (fake-AI) ----------
with tab2:
    st.subheader("🍽️ Meal plans (auto)")
    st.caption("On ‘fait comme si’ un LLM générait ton plan. Ici on assemble un plan par tranches caloriques.")
    st.write(f"**Recommended intake:** ~**{int(out['kcal'])} kcal/j**")

    # Choix de la tranche (auto proposée, modifiable)
    bins = [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800]
    close = min(bins, key=lambda b: abs(b - out["kcal"]))
    cal_target = st.slider("Daily calories for the plan", min_value=1200, max_value=3000,
                           value=int(close), step=100, help="Ajuste si tu veux plus/moins.")
    render_meal_plan(cal_target)

# ---------- Tab 3: Suivi ----------
with tab3:
    st.subheader("📈 Suivi & comparaison")
    st.caption("Entre tes mesures (poids, calories…) et compare à la projection.")

    # init state
    if "tracking_df" not in st.session_state:
        st.session_state.tracking_df = pd.DataFrame(columns=["Date","Weight (kg)","Calories"])

    with st.expander("Importer un CSV (colonnes: Date, Weight (kg), Calories)"):
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up is not None:
            try:
                dfu = pd.read_csv(up)
                # basic normalization
                if "Date" in dfu.columns:
                    dfu["Date"] = pd.to_datetime(dfu["Date"]).dt.date
                st.session_state.tracking_df = dfu[["Date","Weight (kg)","Calories"]].copy()
                st.success("Import ok.")
            except Exception as e:
                st.error(f"CSV illisible: {e}")

    st.write("Ajoute/modifie tes lignes ci-dessous :")
    edited = st.data_editor(
        st.session_state.tracking_df,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.DateColumn(default=date.today()),
            "Weight (kg)": st.column_config.NumberColumn(step=0.1, format="%.1f"),
            "Calories": st.column_config.NumberColumn(step=10, format="%.0f"),
        },
        key="editor"
    )
    st.session_state.tracking_df = edited

    # Courbes : poids réel vs projection
    if not edited.empty:
        df_plot = edited.dropna(subset=["Date","Weight (kg)"]).copy()
        df_plot["Day"] = (pd.to_datetime(df_plot["Date"]) - pd.to_datetime(df_plot["Date"].min())).dt.days
        # Convertir jour→semaine pour l’overlay (approx.)
        df_plot["Week"] = df_plot["Day"] / 7.0

        # projection (tab1) déjà calculée → dfp
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(dfp["Week"], dfp["Weight (kg)"], linewidth=3, label="Projection (achievable)")
        ax2.scatter(df_plot["Week"], df_plot["Weight (kg)"], s=35, label="Actual", zorder=3)

        ax2.set_facecolor(PALETTE["panel"]); fig2.patch.set_facecolor(PALETTE["panel"])
        for sside in ("top","right"): ax2.spines[sside].set_visible(False)
        ax2.spines["left"].set_color(PALETTE["grid"]); ax2.spines["bottom"].set_color(PALETTE["grid"])
        ax2.grid(alpha=0.18, color=PALETTE["grid"], linewidth=0.8)
        ax2.set_title("Weight: Actual vs Projection", fontsize=14, fontweight="bold", color=PALETTE["deep"], pad=12)
        ax2.set_xlabel("Weeks", fontsize=11, color=PALETTE["muted"])
        ax2.set_ylabel("Weight (kg)", fontsize=11, color=PALETTE["muted"])
        ax2.legend(frameon=False)
        st.pyplot(fig2)

    # Petit récap calories vs cible
    if not edited.empty:
        avg_cal = edited["Calories"].dropna().mean() if "Calories" in edited else np.nan
        if np.isfinite(avg_cal):
            delta = avg_cal - out["kcal"]
            signe = "au dessus" if delta > 0 else "en dessous"
            st.info(f"Apport moyen: **{avg_cal:.0f} kcal/j** ({abs(delta):.0f} kcal {signe} de la cible **{out['kcal']:.0f}**).")

