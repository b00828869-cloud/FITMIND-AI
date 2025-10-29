import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

# ---------------------------------
# Gauge drawing (new geometry)
# ---------------------------------

def draw_gauge(bmi_value: float):
    """
    Draw a 5-slice semicircle gauge (UNDERWEIGHT -> SEVERELY OBESE),
    evenly spaced, centered above the needle, with a purple needle.
    """

    # Visual style
    seg_color = "#F4C542"      # gold / yellow
    needle_color = "#2E0A78"   # deep purple
    text_color = "#1a1a1a"     # near black

    # We will draw an arc from -100° to +100°
    start_deg = -100
    end_deg = 100

    # Define the 5 categories, in order from left to right
    categories = [
        ("UNDERWEIGHT", "< 18.5"),
        ("NORMAL", "18.5 – 24.9"),
        ("OVERWEIGHT", "25.0 – 29.9"),
        ("OBESE", "30.0 – 39.9"),
        ("SEVERELY\nOBESE", "≥ 40.0"),
    ]

    n_segments = len(categories)

    # We'll split the total arc evenly across the 5 segments
    total_arc = end_deg - start_deg  # e.g. 200 degrees
    arc_per_segment = total_arc / n_segments

    # Helper: map bmi to needle angle
    # We'll clamp BMI into [10, 50] then map that to [-100°, +100°]
    def bmi_to_angle_deg(b):
        b_clamped = max(10, min(50, b))
        # 10  -> -100°
        # 50  -> +100°
        ratio = (b_clamped - 10) / (50 - 10)  # 0..1
        return start_deg + ratio * (end_deg - start_deg)

    # --- create figure
    fig, ax = plt.subplots(figsize=(6, 4))

    r_outer = 1.0    # outer radius of gauge band
    r_inner = 0.55   # inner radius of gauge band
    label_r = 0.8    # radius where we place text
    y_offset = 0.0   # we keep center on (0,0) now so arc is symmetric

    # Draw each segment wedge
    for i, (title, rng) in enumerate(categories):
        seg_start_deg = start_deg + i * arc_per_segment
        seg_end_deg   = start_deg + (i + 1) * arc_per_segment

        # build the polygon of this wedge
        thetas_outer = np.radians(np.linspace(seg_start_deg, seg_end_deg, 80))
        x_outer = r_outer * np.cos(thetas_outer)
        y_outer = r_outer * np.sin(thetas_outer) + y_offset

        thetas_inner = np.radians(np.linspace(seg_end_deg, seg_start_deg, 80))
        x_inner = r_inner * np.cos(thetas_inner)
        y_inner = r_inner * np.sin(thetas_inner) + y_offset

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

        # middle angle of this wedge, for label placement
        mid_deg = 0.5 * (seg_start_deg + seg_end_deg)
        mid_rad = math.radians(mid_deg)
        x_text = label_r * np.cos(mid_rad)
        y_text = label_r * np.sin(mid_rad) + y_offset

        ax.text(
            x_text,
            y_text,
            f"{title}\n{rng}",
            ha="center",
            va="center",
            fontsize=11,
            color=text_color,
            fontweight="bold",
            zorder=2,
            linespacing=1.15
        )

    # -------- needle --------
    needle_deg = bmi_to_angle_deg(bmi_value)
    needle_rad = math.radians(needle_deg)

    needle_len = 0.9
    x_end = needle_len * np.cos(needle_rad)
    y_end = needle_len * np.sin(needle_rad) + y_offset

    # draw needle line
    ax.plot(
        [0, x_end],
        [0, y_end],
        color=needle_color,
        linewidth=4,
        zorder=3
    )

    # draw needle base (purple circle + white circle)
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

    # "BMI: xx.x" label under the needle center
    ax.text(
        0,
        -0.25,
        f"BMI: {bmi_value:.1f}",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color=text_color,
        zorder=6
    )

    # final styling
    ax.set_aspect("equal")
    # the arc now spans 200°, so we want to see all of it nicely centered
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.6, 1.1)
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

st.title("FitMind AI - BMI Calculator 💪")
st.write(
    "Enter your weight and height to estimate your BMI, see your health category, "
    "and visualize it on the gauge."
)

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
    bmi = weight / (height ** 2)

    st.markdown(f"Your BMI is **{bmi:.1f}**")

    # determine category for the message box
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

