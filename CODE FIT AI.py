import numpy as np
import math
import matplotlib.pyplot as plt

def draw_gauge(bmi_value: float):
    """
    Draws the BMI gauge with 5 yellow segments and a purple needle
    pointing to the current bmi_value.
    Returns a matplotlib figure you can send to st.pyplot(fig).
    """

    # --- Config couleurs / style ---
    seg_color = "#F4C542"  # ton jaune-or
    needle_color = "#2E0A78"  # ton violet
    text_color = "#1a1a1a"

    # bornes globales pour l'échelle angle
    bmi_min_disp = 10
    bmi_max_disp = 50

    # définitions des segments visuels
    # (bmi_low, bmi_high, label_line1, label_line2)
    segments = [
        (10,   18.5, "UNDERWEIGHT", "< 18.5"),
        (18.5, 25.0, "NORMAL", "18.5 – 24.9"),
        (25.0, 30.0, "OVERWEIGHT", "25.0 – 29.9"),
        (30.0, 40.0, "OBESE", "30.0 – 39.9"),
        (40.0, 50.0, "SEVERELY\nOBESE", "≥ 40.0"),
    ]

    # convertit un BMI en angle radians [-90°, +90°]
    def bmi_to_angle(b):
        b = max(bmi_min_disp, min(b, bmi_max_disp))
        ratio = (b - bmi_min_disp) / (bmi_max_disp - bmi_min_disp)  # 0..1
        angle_deg = -90 + ratio * 180
        return math.radians(angle_deg)

    fig, ax = plt.subplots(figsize=(6, 3))

    # dessiner chaque segment comme une "couronne"
    r_outer = 1.0     # rayon externe
    r_inner = 0.55    # rayon interne pour donner l'effet donut
    for (b_low, b_high, line1, line2) in segments:
        start_a = bmi_to_angle(b_low)
        end_a   = bmi_to_angle(b_high)

        # points du bord externe
        angles_outer = np.linspace(start_a, end_a, 50)
        x_outer = r_outer * np.cos(angles_outer)
        y_outer = r_outer * np.sin(angles_outer)

        # points du bord interne (on part dans l'autre sens pour fermer le polygone)
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

        # position du texte = angle milieu
        mid_a = 0.5 * (start_a + end_a)
        label_r = 0.8  # rayon du texte
        x_text = label_r * np.cos(mid_a)
        y_text = label_r * np.sin(mid_a)

        # texte centré en 2 lignes (style powerpoint)
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

    # dessiner l'aiguille
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

    # base ronde + rond blanc au centre (comme ton design)
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

    # style final du plot
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.3, 1.2)
    ax.axis("off")

    # texte sous la jauge
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

