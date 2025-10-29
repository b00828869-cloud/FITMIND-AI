import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math

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

    # Determine label + color box message
    if bmi < 18.5:
        label = "Underweight"
        box_func = st.warning
    elif bmi < 25:
        label = "Normal weight"
        box_func = st.success
    elif bmi < 30:
        label = "Overweight"
        box_func = st.info
    elif bmi < 40:
        label = "Obese"
        box_func = st.error
    else:
        label = "Severely Obese"
        box_func = st.error

    box_func(label)

    st.markdown("---")
    st.subheader("BMI Gauge")

    # ==============================
    # 1. Définition des zones visuelles
    # ==============================
    # On crée un cadran de -90° à +90°
    # Puis on attribue des sous-plages d'angles pour chaque zone BMI.
    #
    # Mapping BMI -> angle:
    #   BMI 10  => -90°
    #   BMI 18.5 => ~ -40°
    #   BMI 25  => ~ -5°
    #   BMI 30  => ~ +25°
    #   BMI 40  => ~ +70°
    #   BMI 50  => +90°
    #
    # On définit les bornes BMI qu'on veut afficher:
    bmi_min_disp = 10
    bmi_max_disp = 50

    # Les segments (bmi_low, bmi_high, color, label_display)
    segments = [
        (10,   18.5, "#2c6fd6", "UNDERWEIGHT\n< 18.5"),
        (18.5, 25.0, "#00b050", "NORMAL\n18.5 - 24.9"),
        (25.0, 30.0, "#ffc000", "OVERWEIGHT\n25.0 - 29.9"),
        (30.0, 40.0, "#ed7d31", "OBESE\n30.0 - 39.9"),
        (40.0, 50.0, "#c00000", "SEVERELY OBESE\n≥ 40.0"),
    ]

    # Fonction utilitaire: convertit un BMI en angle radians sur le demi-cercle
    # -90° = gauche, +90° = droite
    def bmi_to_angle(b):
        # clamp
        b = max(bmi_min_disp, min(b, bmi_max_disp))
        ratio = (b - bmi_min_disp) / (bmi_max_disp - bmi_min_disp)  # 0 -> 1
        angle_deg = -90 + ratio * 180
        return math.radians(angle_deg)

    # ==============================
    # 2. Dessin du cadran
    # ==============================
    fig, ax = plt.subplots(figsize=(6, 3))

    # Pour chaque segment, on dessine un "wedge" (secteur) coloré
    for (b_low, b_high, color, text_label) in segments:
        start_angle = bmi_to_angle(b_low)
        end_angle   = bmi_to_angle(b_high)

        # On crée un ensemble de points entre start_angle et end_angle
        angles = np.linspace(start_angle, end_angle, 50)
        # rayon du cadran
        r_outer = 1.0
        r_inner = 0.45

        # Polygone extérieur/intérieur pour remplir la zone
        x_outer = r_outer * np.cos(angles)
        y_outer = r_outer * np.sin(angles)
        x_inner = r_inner * np.cos(angles[::-1])
        y_inner = r_inner * np.sin(angles[::-1])

        x_poly = np.concatenate([x_outer, x_inner])
        y_poly = np.concatenate([y_outer, y_inner])

        ax.fill(x_poly, y_poly, color=color, edgecolor="white", linewidth=2)

        # Position du label texte au milieu du segment
        mid_angle = (start_angle + end_angle) / 2
        x_text = 0.7 * np.cos(mid_angle)
        y_text = 0.7 * np.sin(mid_angle)
        ax.text(
            x_text,
            y_text,
            text_label,
            ha="center",
            va="center",
            fontsize=8,
            color="white",
            fontweight="bold"
        )

    # ==============================
    # 3. Aiguille
    # ==============================
    needle_angle = bmi_to_angle(bmi)
    needle_len = 0.9
    x_end = needle_len * np.cos(needle_angle)
    y_end = needle_len * np.sin(needle_angle)

    # tige
    ax.plot(
        [0, x_end],
        [0, y_end],
        color="black",
        linewidth=3
    )
    # base de l'aiguille
    ax.scatter([0], [0], color="black", s=80, zorder=10, edgecolor="white", linewidth=1)

    # ==============================
    # 4. Style du cadran
    # ==============================
    ax.set_aspect("equal")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.2, 1.1)
    ax.axis("off")

    # Texte global sous le cadran
    ax.text(
        0,
        -0.25,
        f"BMI: {bmi:.1f} ({label})",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold"
    )

    st.pyplot(fig)

    st.caption(
        "This scale is a general health indicator. It does not account for muscle mass, age, or medical conditions. "
        "Ask a professional if you have concerns."
    )
