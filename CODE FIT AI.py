import streamlit as st

st.title("FitMind AI - BMI Calculator 🧮")

weight = st.number_input("Enter your weight (kg):", min_value=30.0, max_value=200.0, step=0.1)
height = st.number_input("Enter your height (m):", min_value=1.2, max_value=2.2, step=0.01)

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)
    st.write(f"Your BMI is **{bmi:.1f}**")

    if bmi < 18.5:
        st.warning("Underweight")
    elif bmi < 25:
        st.success("Normal weight")
    elif bmi < 30:
        st.info("Overweight")
    elif bmi < 35:
        st.warning("Obesity (Class I)")
    elif bmi < 40:
        st.error("Obesity (Class II)")
    else:
        st.error("Obesity (Class III)")
