import streamlit as st

st.set_page_config(
    page_title="FitMind AI - BMI Advisor",
    page_icon="💪",
    layout="centered"
)

# -------------------------------
# Helper functions
# -------------------------------
def calculate_bmi(weight, height):
    return weight / (height ** 2)

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

def bmi_advice(bmi, category):
    if category == "UNDERWEIGHT":
        return (
            "Your BMI indicates that you are **underweight**.\n\n"
            "👉 A healthy BMI usually ranges between **18.5 and 24.9**.\n\n"
            "You may need to **increase your caloric intake** and focus on foods rich in healthy fats and proteins. "
            "Consider strength training to gain muscle mass. If your weight loss is unintentional, consult a doctor or nutritionist."
        )
    elif category == "NORMAL":
        return (
            "🎉 Congratulations! Your BMI is within the **healthy range (18.5 – 24.9)**.\n\n"
            "Keep maintaining a **balanced diet**, regular **physical activity**, and good **sleep habits**. "
            "You can still focus on improving your body composition by increasing muscle mass or maintaining endurance."
        )
    elif category == "OVERWEIGHT":
        return (
            "⚠️ Your BMI indicates **overweight**.\n\n"
            "The healthy range is **18.5 – 24.9**. You are above that, which might increase the risk of cardiovascular issues over time.\n\n"
            "✅ Tips:\n"
            "- Focus on a slight **caloric deficit** (eat fewer calories than you burn).\n"
            "- Increase **physical activity**: cardio + strength training.\n"
            "- Monitor progress gradually — even losing **5–10% of your body weight** can improve your health significantly."
        )
    elif category == "OBESE":
        return (
            "🚨 Your BMI indicates **obesity (30.0 – 39.9)**.\n\n"
            "This range is associated with higher risks for **diabetes, hypertension, and cardiovascular disease**.\n\n"
            "✅ Recommendations:\n"
            "- Consult a healthcare professional for a personalized plan.\n"
            "- Adopt a **sustainable nutrition plan**, not a restrictive one.\n"
            "- Begin with **low-impact activities** (walking, swimming, cycling).\n"
            "- Track small wins — long-term consistency matters more than rapid loss."
        )
    else:  # SEVERELY OBESE
        return (
            "🚨 Your BMI indicates **severe obesity (≥ 40)**.\n\n"
            "This range significantly increases the risk of chronic conditions. "
            "It is important to get **medical supervision** to design a safe, long-term strategy.\n\n"
            "✅ Next steps:\n"
            "- Seek medical and nutritional support (doctor, dietitian, coach).\n"
            "- Focus on **gradual weight loss** and improving **daily mobility**.\n"
            "- Remember: sustainable change is possible, and every effort counts."
        )

# -------------------------------
# App layout
# -------------------------------
st.title("FitMind AI - Personalized BMI Analysis 💡")
st.write(
    "This tool helps you understand your **Body Mass Index (BMI)** and gives you tailored advice "
    "to help you reach and maintain a healthy range."
)

col1, col2 = st.columns(2)
with col1:
    weight = st.number_input("Weight (kg):", min_value=30.0, max_value=250.0, step=0.5, value=75.0)
with col2:
    height = st.number_input("Height (m):", min_value=1.2, max_value=2.2, step=0.01, value=1.75)

if st.button("Calculate BMI"):
    bmi = calculate_bmi(weight, height)
    category = bmi_category(bmi)

    st.markdown(f"## 🧮 Your BMI: **{bmi:.1f}**")
    st.markdown(f"### Category: **{category}**")

    st.divider()
    st.markdown(bmi_advice(bmi, category))

