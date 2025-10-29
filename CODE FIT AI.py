import streamlit as st
import math
import streamlit.components.v1 as components

st.set_page_config(
    page_title="FitMind AI - BMI Calculator",
    page_icon="💪",
    layout="centered"
)

# -------------------------
# Helpers (Python side)
# -------------------------
def bmi_to_angle_deg(bmi):
    # clamp BMI range so we never go outside the gauge
    b = max(10, min(50, bmi))
    # map BMI 10 -> -100 deg, BMI 50 -> +100 deg
    ratio = (b - 10) / (50 - 10)
    return -100 + ratio * 200  # in degrees

def bmi_category(bmi):
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


# -------------------------
# Streamlit UI
# -------------------------
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
    bmi = weight / (height ** 2)
    cat_label = bmi_category(bmi)
    angle = bmi_to_angle_deg(bmi)

    st.markdown(f"Your BMI is **{bmi:.1f} ({cat_label})**")
    st.divider()
    st.subheader("BMI Gauge")

    # We'll send data to JS like this:
    js_payload = {
        "bmi_text": f"BMI: {bmi:.1f} ({cat_label})",
        "angle": angle
    }

    # Build the HTML/JS. We don't include <html> or <body>, just a container.
    gauge_html = f"""
    <div id="gauge-root" style="width:600px; margin:0 auto; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"></div>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    (function() {{
        // ----- DATA FROM PYTHON -----
        const bmiText = {js_payload["bmi_text"]!r};
        const targetAngle = {js_payload["angle"]};

        // ----- STATIC SEGMENTS DEFINITIONS -----
        // We keep the text content here in JS to avoid weird unicode in Python f-string
        const segments = [
            {{ line1: "UNDERWEIGHT",    line2: "< 18.5" }},
            {{ line1: "NORMAL",         line2: "18.5 - 24.9" }},
            {{ line1: "OVERWEIGHT",     line2: "25.0 - 29.9" }},
            {{ line1: "OBESE",          line2: "30.0 - 39.9" }},
            {{ line1: "SEVERELY OBESE", line2: ">= 40.0" }}
        ];

        // ----- LAYOUT CONSTANTS -----
        const width = 600;
        const height = 320;

        const outerR = 200;
        const innerR = 130;

        // center of the gauge (the pivot of the needle)
        const centerX = width / 2;
        const centerY = 220;

        // gauge arc from -100 deg to +100 deg
        const startDeg = -100;
        const endDeg = 100;
        const totalArc = endDeg - startDeg;        // 200
        const arcPerSeg = totalArc / segments.length; // 40 deg each

        // ----- CREATE SVG -----
        const container = d3.select("#gauge-root");
        const svg = container.append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("background-color", "white");  // force white background

        const g = svg.append("g");

        // ----- DRAW SEGMENTS -----
        segments.forEach((seg, i) => {{
            const segStart = startDeg + i * arcPerSeg;
            const segEnd   = startDeg + (i + 1) * arcPerSeg;

            const arcGen = d3.arc()
                .innerRadius(innerR)
                .outerRadius(outerR)
                .startAngle(segStart * Math.PI/180)
                .endAngle(segEnd * Math.PI/180);

            // wedge
            g.append("path")
                .attr("d", arcGen)
                .attr("fill", "#F4C542")
                .attr("stroke", "white")
                .attr("stroke-width", 5)
                .attr("transform", `translate(${centerX}, ${centerY})`);

            // label position in the middle of this wedge
            const midDeg = (segStart + segEnd) / 2;
            const midRad = midDeg * Math.PI/180;
            const labelR = (innerR + outerR) / 2;

            const lx = centerX + labelR * Math.cos(midRad);
            const ly = centerY + labelR * Math.sin(midRad);

            // line1 (bold)
            g.append("text")
                .attr("x", lx)
                .attr("y", ly - 6)
                .text(seg.line1)
                .attr("fill", "#1a1a1a")
                .attr("font-size", "12px")
                .attr("font-weight", "700")
                .attr("text-anchor", "middle");

            // line2 (range)
            g.append("text")
                .attr("x", lx)
                .attr("y", ly + 12)
                .text(seg.line2)
                .attr("fill", "#1a1a1a")
                .attr("font-size", "11px")
                .attr("font-weight", "500")
                .attr("text-anchor", "middle");
        }});

        // ----- NEEDLE GROUP -----
        const needleGroup = g.append("g")
            .attr("transform", `translate(${centerX}, ${centerY})`);

        // needle shape (skinny triangle pointing straight up initially)
        const needleLen = 140;
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

        // purple circle base
        needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 22)
            .attr("fill", "#2E0A78")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

        // white inner circle
        needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 8)
            .attr("fill", "white")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

        // BMI readout text under gauge
        g.append("text")
            .attr("x", centerX)
            .attr("y", centerY + 50)
            .text(bmiText)
            .attr("fill", "#1a1a1a")
            .attr("font-size", "20px")
            .attr("font-weight", "600")
            .attr("text-anchor", "middle");

        // ----- NEEDLE ANIMATION -----
        needle
            .attr("transform", "rotate(-100)")  // start far left
            .transition()
            .duration(800)
            .attr("transform", `rotate(${targetAngle})`);
    }})();
    </script>
    """

    # render component
    components.html(gauge_html, height=400)

    st.caption(
        "Interactive gauge built in D3.js. BMI is only an indicator. "
        "Muscle mass, age, and medical conditions matter."
    )


