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
    <html>
      <head>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
          body {{
            background-color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #1a1a1a;
          }}

          .segment-line1 {{
            font-size: 12px;
            fill: #1a1a1a;
            font-weight: 700;
            text-anchor: middle;
          }}

          .segment-line2 {{
            font-size: 11px;
            fill: #1a1a1a;
            font-weight: 500;
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
        <div id="gauge-container" style="width:600px; margin:0 auto;"></div>

        <script>
          // --- Layout config ---
          const width = 600;
          const height = 320;

          // Radii of the arc
          const outerR = 200;
          const innerR = 130;

          // Where the gauge sits
          const centerX = width / 2;
          const centerY = 220;

          // Gauge spans from -100deg to +100deg
          const startDeg = -100;
          const endDeg = 100;

          // 5 segments across the arc
          const segments = [
            {{
              line1: "UNDERWEIGHT",
              line2: "< 18.5"
            }},
            {{
              line1: "NORMAL",
              line2: "18.5 – 24.9"
            }},
            {{
              line1: "OVERWEIGHT",
              line2: "25.0 – 29.9"
            }},
            {{
              line1: "OBESE",
              line2: "30.0 – 39.9"
            }},
            {{
              line1: "SEVERELY OBESE",
              line2: "≥ 40.0"
            }}
          ];

          const totalArc = endDeg - startDeg;          // 200 deg
          const arcPerSeg = totalArc / segments.length; // 40 deg/segment

          // Create SVG
          const svg = d3.select("#gauge-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

          const g = svg.append("g");

          // Draw each wedge + text
          segments.forEach((seg, i) => {{
            const segStart = startDeg + i * arcPerSeg;
            const segEnd   = startDeg + (i + 1) * arcPerSeg;

            // The slice shape
            const arcGen = d3.arc()
              .innerRadius(innerR)
              .outerRadius(outerR)
              .startAngle(segStart * Math.PI/180)
              .endAngle(segEnd * Math.PI/180);

            // Draw the colored band piece
            g.append("path")
              .attr("d", arcGen)
              .attr("fill", "#F4C542")
              .attr("stroke", "white")
              .attr("stroke-width", 5)
              .attr("transform", `translate(${{centerX}}, ${{centerY}})`);

            // Compute label anchor point (middle angle)
            const midDeg = (segStart + segEnd)/2;
            const midRad = midDeg * Math.PI/180;
            const labelR = (innerR + outerR)/2; // halfway inside wedge

            const lx = centerX + labelR * Math.cos(midRad);
            const ly = centerY + labelR * Math.sin(midRad);

            // Two-line label (line1 bold caps, line2 range)
            g.append("text")
              .attr("class", "segment-line1")
              .attr("x", lx)
              .attr("y", ly - 6)
              .text(seg.line1)
              .attr("text-anchor", "middle");

            g.append("text")
              .attr("class", "segment-line2")
              .attr("x", lx)
              .attr("y", ly + 12)
              .text(seg.line2)
              .attr("text-anchor", "middle");
          }});

          // ----- Needle -----
          const needleGroup = g.append("g")
            .attr("transform", `translate(${{centerX}}, ${{centerY}})`);

          // needle shape: a slim triangle pointing straight up (0deg = up)
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

          // BMI text under gauge (centered)
          g.append("text")
            .attr("class", "bmi-readout")
            .attr("x", centerX)
            .attr("y", centerY + 50)
            .text("BMI: {bmi:.1f} ({cat_label})")
            .attr("text-anchor", "middle");

          // Animate needle rotation
          const targetAngle = {angle}; // from Python, -100 to +100 deg

          needle
            .attr("transform", "rotate(-100)") // start far left
            .transition()
            .duration(800)
            .attr("transform", `rotate(${{targetAngle}})`);
        </script>
      </body>
    </html>
    """

    # Inject HTML/JS gauge into Streamlit
    components.html(gauge_html, height=360)

    st.caption(
        "This gauge is interactive (D3.js). BMI is only an indicator. "
        "Muscle mass, age, and medical conditions matter."
    )


