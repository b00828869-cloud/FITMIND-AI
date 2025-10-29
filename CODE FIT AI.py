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
    # Clamp BMI into [10, 50] so needle never goes out of range
    b = max(10, min(50, bmi))
    # Map 10 -> -100°, 50 -> +100°
    ratio = (b - 10) / (50 - 10)  # 0..1
    return -100 + ratio * 200     # [-100, +100] degrees

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)

    st.markdown(f"Your BMI is **{bmi:.1f}**")

    # choose label for message box
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

    angle = bmi_to_angle_deg(bmi)

    # ------- D3.js gauge HTML block -------
    gauge_html = f"""
    <html>
      <head>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
          body {{
            background-color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #1a1a1a;
          }}

          .segment-label {{
            font-size: 11px;
            fill: #1a1a1a;
            font-weight: 600;
            text-anchor: middle;
          }}

          .bmi-readout {{
            font-size: 20px;
            font-weight: 600;
            fill: #1a1a1a;
            text-anchor: middle;
          }}
        </style>
      </head>
      <body>
        <div id="gauge-container" style="width:500px; margin:0 auto;"></div>

        <script>
          // SVG / layout config
          const width = 500;
          const height = 260;
          const outerR = 180;      // outer radius of the gauge band
          const innerR = 110;      // inner radius of the gauge band
          const centerX = width / 2;
          const centerY = 200;     // push gauge up/down visually

          // Gauge covers -100° to +100°
          const startDeg = -100;
          const endDeg = 100;

          // Our 5 slices across that arc, evenly spaced
          const segments = [
            {{ name1: "UNDERWEIGHT",    name2: "< 18.5" }},
            {{ name1: "NORMAL",         name2: "18.5 – 24.9" }},
            {{ name1: "OVERWEIGHT",     name2: "25.0 – 29.9" }},
            {{ name1: "OBESE",          name2: "30.0 – 39.9" }},
            {{ name1: "SEVERELY OBESE", name2: "≥ 40.0" }},
          ];

          const totalArc = endDeg - startDeg;             // 200 deg
          const arcPerSeg = totalArc / segments.length;   // 40 deg each

          // Create SVG
          const svg = d3.select("#gauge-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

          const g = svg.append("g");

          // Draw each yellow wedge
          segments.forEach((seg, i) => {{
            const segStart = startDeg + i * arcPerSeg;
            const segEnd   = startDeg + (i+1) * arcPerSeg;

            const arcGen = d3.arc()
              .innerRadius(innerR)
              .outerRadius(outerR)
              .startAngle(segStart * Math.PI/180)
              .endAngle(segEnd * Math.PI/180);

            g.append("path")
              .attr("d", arcGen)
              .attr("fill", "#F4C542")
              .attr("stroke", "white")
              .attr("stroke-width", 4)
              .attr("transform", `translate(${{centerX}}, ${{centerY}})`);

            // Mid-angle for label placement
            const midDeg = (segStart + segEnd)/2;
            const midRad = midDeg * Math.PI/180;
            const labelR = (innerR + outerR)/2;

            const lx = centerX + labelR * Math.cos(midRad);
            const ly = centerY + labelR * Math.sin(midRad);

            // two-line label
            g.append("text")
              .attr("class", "segment-label")
              .attr("x", lx)
              .attr("y", ly - 6)
              .text(seg.name1)
              .attr("text-anchor", "middle");

            g.append("text")
              .attr("class", "segment-label")
              .attr("x", lx)
              .attr("y", ly + 10)
              .text(seg.name2)
              .attr("text-anchor", "middle");
          }});

          // Needle group at center
          const needleGroup = g.append("g")
            .attr("transform", `translate(${{centerX}}, ${{centerY}})`);

          // Needle shape (triangle-ish)
          const needleLen = 125;
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

          // Purple circle base
          needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 20)
            .attr("fill", "#2E0A78")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

          // White inner circle
          needleGroup.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 8)
            .attr("fill", "white")
            .attr("stroke", "#2E0A78")
            .attr("stroke-width", 3);

          // BMI text under gauge
          g.append("text")
            .attr("class", "bmi-readout")
            .attr("x", centerX)
            .attr("y", centerY + 40)
            .text("BMI: {bmi:.1f} ({cat_label})");

          // Animate needle from far left (-100deg) to target angle
          const targetAngle = {angle};

          needle
            .attr("transform", "rotate(-100)")
            .transition()
            .duration(800)
            .attr("transform", `rotate(${{targetAngle}})`);
        </script>
      </body>
    </html>
    """

    # Render the custom HTML/JS block inside Streamlit
    components.html(gauge_html, height=320)

    st.caption(
        "This gauge is interactive (D3.js). BMI is only an indicator. "
        "Muscle mass, age, and medical conditions matter."
    )
