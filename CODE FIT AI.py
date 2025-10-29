import streamlit as st
import math
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="FitMind AI - BMI Calculator",
    page_icon="💪",
    layout="centered"
)

st.title("FitMind AI - BMI Calculator 🧮")

weight = st.number_input("Enter your weight (kg):", min_value=30.0, max_value=250.0, step=0.5, value=75.0)
height = st.number_input("Enter your height (m):", min_value=1.2, max_value=2.2, step=0.01, value=1.75)

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)
    st.write(f"Your BMI is **{bmi:.1f}**")

    # Interpretation
    if bmi < 18.5:
        label = "Underweight"
        zone_min, zone_max = 10, 18.5
    elif bmi < 25:
        label = "Normal weight"
        zone_min, zone_max = 18.5, 25
    elif bmi < 30:
        label = "Overweight"
        zone_min, zone_max = 25, 30
    elif bmi < 35:
        label = "Obesity (Class I)"
        zone_min, zone_max = 30, 35
    elif bmi < 40:
        label = "Obesity (Class II)"
        zone_min, zone_max = 35, 40
    else:
        label = "Obesity (Class III)"
        zone_min, zone_max = 40, 50  # just extend scale visually

    # Message box
    if bmi < 18.5:
        st.warning(label)
    elif bmi < 25:
        st.success(label)
    elif bmi < 30:
        st.info(label)
    elif bmi < 35:
        st.warning(label)
    elif bmi < 40:
        st.error(label)
    else:
        st.error(label)

    st.markdown("---")
    st.subheader("BMI Gauge")

    # We create a "gauge" from 10 to 50 roughly
    min_bmi_display = 10
    max_bmi_display = 50
    bmi_clamped = min(max(bmi, min_bmi_display), max_bmi_display)

    # Convert BMI position to angle on a semicircle
    # left side (-90 deg) = min_bmi_display
    # right side (+90 deg) = max_bmi_display
    # We'll map the bmi_clamped proportionally
    ratio = (bmi_clamped - min_bmi_display) / (max_bmi_display - min_bmi_display)
    angle_deg = -90 + ratio * 180
    angle_rad = math.radians(angle_deg)

    # Needle endpoint
    needle_length = 1.0
    x_needle = needle_length * math.cos(angle_rad)
    y_needle = needle_length * math.sin(angle_rad)

    # Draw gauge using matplotlib
    fig, ax = plt.subplots(figsize=(5, 2.5))

    # Draw semicircle outline
    theta = [math.radians(a) for a in range(-90, 91)]
    xs = [math.cos(t) for t in theta]
    ys = [math.sin(t) for t in theta]
    ax.plot(xs, ys, linewidth=3)

    # Fill ticks for main BMI zones (rough visual ranges)
    # We'll just add simple text annotations instead of colors for now
    ax.text(-0.9, -0.1, "<18.5\nUnder", ha="center", va="center", fontsize=8)
    ax.text(-0.4, 0.6, "18.5-24.9\nNormal", ha="center", va="center", fontsize=8)
    ax.text(0.2, 0.6, "25-29.9\nOverwt.", ha="center", va="center", fontsize=8)
    ax.text(0.75, 0.2, "30+\nObese", ha="center", va="center", fontsize=8)

    # Draw the needle
    ax.plot([0, x_needle], [0, y_needle], linewidth=3)
    ax.scatter([0], [0], s=50)

    # Style the plot
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.2, 1.1)
    ax.axis("off")

    # Add current BMI label under the gauge
    ax.text(0, -0.3, f"BMI: {bmi:.1f} ({label})", ha="center", va="center", fontsize=10)

    st.pyplot(fig)

    st.caption(
        "The gauge shows where you are on the BMI spectrum. "
        "Reminder: BMI is only one indicator. Muscle mass, age, and medical context matter."
    )
