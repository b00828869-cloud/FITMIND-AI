import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

# ---------- Gauge drawing function ----------
def draw_gauge(bmi_value: float):
    seg_color = "#F4C542"      # jaune or
    needle_color = "#2E0A78"   # violet
    text_color = "#1a1a1a"

    bmi_min_disp = 10
    bmi_max_disp = 50

    segments = [
        (10,   18.5, "UNDERWEIGHT", "< 18.5"),
        (18.5, 25.0, "NORMAL", "18.5 – 24.9"),
        (25.0, 30.0, "OVERWEIGHT", "25.0 – 29.9"),
        (30.0, 40.0, "OBESE", "30.0 – 39.9"),
        (40.0, 50.0, "SEVERELY\nOBESE", "≥ 40.0"),
    ]

    def bmi_to_angle(b):
        b = max(bmi_min_disp, min(b, bmi_max_disp))
        ratio = (b - bmi_min_disp) / (bmi_max_disp - bmi_min_disp)
        angle_deg = -90 + ratio * 180
        return math.radians(angle_deg)

    fig, ax = plt.subplots(figsize=(6, 3))

    r_outer = 1.0
    r_inner = 0.55

    for (b_low, b_high, line1, line2) in segments:
        start_a = bmi_to_angle(b_low)
        end_a   = bmi_to_angle(b_high)

        angles_outer = np.linspace(start_a, end_a, 50)
        x_outer = r_outer * np.cos(angles_outer)
        y_outer = r_outer * np.sin(angles_outer)

        angles_inner = np.linspace(end_a, start_a, 50)
        x_inner = r_inner * np.cos(angles_inner)
        y_inner = r_inner * np.sin(angles_inner)

        x_poly = np.concatenate([x_outer, x_inner])
        y_poly = np.concatenate([y_outer, y_inner])

        ax.fill(
            x_poly,
            y_poly,
            color=seg_color,
            edgecolor="white",
            linewidth=3,
            zorder=1
        )

        mid_a = 0.5 * (start_a + end_a)
        label_r = 0.8
        x_text = label_r * np.cos(mid_a)
        y_text = label_r * np.sin(mid_a)

        ax.text(
            x_text,
            y_text,
            f"{line1}\n{line2}",
            ha="center",
            va="center",
            fontsize=10,
            color=text_color,
            fontweight="bold",
            zorder=2,
            linespacing=1.2
        )

    needle_angle = bmi_to_angle(bmi_value)
    needle_len = 0.9
    x_end = needle_len * np.cos(needle_angle)
    y_end = needle_len * np.sin(needle_angle)

    ax.plot(
        [0, x_end],
        [0, y_end],
        color=needle_color,
        linewidth=4,
        zorder=3
    )

    ax.scatter(
        [0],
        [0],
        color=needle_color,
        s=500,
        zorder=4,
        edgecolor=needle_color,
        linewidth=1
    )
    ax.scatter(
        [0],
        [0],
        color="white",
        s=150,
        zorder=5,
        edgecolor=needle_color,
        linewidth=2
    )

    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.3, 1.2)
    ax.axis("off")

    ax.text(
        0,
        -0.25,
        f"BMI: {bmi_value:.1f}",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=text_color
    )

    return fig


# ---------- Streamlit UI ----------

st.set_page_config(
    page_title="FitMind AI - BMI Calculator",
    page_icon="💪",
    layout="centered"
)

st.title("FitMind AI - BMI Calculator 💪")

weight = st.number_input("Enter your weight (kg):", min_value=30.0, max_value=250.0, step=0.5, value=75.0)
height = st.number_input("Enter your height (m):", min_value=1.2, max_value=2.2, step=0.01, value=1.75)

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)

    st.write(f"Your BMI is **{bmi:.1f}**")

    # status box
    if bmi < 18.5:
        st.warning("UNDERWEIGHT (<18.5)")
    elif bmi < 25:
        st.success("NORMAL (18.5–24.9)")
    elif bmi < 30:
        st.info("OVERWEIGHT (25.0–29.9)")
    elif bmi < 40:
        st.error("OBESE (30.0–39.9)")
    else:
        st.error("SEVERELY OBESE (≥40.0)")

    st.divider()
    st.subheader("BMI Gauge")

    fig = draw_gauge(bmi)
    st.pyplot(fig)

    st.caption(
        "This gauge is an educational health indicator. It does not replace medical advice."
    )
