import math
import datetime as dt
import streamlit as st

# =========================
# Helpers & state
# =========================
st.set_page_config(page_title="FitMind AI", page_icon="💪", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "home"

if "goals" not in st.session_state:
    st.session_state.goals = []  # list of dicts

def goto(page: str):
    st.session_state.page = page

def new_goal_id():
    return (max([g["id"] for g in st.session_state.goals], default=0) + 1)

def bmi_value(weight_kg: float, height_m: float) -> float:
    return weight_kg / (height_m ** 2)

def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "UNDERWEIGHT"
    elif bmi < 25:
        return "NORMAL"
    elif bmi < 30:
        return "OVERWEIGHT"
    elif bmi < 40:
        return "OBESE"
    else:
        return "SEVERELY OBESE"

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# Rough TDEE estimate (very simplified if age/sex/activity unknown)
def estimate_tdee(weight, height, age, sex, activity):
    # Mifflin-St Jeor
    if sex == "Male":
        bmr = 10*weight + 6.25*(height*100) - 5*age + 5
    else:
        bmr = 10*weight + 6.25*(height*100) - 5*age - 161
    factor = {
        "Low (1–2x/week)": 1.375,
        "Moderate (3–4x/week)": 1.55,
        "High (5+ /week)": 1.725
    }.get(activity, 1.55)
    return round(bmr * factor)

def weekly_schedule_header():
    st.markdown("#### 📅 Your Week at a Glance")

def render_week_table(plan_days):
    # plan_days: list of (day, activity, notes)
    for d, act, note in plan_days:
        st.markdown(f"**{d}:** {act}  \n{note}")

# =========================
# Generators (core logic)
# =========================
def generate_weight_loss_plan(weight, height, age, sex, activity, target_loss_kg, weeks):
    bmi = bmi_value(weight, height)
    tdee = estimate_tdee(weight, height, age, sex, activity)

    # Pace recommendation
    max_safe_rate = 1.0  # kg/week upper guidance
    rate = clamp(target_loss_kg / max(weeks, 1), 0.3, max_safe_rate)
    daily_deficit = int(rate * 7700 / 7)  # ~7700 kcal per kg
    target_cal = max(1200 if sex == "Female" else 1400, tdee - daily_deficit)

    macros = "≈ 40% carbs / 30% protein / 30% fat"
    if rate >= 0.9:
        caution = "Your requested pace is aggressive; consider extending duration or increasing steps."
    else:
        caution = "Steady, sustainable pace. Focus on adherence and sleep quality."

    plan_days = [
        ("Mon", "Strength (Full Body) 45′ + 6k steps",
         "Squat, push, hinge, pull, core. RPE 6–7."),
        ("Tue", "Cardio Z2 30–40′ + mobility 10′",
         "Comfortable pace; you should be able to talk."),
        ("Wed", "Steps 8–10k + optional core 15′",
         "Planks, dead bug, side plank."),
        ("Thu", "Strength (Upper) 45′ + 6k steps",
         "Press, row, lateral raise, triceps."),
        ("Fri", "Intervals Cardio 20–25′ (5×2′ hard/2′ easy)",
         "Warm up 8′, cool down 7′."),
        ("Sat", "Active recovery: walk 60′ / swim / bike easy",
         "Hydration, sunlight, stretching."),
        ("Sun", "Rest or gentle yoga 20′",
         "Meal prep for next week.")
    ]

    nutrition_day = [
        ("Breakfast", "Oats + Greek yogurt + berries + nuts", "≈ 450 kcal"),
        ("Lunch", "Chicken, rice, veggies, olive oil", "≈ 550 kcal"),
        ("Snack", "Fruit + cottage cheese", "≈ 200 kcal"),
        ("Dinner", "Salmon, quinoa, broccoli", "≈ 600 kcal"),
    ]

    return {
        "type": "Weight Loss",
        "bmi": round(bmi, 1),
        "bmi_cat": bmi_category(bmi),
        "tdee": tdee,
        "target_kcal": target_cal,
        "macros": macros,
        "pace_kg_per_week": round(rate, 2),
        "deficit_per_day": daily_deficit,
        "weeks": weeks,
        "target_loss": target_loss_kg,
        "notes": caution,
        "week_plan": plan_days,
        "nutrition_example": nutrition_day
    }

def generate_muscle_gain_plan(weight, height, age, sex, activity, target_gain_kg, weeks):
    bmi = bmi_value(weight, height)
    tdee = estimate_tdee(weight, height, age, sex, activity)
    rate = clamp(target_gain_kg / max(weeks, 1), 0.2, 0.5)  # kg/week
    daily_surplus = int(rate * 7700 / 7 * 0.6)  # muscle accretion less energy-efficient
    target_cal = tdee + daily_surplus
    protein = round(max(1.6, min(2.2, 1.8)) * weight)  # g/day guideline

    plan_days = [
        ("Mon", "Push (Chest/Shoulders/Triceps) 60′", "8–12 reps, 3–4 sets, RPE 7–8."),
        ("Tue", "Pull (Back/Biceps) 60′", "Rows, pulldowns, curls; tempo control."),
        ("Wed", "Legs + Core 60′", "Squats/hinge, lunges, calves, core."),
        ("Thu", "Rest or light cardio 20–30′", "Steps 7–8k."),
        ("Fri", "Upper Hypertrophy 60′", "Higher volume, machines ok."),
        ("Sat", "Legs Hypertrophy 60′", "Moderate load, more sets."),
        ("Sun", "Rest & mobility 20′", "Sleep 7.5–9h.")
    ]

    nutrition_day = [
        ("Breakfast", "Eggs + toast + avocado + fruit", "≈ 600 kcal | 35–40g protein"),
        ("Lunch", "Beef/poultry + rice/pasta + veggies", "≈ 750 kcal | 40–50g protein"),
        ("Snack", "Skyr + banana + almonds", "≈ 350 kcal | 25g protein"),
        ("Dinner", "Fish + potatoes + salad + olive oil", "≈ 700 kcal | 40g protein"),
        ("Post-workout", "Whey + milk/water", "25–30g protein"),
    ]

    return {
        "type": "Muscle Gain",
        "bmi": round(bmi, 1),
        "bmi_cat": bmi_category(bmi),
        "tdee": tdee,
        "target_kcal": target_cal,
        "protein_g": protein,
        "pace_kg_per_week": round(rate, 2),
        "surplus_per_day": daily_surplus,
        "weeks": weeks,
        "target_gain": target_gain_kg,
        "week_plan": plan_days,
        "nutrition_example": nutrition_day,
        "notes": "Prioritize progressive overload, protein distribution (4 meals), and sleep."
    }

def generate_endurance_plan(weight, height, age, sex, activity, target_event, weeks, sessions_per_week):
    bmi = bmi_value(weight, height)
    tdee = estimate_tdee(weight, height, age, sex, activity)

    # Simple 3-zone template
    z2 = "Zone 2 (easy, conversational)"
    tempo = "Tempo (comfortably hard)"
    intervals = "Intervals (short hard reps)"
    longrun = "Long easy run"

    # Build a simple weekly skeleton
    plan_days = [
        ("Mon", "Rest or mobility 20′", "Foam roll + hips/ankles."),
        ("Tue", f"{intervals} 6×2′/2′ + warmup/cooldown", "RPE 8; technique focus."),
        ("Wed", f"{z2} 30–40′", "Breathing control, nasal ok."),
        ("Thu", f"{tempo} 20′ block", "RPE 7; even pacing."),
        ("Fri", "Rest or cross-training (bike/swim) 30′", "Low impact."),
        ("Sat", f"{longrun} 50–70′", "Fuel & hydrate."),
        ("Sun", f"{z2} 30′ + strides 6×15s", "Form drills optional."),
    ]

    return {
        "type": "Endurance",
        "bmi": round(bmi, 1),
        "bmi_cat": bmi_category(bmi),
        "tdee": tdee,
        "sessions_per_week": sessions_per_week,
        "target_event": target_event,
        "weeks": weeks,
        "week_plan": plan_days,
        "nutrition_example": [
            ("Pre-workout", "Banana + water/electrolytes", ""),
            ("During long", "Sip water; 30–50g carbs/h if >60′", ""),
            ("Post", "Protein 25–30g + carbs 1g/kg", "")
        ],
        "notes": "Progress volume by ~10%/week; add cutback week every 3–4 weeks."
    }

def generate_lifestyle_plan(weight, height, age, sex, activity, focus, weeks):
    bmi = bmi_value(weight, height)
    tdee = estimate_tdee(weight, height, age, sex, activity)

    habits = [
        ("Sleep", "7.5–9h / night, consistent schedule"),
        ("Hydration", "≈ 30–35 ml/kg/day; more on training days"),
        ("Steps", "8–10k steps/day baseline"),
        ("Meals", "3–4 anchors / day; whole foods first"),
        ("Screen-off", "No screens 45′ before bed"),
    ]
    plan_days = [
        ("Mon", "Walk 30–40′ + mobility 10′", "Focus posture & hips."),
        ("Tue", "Strength basics 30′", "Squat, push, hinge, pull."),
        ("Wed", "Mindfulness 10′ + steps 8k", "Low intensity."),
        ("Thu", "Cardio easy 25–30′", "Bike/run/swim as you like."),
        ("Fri", "Strength basics 30′", "Core + glutes."),
        ("Sat", "Outdoor activity 60′", "Hike, ride, team sport."),
        ("Sun", "Plan next week + groceries", "Batch cook 2 proteins.")
    ]
    return {
        "type": "Lifestyle",
        "bmi": round(bmi, 1),
        "bmi_cat": bmi_category(bmi),
        "tdee": tdee,
        "focus": focus,
        "weeks": weeks,
        "habits": habits,
        "week_plan": plan_days,
        "nutrition_example": [
            ("Breakfast", "Protein + fiber + fruit", ""),
            ("Lunch", "Protein + starch + veg + fat", ""),
            ("Dinner", "Same template; avoid heavy late meals", ""),
        ],
        "notes": "Pick 2–3 habits only; track daily with a simple checkbox."
    }

# =========================
# Pages
# =========================
def page_home():
    st.title("FitMind AI")
    st.caption("Your personalized fitness companion. Start from your goal — we’ll design the plan.")

    st.markdown("### Choose a goal")
    cols = st.columns(2)
    with cols[0]:
        if st.button("🔥 Lose Weight"):
            st.session_state["new_goal_type"] = "Weight Loss"
            goto("create_goal")
        if st.button("🏃 Improve Endurance"):
            st.session_state["new_goal_type"] = "Endurance"
            goto("create_goal")
    with cols[1]:
        if st.button("💪 Build Muscle"):
            st.session_state["new_goal_type"] = "Muscle Gain"
            goto("create_goal")
        if st.button("🌿 Rebalance Lifestyle"):
            st.session_state["new_goal_type"] = "Lifestyle"
            goto("create_goal")

    st.divider()
    st.markdown("### Your goals")
    if not st.session_state.goals:
        st.info("No goals yet. Create one above.")
    else:
        for g in st.session_state.goals:
            with st.container(border=True):
                st.markdown(f"**{g['title']}** · *{g['type']}*")
                st.write(f"Created: {g['created'].strftime('%Y-%m-%d')}  |  BMI: {g['plan']['bmi']} ({g['plan']['bmi_cat']})")
                if st.button(f"Open: {g['title']}", key=f"open_{g['id']}"):
                    st.session_state["open_goal_id"] = g["id"]
                    goto("view_plan")

    st.divider()
    if st.button("➕ Create a custom goal"):
        st.session_state["new_goal_type"] = None
        goto("create_goal")

def page_create_goal():
    st.markdown("### Create your goal")

    with st.form("create_goal_form"):
        # Profile
        st.subheader("Your profile")
        c1, c2, c3 = st.columns(3)
        with c1:
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=75.0, step=0.5)
        with c2:
            height = st.number_input("Height (m)", min_value=1.2, max_value=2.2, value=1.75, step=0.01)
        with c3:
            age = st.number_input("Age", min_value=14, max_value=100, value=22, step=1)

        sex = st.selectbox("Sex", ["Male", "Female"], index=0)
        activity = st.selectbox("Activity level", ["Low (1–2x/week)", "Moderate (3–4x/week)", "High (5+ /week)"], index=1)

        st.divider()

        # Goal type
        st.subheader("Goal type")
        preselect = st.session_state.get("new_goal_type", "Weight Loss")
        gtype = st.selectbox("Select", ["Weight Loss", "Muscle Gain", "Endurance", "Lifestyle"], index=["Weight Loss","Muscle Gain","Endurance","Lifestyle"].index(preselect))

        goal_title = st.text_input("Goal title", value=f"{gtype} Plan")

        st.markdown("#### Goal parameters")
        if gtype == "Weight Loss":
            target_loss = st.number_input("How much to lose? (kg)", min_value=1.0, max_value=40.0, value=7.0, step=0.5)
            weeks = st.number_input("Over how many weeks?", min_value=2, max_value=52, value=8, step=1)
        elif gtype == "Muscle Gain":
            target_gain = st.number_input("How much to gain? (kg)", min_value=1.0, max_value=15.0, value=3.0, step=0.5)
            weeks = st.number_input("Over how many weeks?", min_value=4, max_value=52, value=12, step=1)
        elif gtype == "Endurance":
            target_event = st.selectbox("Target", ["Run 5k", "Run 10k", "Cycle 50k", "Improve VO2max"])
            weeks = st.number_input("Training block (weeks)", min_value=4, max_value=24, value=8, step=1)
            sessions = st.slider("Sessions per week", 2, 6, 4)
        else:  # Lifestyle
            focus = st.selectbox("Primary focus", ["Sleep & Energy", "Daily Activity", "Stress & Recovery", "Nutrition Basics"])
            weeks = st.number_input("Coaching horizon (weeks)", min_value=4, max_value=24, value=8, step=1)

        submitted = st.form_submit_button("Generate plan 🚀")

    if submitted:
        # Generate plan dict
        if gtype == "Weight Loss":
            plan = generate_weight_loss_plan(weight, height, age, sex, activity, target_loss, weeks)
        elif gtype == "Muscle Gain":
            plan = generate_muscle_gain_plan(weight, height, age, sex, activity, target_gain, weeks)
        elif gtype == "Endurance":
            plan = generate_endurance_plan(weight, height, age, sex, activity, target_event, weeks, sessions)
        else:
            plan = generate_lifestyle_plan(weight, height, age, sex, activity, focus, weeks)

        # Store goal
        goal = {
            "id": new_goal_id(),
            "title": goal_title.strip() or f"{gtype} Plan",
            "type": gtype,
            "created": dt.datetime.now(),
            "profile": {
                "weight": weight, "height": height, "age": age, "sex": sex, "activity": activity
            },
            "plan": plan
        }
        st.session_state.goals.append(goal)
        st.success("Plan created ✅")
        st.session_state["open_goal_id"] = goal["id"]
        goto("view_plan")

    if st.button("← Back to home"):
        goto("home")

