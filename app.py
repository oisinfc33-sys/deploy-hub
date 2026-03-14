import os
import uuid
import time
import logging
import requests
import psycopg
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def get_db():
    return psycopg.connect(DATABASE_URL)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS searches (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100),
                    temperature FLOAT,
                    description VARCHAR(200),
                    searched_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()

@app.route("/")
def index():
    request_id = str(uuid.uuid4())
    logger.info(f"request_id={request_id} path=/")
    return render_template("index.html")

@app.route("/weather")
def weather():
    request_id = str(uuid.uuid4())
    city = request.args.get("city", "Dublin")
    start = time.time()
    logger.info(f"request_id={request_id} path=/weather city={city}")
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO searches (city, temperature, description) VALUES (%s, %s, %s)",
                    (city, temp, description)
                )
            conn.commit()
        duration = round(time.time() - start, 3)
        logger.info(f"request_id={request_id} duration={duration}s status=success")
        return jsonify({"city": city, "temperature": temp, "description": description, "request_id": request_id})
    except requests.exceptions.RequestException as e:
        logger.error(f"request_id={request_id} error={str(e)}")
        return jsonify({"error": "Weather service unavailable", "request_id": request_id}), 503

@app.route("/history")
def history():
    request_id = str(uuid.uuid4())
    logger.info(f"request_id={request_id} path=/history")
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT city, temperature, description, searched_at FROM searches ORDER BY searched_at DESC LIMIT 10")
                rows = cur.fetchall()
        results = [{"city": r[0], "temperature": r[1], "description": r[2], "searched_at": str(r[3])} for r in rows]
        return jsonify(results)
    except Exception as e:
        logger.error(f"request_id={request_id} error={str(e)}")
        return jsonify({"error": "Database unavailable"}), 503

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/status")
def status():
    db_ok = False
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass
    weather_ok = False
    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q=Dublin&appid={WEATHER_API_KEY}&units=metric",
            timeout=5
        )
        weather_ok = r.status_code == 200
    except Exception:
        pass
    return jsonify({
        "database": "ok" if db_ok else "unavailable",
        "weather_api": "ok" if weather_ok else "unavailable"
    }), 200 if (db_ok and weather_ok) else 503

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
