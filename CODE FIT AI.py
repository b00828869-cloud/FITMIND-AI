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

def bmi_to_angle_deg(bmi):
    # On mappe BMI 10 -> -100°, BMI 50 -> 100°
    # clamp
    b = max(10, min(50, bmi))
    ratio = (b - 10) / (50 - 10)  # 0..1
    angle = -100 + ratio * 200    # -100 to +100 degrees
    return angle

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)

    st.markdown(f"Your BMI is **{bmi:.1f}**")

    # category message
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

    # ---- HTML/CSS GAUGE ----
    # id="needle" is rotated using the computed angle
    gauge_html = f"""
    <div style="
        width: 400px;
        margin: 0 auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        text-align: center;
        color: #1a1a1a;
    ">
        <!-- container for the semi-circle gauge -->
        <div style="
            position: relative;
            width: 400px;
            height: 200px;
            margin: 0 auto;
        ">
            <!-- Each yellow segment is just an absolutely positioned arc using border-radius and clip-path -->
            <!-- We'll fake the 5 slices by stacking rotated wedges -->

            <!-- UNDERWEIGHT -->
            <div style="
                position:absolute;
                width:200px;
                height:200px;
                left:0;
                top:0;
                background:#F4C542;
                border-top-left-radius:200px;
                border-top-right-radius:0;
                border-bottom-right-radius:0;
                border-bottom-left-radius:0;
                clip-path: polygon(0% 100%, 0% 0%, 100% 0%, 80% 100%);
                transform-origin: 100% 100%;
                transform: translate(0px,0px) rotate(-100deg);
                border:4px solid white;
                box-sizing:border-box;
            ">
                <div style="
                    position:absolute;
                    left:35%;
                    top:30%;
                    transform:translate(-50%,-50%) rotate(100deg);
                    text-align:center;
                    font-weight:bold;
                    font-size:12px;
                    color:#1a1a1a;
                    line-height:1.2;
                ">
                    UNDERWEIGHT<br>&lt; 18.5
                </div>
            </div>

            <!-- NORMAL -->
            <div style="
                position:absolute;
                width:200px;
                height:200px;
                left:0;
                top:0;
                background:#F4C542;
                border-top-left-radius:200px;
                clip-path: polygon(0% 100%, 0% 0%, 100% 0%, 80% 100%);
                transform-origin: 100% 100%;
                transform: translate(0px,0px) rotate(-60deg);
                border:4px solid white;
                box-sizing:border-box;
            ">
                <div style="
                    position:absolute;
                    left:35%;
                    top:30%;
                    transform:translate(-50%,-50%) rotate(60deg);
                    text-align:center;
                    font-weight:bold;
                    font-size:12px;
                    color:#1a1a1a;
                    line-height:1.2;
                ">
                    NORMAL<br>18.5 – 24.9
                </div>
            </div>

            <!-- OVERWEIGHT -->
            <div style="
                position:absolute;
                width:200px;
                height:200px;
                left:0;
                top:0;
                background:#F4C542;
                border-top-left-radius:200px;
                clip-path: polygon(0% 100%, 0% 0%, 100% 0%, 80% 100%);
                transform-origin: 100% 100%;
                transform: translate(0px,0px) rotate(-20deg);
                border:4px solid white;
                box-sizing:border-box;
            ">
                <div style="
                    position:absolute;
                    left:35%;
                    top:30%;
                    transform:translate(-50%,-50%) rotate(20deg);
                    text-align:center;
                    font-weight:bold;
                    font-size:12px;
                    color:#1a1a1a;
                    line-height:1.2;
                ">
                    OVERWEIGHT<br>25.0 – 29.9
                </div>
            </div>

            <!-- OBESE -->
            <div style="
                position:absolute;
                width:200px;
                height:200px;
                left:0;
                top:0;
                background:#F4C542;
                border-top-left-radius:200px;
                clip-path: polygon(0% 100%, 0% 0%, 100% 0%, 80% 100%);
                transform-origin: 100% 100%;
                transform: translate(0px,0px) rotate(20deg);
                border:4px solid white;
                box-sizing:border-box;
            ">
                <div style="
                    position:absolute;
                    left:35%;
                    top:30%;
                    transform:translate(-50%,-50%) rotate(-20deg);
                    text-align:center;
                    font-weight:bold;
                    font-size:12px;
                    color:#1a1a1a;
                    line-height:1.2;
                ">
                    OBESE<br>30.0 – 39.9
                </div>
            </div>

            <!-- SEVERELY OBESE -->
            <div style="
                position:absolute;
                width:200px;
                height:200px;
                left:0;
                top:0;
                background:#F4C542;
                border-top-left-radius:200px;
                clip-path: polygon(0% 100%, 0% 0%, 100% 0%, 80% 100%);
                transform-origin: 100% 100%;
                transform: translate(0px,0px) rotate(60deg);
                border:4px solid white;
                box-sizing:border-box;
            ">
                <div style="
                    position:absolute;
                    left:35%;
                    top:30%;
                    transform:translate(-50%,-50%) rotate(-60deg);
                    text-align:center;
                    font-weight:bold;
                    font-size:12px;
                    color:#1a1a1a;
                    line-height:1.2;
                ">
                    SEVERELY OBESE<br>≥ 40.0
                </div>
            </div>

            <!-- Needle -->
            <div style="
                position:absolute;
                left:200px;
                top:200px;
                width:0;
                height:0;
                transform-origin: 0 0;
                transform: rotate({angle}deg) translate(0,-5px);
            ">
                <!-- purple triangle needle -->
                <div style="
                    width:0;
                    height:0;
                    border-left:4px solid transparent;
                    border-right:4px solid transparent;
                    border-bottom:120px solid #2E0A78;
                    position:absolute;
                    left:-4px;
                    top:-120px;
                "></div>

                <!-- purple circle base -->
                <div style="
                    width:40px;
                    height:40px;
                    background:#2E0A78;
                    border-radius:50%;
                    position:absolute;
                    left:-20px;
                    top:-20px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    border:3px solid #2E0A78;
                ">
                    <div style="
                        width:18px;
                        height:18px;
                        background:white;
                        border-radius:50%;
                        border:3px solid #2E0A78;
                    "></div>
                </div>
            </div>
        </div>

        <div style="margin-top:16px; font-size:20px; font-weight:600; color:#1a1a1a;">
            BMI: {bmi:.1f} ({cat_label})
        </div>
    </div>
    """

    components.html(gauge_html, height=320)

    st.caption(
        "This gauge shows where you are. BMI is only an indicator. "
        "Muscle mass, age, and medical conditions matter."
    )

