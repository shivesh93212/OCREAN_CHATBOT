from flask import Flask, render_template, request, jsonify, Response, url_for
import requests
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Predefined Q&A
qa_dict = {
    "how many percent earth cover by the ocean": "About 71% of the Earth's surface is covered by oceans.",
    "how deep is the deepest part of the ocean": "The Mariana Trench is the deepest part of the ocean, reaching about 11,034 meters.",
    "what is the largest ocean": "The Pacific Ocean is the largest ocean on Earth.",
    "what is the smallest ocean": "The Arctic Ocean is the smallest ocean on Earth."
}

# Get live ocean temperature & wind using WorldWeatherOnline API
def get_ocean_weather(lat=3.0, lon=73.0):
    try:
        url = f"http://api.worldweatheronline.com/premium/v1/marine.ashx?key=b7b4493409f745e18c241556251109&q={lat},{lon}&format=json"
        response = requests.get(url).json()

        weather = response.get("data", {}).get("weather", [])
        if not weather:
            return {"temperature": "N/A", "wind_speed": "N/A"}

        hourly = weather[0].get("hourly", [])
        if not hourly:
            return {"temperature": "N/A", "wind_speed": "N/A"}

        last_entry = hourly[-1]
        temp = last_entry.get("waterTemp_C", "N/A")
        wind = last_entry.get("windspeedKmph", "N/A")

        return {"temperature": temp, "wind_speed": wind}
    except Exception as e:
        print("Error:", e)
        return {"temperature": "N/A", "wind_speed": "N/A"}

# Get ocean depth using OpenTopoData API
def get_ocean_depth(lat=3.0, lon=73.0):
    try:
        url = f"https://api.opentopodata.org/v1/etopo1?locations={lat},{lon}"
        response = requests.get(url).json()
        depth = response['results'][0]['elevation']
        return abs(depth)  # depth below sea level
    except:
        return "N/A"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/graph')
def graph_page():
    return render_template("graph.html")

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get("question", "").lower()
    
    # FIX ✅ lat/lon string → float
    try:
        lat = float(request.form.get("lat", 3.0))
        lon = float(request.form.get("lon", 73.0))
    except ValueError:
        lat, lon = 3.0, 73.0

    for key in qa_dict:
        if key in user_input:
            return jsonify({"answer": qa_dict[key]})

    if "temperature" in user_input:
        data = get_ocean_weather(lat, lon)
        answer = f"🌊 Current ocean temperature at ({lat},{lon}): {data['temperature']}°C"
        return jsonify({"answer": answer})

    if "wind" in user_input:
        data = get_ocean_weather(lat, lon)
        answer = f"🌬️ Current wind speed at ({lat},{lon}): {data['wind_speed']} km/h"
        return jsonify({"answer": answer})

    if "depth" in user_input:
        depth = get_ocean_depth(lat, lon)
        answer = f"🌊 The ocean depth at ({lat},{lon}) is approximately {depth} meters."
        return jsonify({"answer": answer})

    return jsonify({"answer": "Sorry, I don't have an answer for that yet."})

# ---------- GRAPH ROUTE ----------
@app.route('/graph/trend')
def graph_trend():
    years = [2020, 2021, 2022, 2023, 2024]
    temps = [27.5, 28.1, 27.9, 28.4, 28.0]

    plt.figure(figsize=(7, 4))
    for i in range(1, len(years)):
        color = "green" if temps[i] > temps[i-1] else "red"
        plt.plot(years[i-1:i+1], temps[i-1:i+1], marker="o", color=color, linewidth=2)

    plt.title("🌡️ Ocean Temperature Trend", fontsize=14, color="navy")
    plt.xlabel("Year")
    plt.ylabel("Temperature (°C)")
    plt.grid(True, linestyle="--", alpha=0.5)

    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=120)
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
