from flask import Flask, render_template, request, redirect, session
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "phishguard_secret"

# -------------------------
# Load ML files
# -------------------------
model = pickle.load(open("xgboost_phishing_model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))
feature_names = pickle.load(open("feature_names.pkl", "rb"))

# -------------------------
# Temporary User Store
# -------------------------
TEMP_USERS = {}   # username : password

# -------------------------
# 1️⃣ HOME PAGE (Public)
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")

# -------------------------
# 2️⃣ REGISTER (Temporary)
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in TEMP_USERS:
            return render_template("register.html", error="User already exists")

        TEMP_USERS[u] = p
        return redirect("/login")

    return render_template("register.html")

# -------------------------
# 3️⃣ LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in TEMP_USERS and TEMP_USERS[u] == p:
            session["user"] = u
            return redirect("/predict")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# -------------------------
# 4️⃣ PREDICT PAGE
# -------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":
        values = [float(request.form[f]) for f in feature_names]
        df = pd.DataFrame([values], columns=feature_names)
        df_scaled = scaler.transform(df)

        pred = model.predict(df_scaled)[0]
        session["last_prediction"] = int(pred)

        result = "🚨 Phishing Website" if pred == 1 else "✅ Legitimate Website"

    return render_template(
        "predict.html",
        feature_names=feature_names,
        result=result
    )

# -------------------------
# 5️⃣ CHART PAGE
# -------------------------
@app.route("/chart")
def chart():
    if "last_prediction" not in session:
        return redirect("/predict")

    labels = ["Legitimate", "Phishing"]
    values = [1, 0] if session["last_prediction"] == 0 else [0, 1]

    if not os.path.exists("static"):
        os.mkdir("static")

    plt.figure()
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title("Prediction Result")
    plt.savefig("static/result.png")
    plt.close()

    return render_template("chart.html")

# -------------------------
# 6️⃣ LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
