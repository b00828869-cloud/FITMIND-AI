import streamlit as st
import math
import streamlit.components.v1 as components

st.set_page_config(
    page_title="FitMind AI - BMI Calculator",
    page_icon="💪",
    layout="centered"
)

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

def bmi_to_angle_deg(bmi):
    # clamp BMI to stay within the gauge
    b = max(10, min(50, bmi))
    # map BMI 10 -> -100°, BMI 50 -> +100°
    ratio = (b - 10) / (50 - 10)  # 0..1
    return -100 + ratio * 200     # [-100, +100]

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

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)
    cat_label = bmi_category(bmi)

    st.markdown(f"Your BMI is **{bmi:.1f} ({cat_label})**")

    st.divider()
    st.subheader("BMI Gauge")

    angle = bmi_to_angle_deg(bmi)

    # HTML + D3 gauge with labels in each slice
       gauge_html = f"""
    <div id="gauge-root" style="width:700px; margin:0 auto; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"></div>

    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    (function() {{
        // ----- DATA FROM PYTHON -----
        const bmiText = {js_payload["bmi_text"]!r};
        const targetAngle = {js_payload["angle"]};

        // ----- SEGMENTS DEFINITIONS -----
        const segments = [
            {{ line1: "UNDERWEIGHT",    line2: "< 18.5" }},
            {{ line1: "NORMAL",         line2: "18.5 – 24.9" }},
            {{ line1: "OVERWEIGHT",     line2: "25.0 – 29.9" }},
            {{ line1: "OBESE",          line2: "30.0 – 39.9" }},
            {{ line1: "SEVERELY OBESE", line2: "≥ 40.0" }}
        ];

        // ----- LAYOUT CONSTANTS -----
        // plus large pour que les textes aux extrémités ne soient pas coupés
        const width = 700;
        const height = 360;

        const outerR = 230;   // rayon externe un peu plus grand
        const innerR = 150;   // rayon interne un peu plus grand
        const labelR = (innerR + outerR) / 2; // là où on va poser le texte

        // centre géometrique (pivot de l'aiguille)
        const centerX = width / 2;
        const centerY = 250;  // on descend un peu la jauge pour laisser de la place aux labels

        // jauge = -100° à +100°
        const startDeg = -100;
        const endDeg = 100;
        const totalArc = endDeg - startDeg;           // 200 deg
        const arcPerSeg = totalArc / segments.length; // 40 deg / segment

        // ----- CREATE SVG -----
        const container = d3.select("#gauge-root");
        const svg = container.append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("background-color", "white");

        const g = svg.append("g");

        // ----- DRAW SEGMENTS + LABELS -----
        segments.forEach((seg, i) => {{
            const segStart = startDeg + i * arcPerSeg;
            const segEnd   = startDeg + (i + 1) * arcPerSeg;

            // arc shape
            const arcGen = d3.arc()
                .innerRadius(innerR)
                .outerRadius(outerR)
                .startAngle(segStart * Math.PI/180)
                .endAngle(segEnd * Math.PI/180);

            // yellow wedge
            g.append("path")
                .attr("d", arcGen)
                .attr("fill", "#F4C542")
                .attr("stroke", "white")
                .attr("stroke-width", 6)
                .attr("transform", `translate(${centerX}, ${centerY})`);

            // middle angle of this wedge
            const midDeg = (segStart + segEnd)/2;
            const midRad = midDeg * Math.PI/180;

            // label position
            // on rapproche un peu du centre pour être VISIBLE
            const lx = centerX + (labelR - 10) * Math.cos(midRad);
            const ly = centerY + (labelR - 10) * Math.sin(midRad);

            // We draw shadow (white stroke) behind black text to pop on yellow
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

        // aiguille : triangle fin
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

        // rond violet
        needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 24)
            .attr("fill", "#2E0A78")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

        // rond blanc au centre
        needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 9)
            .attr("fill", "white")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

        // ----- BMI TEXT sous la jauge -----
        g.append("text")
            .attr("x", centerX)
            .attr("y", centerY + 60)
            .text(bmiText)
            .attr("fill", "#1a1a1a")
            .attr("font-size", "22px")
            .attr("font-weight", "700")
            .attr("text-anchor", "middle");

        // ----- ANIMATION AIGUILLE -----
        needle
            .attr("transform", "rotate(-100)")
            .transition()
            .duration(800)
            .attr("transform", `rotate(${targetAngle})`);
    }})();
    </script>
    """
