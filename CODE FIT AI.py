import streamlit as st
import streamlit.components.v1 as components

# -------------------------------------------------
# Streamlit page config
# -------------------------------------------------
st.set_page_config(
    page_title="FitMind AI - BMI Calculator",
    page_icon="💪",
    layout="centered"
)

# -------------------------------------------------
# Helper functions (Python)
# -------------------------------------------------
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

def bmi_to_angle_deg(bmi: float) -> float:
    """
    We map BMI range [10, 50] -> [-100°, +100°]
    Clamp so needle never goes outside the gauge.
    """
    b = max(10, min(50, bmi))
    ratio = (b - 10) / (50 - 10)  # 0..1
    return -100 + ratio * 200     # degrees


# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("FitMind AI - BMI Calculator 💪")
st.write(
    "Enter your weight and height to estimate your BMI, see your health category, "
    "and visualize it on a dynamic gauge."
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
    # 1. Calculate BMI + label
    bmi = bmi_value(weight, height)
    cat_label = bmi_category(bmi)

    st.markdown(f"Your BMI is **{bmi:.1f} ({cat_label})**")
    st.divider()
    st.subheader("BMI Gauge")

    # 2. Compute needle angle + text for JS
    angle = bmi_to_angle_deg(bmi)
    bmi_text_js = f"BMI: {bmi:.1f} ({cat_label})"

    # 3. Build D3 gauge HTML
    gauge_html = f"""
    <div id="gauge-root" style="
        width:700px;
        margin:0 auto;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    "></div>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    (function() {{
        // ----- DATA FROM PYTHON -----
        const bmiText = {bmi_text_js!r};        // ex: "BMI: 23.1 (NORMAL)"
        const targetAngle = {angle};            // ex: 15.2 (degrees)

        // ----- SEGMENTS DEFINITIONS -----
        // Labels to draw inside each yellow wedge
        const segments = [
            {{ line1: "UNDERWEIGHT",    line2: "< 18.5" }},
            {{ line1: "NORMAL",         line2: "18.5 – 24.9" }},
            {{ line1: "OVERWEIGHT",     line2: "25.0 – 29.9" }},
            {{ line1: "OBESE",          line2: "30.0 – 39.9" }},
            {{ line1: "SEVERELY OBESE", line2: "≥ 40.0" }}
        ];

        // ----- LAYOUT CONSTANTS -----
        // We make it wide so text at the extremes isn't cut off
        const width = 700;
        const height = 360;

        // Radii of the arc band
        const outerR = 230;    // outer radius
        const innerR = 150;    // inner radius
        const labelR = (innerR + outerR) / 2;  // where labels go

        // The pivot of the needle / center of gauge arc
        const centerX = width / 2;
        const centerY = 250;   // move gauge down to leave space above

        // Gauge arc covers -100 deg to +100 deg
        const startDeg = -100;
        const endDeg = 100;
        const totalArc = endDeg - startDeg;           // 200 deg span
        const arcPerSeg = totalArc / segments.length; // 40 deg each

        // ----- CREATE SVG -----
        const container = d3.select("#gauge-root");
        const svg = container.append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("background-color", "white"); // force white bg even in dark theme

        const g = svg.append("g");

        // ----- DRAW SEGMENTS + LABELS -----
        segments.forEach((seg, i) => {{
            const segStart = startDeg + i * arcPerSeg;
            const segEnd   = startDeg + (i + 1) * arcPerSeg;

            // arc path for this segment
            const arcGen = d3.arc()
                .innerRadius(innerR)
                .outerRadius(outerR)
                .startAngle(segStart * Math.PI/180)
                .endAngle(segEnd * Math.PI/180);

            // yellow slice
            g.append("path")
                .attr("d", arcGen)
                .attr("fill", "#F4C542")
                .attr("stroke", "white")
                .attr("stroke-width", 6)
                .attr("transform", `translate(${centerX}, ${centerY})`);

            // mid-angle for label position
            const midDeg = (segStart + segEnd)/2;
            const midRad = midDeg * Math.PI/180;

            // We pull the label slightly toward the inner radius for readability
            const lx = centerX + (labelR - 10) * Math.cos(midRad);
            const ly = centerY + (labelR - 10) * Math.sin(midRad);

            // line1 (bold, with white stroke outline for contrast)
            g.append("text")
                .attr("x", lx)
                .attr("y", ly - 6)
                .text(seg.line1)
                .attr("fill", "#1a1a1a")
                .attr("font-size", "13px")
                .attr("font-weight", "700")
                .attr("text-anchor", "middle")
                .attr("stroke", "white")
                .attr("stroke-width", 2)
                .attr("paint-order", "stroke");

            // line2 (range text)
            g.append("text")
                .attr("x", lx)
                .attr("y", ly + 12)
                .text(seg.line2)
                .attr("fill", "#1a1a1a")
                .attr("font-size", "12px")
                .attr("font-weight", "500")
                .attr("text-anchor", "middle")
                .attr("stroke", "white")
                .attr("stroke-width", 2)
                .attr("paint-order", "stroke");
        }});

        // ----- NEEDLE -----
        const needleGroup = g.append("g")
            .attr("transform", `translate(${centerX}, ${centerY})`);

        // Needle is a thin triangle that starts pointing straight up (0deg)
        const needleLen = 160;
        const needleWidth = 6;
        const needlePath = d3.path();
        needlePath.moveTo(0, 0);
        needlePath.lineTo(-needleWidth, 0);
        needlePath.lineTo(0, -needleLen);
        needlePath.lineTo(needleWidth, 0);
        needlePath.closePath();

        const needle = needleGroup.append("path")
            .attr("d", needlePath.toString())
            .attr("fill", "#2E0A78");

        // Purple base circle
        needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 24)
            .attr("fill", "#2E0A78")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

        // White center circle
        needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 9)
            .attr("fill", "white")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

        // BMI text under gauge
        g.append("text")
            .attr("x", centerX)
            .attr("y", centerY + 60)
            .text(bmiText)
            .attr("fill", "#1a1a1a")
            .attr("font-size", "22px")
            .attr("font-weight", "700")
            .attr("text-anchor", "middle");

        // ----- NEEDLE ANIMATION -----
        needle
            .attr("transform", "rotate(-100)")  // start fully left
            .transition()
            .duration(800)
            .attr("transform", `rotate(${targetAngle})`);
    }})();
    </script>
    """

    # 4. Render the gauge in Streamlit
    components.html(gauge_html, height=420)

    st.caption(
        "This BMI gauge is interactive (D3.js). BMI is only an indicator. "
        "Muscle mass, age, and medical conditions matter."
    )