def page_view_plan():
    gid = st.session_state.get("open_goal_id")
    goal = next((g for g in st.session_state.goals if g["id"] == gid), None)
    if not goal:
        st.warning("Goal not found.")
        if st.button("← Back"):
            goto("home")
        return

    gtype = goal["type"]
    plan = goal["plan"]
    prof = goal["profile"]

    st.markdown(f"### {goal['title']}  ·  *{gtype}*")
    st.caption(f"Created on {goal['created'].strftime('%Y-%m-%d')}")

    # Summary badges
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("BMI", f"{plan['bmi']}", plan['bmi_cat'])
    with c2:
        st.metric("TDEE (kcal)", f"{plan['tdee']}")
    with c3:
        if gtype == "Weight Loss":
            st.metric("Deficit/day", f"-{plan['deficit_per_day']} kcal")
        elif gtype == "Muscle Gain":
            st.metric("Surplus/day", f"+{plan['surplus_per_day']} kcal")
        elif gtype == "Endurance":
            st.metric("Sessions/wk", f"{plan['sessions_per_week']}")
        else:
            st.metric("Horizon", f"{plan['weeks']} w")
    with c4:
        if gtype == "Weight Loss":
            st.metric("Target kcal", f"{plan['target_kcal']}")
        elif gtype == "Muscle Gain":
            st.metric("Protein", f"{plan['protein_g']} g/day")
        else:
            st.metric("Weeks", f"{plan['weeks']}")

    st.divider()

    # Nutrition block
    st.subheader("🍎 Nutrition")
    if gtype == "Weight Loss":
        st.write(f"**Target intake:** ~**{plan['target_kcal']} kcal/day**  ·  Suggested macros: {plan['macros']}")
        st.info(plan["notes"])
    elif gtype == "Muscle Gain":
        st.write(f"**Target intake:** ~**{plan['target_kcal']} kcal/day**  ·  **Protein:** ~**{plan['protein_g']} g/day**")
        st.info(plan["notes"])
    elif gtype == "Endurance":
        st.write("Fuel for performance: carbs around workouts, protein 1.6–2.0 g/kg/day, hydrate well.")
        st.info(plan["notes"])
    else:
        st.write("Simple template: protein each meal + veggies + quality carbs + healthy fats. Avoid late heavy meals.")

    if "nutrition_example" in plan:
        with st.expander("Example day"):
            for meal, desc, kcal in plan["nutrition_example"]:
                st.markdown(f"- **{meal}:** {desc} {('· ' + kcal) if kcal else ''}")

    st.divider()

    # Training / Habits block
    if gtype in ("Weight Loss", "Muscle Gain", "Endurance"):
        st.subheader("🏋️ Training Plan")
    else:
        st.subheader("❤️ Lifestyle Habits")

    weekly_schedule_header()
    render_week_table(plan["week_plan"])

    if gtype == "Lifestyle" and "habits" in plan:
        st.divider()
        st.subheader("🧰 Keystone Habits")
        for name, tip in plan["habits"]:
            st.markdown(f"- **{name}:** {tip}")

    st.divider()
    st.caption("FitMind AI is educational and does not replace medical advice. Consult a professional for personalized care.")

    cols = st.columns(2)
    with cols[0]:
        if st.button("← Back to goals"):
            goto("home")
    with cols[1]:
        if st.button("Duplicate this plan"):
            dup = {**goal, "id": new_goal_id(), "title": goal["title"] + " (copy)", "created": dt.datetime.now()}
            st.session_state.goals.append(dup)
            st.success("Plan duplicated.")

# =========================
# Router
# =========================
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "create_goal":
    page_create_goal()
elif st.session_state.page == "view_plan":
    page_view_plan()
else:
    page_home()

