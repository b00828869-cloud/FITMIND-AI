# Modern chart styling
import matplotlib.pyplot as plt
from matplotlib import cm

# Modern gradient-like color palette (inspired by your image)
colors = ["#240046", "#7B2CBF", "#FF5E78", "#FFD100"]

dfp = projection(weight_start, weight_goal, weeks)
fig, ax = plt.subplots(figsize=(8, 4))

# Create smooth gradient color line
gradient = np.linspace(0, 1, len(dfp))
ax.plot(
    dfp['Week'],
    dfp['Weight (kg)'],
    color=colors[2],
    linewidth=3,
    marker='o',
    markersize=6,
    markerfacecolor=colors[3],
    markeredgecolor="white",
    alpha=0.9,
)

# Fill the area under the curve with a soft fade
ax.fill_between(
    dfp['Week'],
    dfp['Weight (kg)'],
    color=colors[1],
    alpha=0.2
)

# Clean, modern styling
ax.set_facecolor("#F9F9FB")
fig.patch.set_facecolor("#F9F9FB")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_color("#CCCCCC")
ax.grid(alpha=0.15)
ax.set_title("🏋️ Weight Projection", fontsize=14, fontweight="bold", color="#240046", pad=12)
ax.set_xlabel("Weeks", fontsize=11, color="#555555")
ax.set_ylabel("Weight (kg)", fontsize=11, color="#555555")

st.pyplot(fig)

