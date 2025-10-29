import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

# ---------------------------------
# Gauge drawing function
# ---------------------------------
def draw_gauge(bmi_value: float):
    # Colors / style
    seg_color = "#F4C542"      # gold / yellow
    needle_color = "#2E0A78"   # deep purple
    text_color = "#1a1a1a"     # almost black

    # BMI scale we'll map to angles
    bmi_min_disp = 10
    bmi_max_disp = 50

    # Segments definition (from left to right)
    # (bmi_low, bmi_high, line1, line2)
    segments = [
        (10,   18.5, "UNDERWEIGHT", "< 18.5"),
        (18.5, 25.0, "NORMAL", "18.5 – 24.9"),
        (25.0, 30.0, "OVERWEIGHT", "25.0 – 29.9"),
        (30.0, 40.0, "OBESE", "30.0 – 39.9"),
        (40.0, 50.0, "SEVERELY\nOBESE", "≥ 40.0"),
    ]

    # Map BMI value to angle in radians
    # -90° (left) to +90° (right)
    def bmi_to_angle(b):
        b = max(bmi_min_disp, min(b, bmi_max_disp))
        ratio = (b - bmi_min_disp) / (bmi_max_disp - bmi_min_disp)  # 0..1
        angle_deg = -90 + ratio * 180
        return math.radians(angle_deg)

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 4))

    # Adjust vertical offset so the arc sits nicely above the needle
    y_offset = 0.2
    r_outer = 1.0
    r_inner = 0.55
    text_r = 0.8  # where to place labels inside each wedge

    # Draw each wedge (segment)
    for (b_low, b_high, line1, line2) in segments:
        start_a = bmi_to_angle(b_low)
        end_a   = bmi_to_angle(b_high)

        # Outer boundary of the wedge
        angles_outer = np.linspace(start_a, end_a, 60)
        x_outer = r_outer * np.cos(angles_outer)
        y_outer = r_outer * np.sin(angles_outer) + y_offset

        # Inner boundary of the wedge
        angles_inner = np.linspace(end_a, start_a, 60)
        x_inner = r_inner * np.cos(angles_inner)
        y_inner = r_inner * np.sin(angles_inner) + y_offset

        # Build polygon
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

        # Put the label in the middle of the wedge
        mid_a = 0.5 * (start_a + end_a)
        x_text = text_r * np.cos(mid_a)
        y_text = text_r * np.sin(mid_a) + y_offset

        # 2-line label (bold like your PowerPoint)
        # "SEVERELY\nOBESE" already includes newline, so line1 can be multi-line
        ax.text(
            x_text,
            y_text,
            f"{line1}\n{line2}",
            ha="center",
            va="center",
            fontsize=11,
            color=text_color,
            fontweight="bold",
            zorder=2,
            linespacing=1.15,
        )

    # Draw needle
    needle_angle = bmi_to_angle(bmi_value)
    needle_len = 0.9

    x_end = needle_len * np.cos(needle_angle)
    y_end = needle_len * np.sin(needle_angle) + y_offset

    # needle line
    ax.plot(
        [0, x_end],
        [0 + y_offset, y_end],
        color=needle_color,
        linewidth=4,
        zorder=3
    )

    # needle base (purple circle + white inner circle)
    ax.scatter(
        [0],
        [0 + y_offset],
        color=needle_color,
        s=500,
        zorder=4,
        edgecolor=needle_color,
        linewidth=1
    )

    ax.scatter(
        [0],
        [0 + y_offset],
        color="white",
        s=150,
        zorder=5,
        edgecolor=needle_color,
        linewidth=2
    )

    # BMI text under the gauge
    ax.text(
        0,
        -0.25 + y_offset,
        f"BMI: {bmi_value:.1f}",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color=text_color,
        zorder=6
    )

    # Clean figure style
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.4 + y_offset, 1.3 + y_offset)
    ax.axis("off")

    return fig


# ---------------------------------
# Streamlit UI
# ---------------------------------

st.set_page_config(
    page_title="FitMind AI - BMI Calculator",
    page_icon="💪",
    layout="centered"
)

# Header / intro
st.title("FitMind AI - BMI Calculator 💪")
st.write(
    "Enter your weight and height to estimate your BMI, see your health category, "
    "and visualize it on the gauge."
)

# Inputs
col1, col2 = st.columns(2)
with col1:
    weight = st.number_input(
        "Weight (kg):",
        min_value=30.0,
        max_value=250.0,
        step=0.5,
        value=75.0
    )
with col2:
    height = st.number_input(
        "Height (m):",
        min_value=1.2,
        max_value=2.2,
        step=0.01,
        value=1.75
    )

if st.button("Calculate BMI"):
    # Calculate BMI
    bmi = weight / (height ** 2)

    st.markdown(f"Your BMI is **{bmi:.1f}**")

    # Category message
    if bmi < 18.5:
        st.warning("UNDERWEIGHT (<18.5)")
        cat_label = "UNDERWEIGHT"
    elif bmi < 25:
        st.success("NORMAL (18.5 – 24.9)")
        cat_label = "NORMAL"
    elif bmi < 30:
        st.info("OVERWEIGHT (25.0 – 29.9)")
        cat_label = "OVERWEIGHT"
    elif bmi < 40:
        st.error("OBESE (30.0 – 39.9)")
        cat_label = "OBESE"
    else:
        st.error("SEVERELY OBESE (≥ 40.0)")
        cat_label = "SEVERELY OBESE"

    st.divider()

    st.subheader("BMI Gauge")
    fig = draw_gauge(bmi)
    st.pyplot(fig)

    st.caption(
        f"This gauge shows where you are ({cat_label}). "
        "BMI is only an indicator. Muscle mass, age, and medical conditions matter."
    )

