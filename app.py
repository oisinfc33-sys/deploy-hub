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
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS searches (
                        id SERIAL PRIMARY KEY,
                        city VARCHAR(100),
                        temperature FLOAT,
                        description VARCHAR(200),
                        country_code VARCHAR(10),
                        searched_at TIMESTAMP DEFAULT NOW()
                    )
                """)
            conn.commit()
        logger.info("Database initialised successfully")
    except Exception as e:
        logger.warning(f"Database init failed: {str(e)}")

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
        response = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        country_code = data["sys"]["country"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"] * 3.6
        visibility = data.get("visibility")
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO searches (city, temperature, description, country_code) VALUES (%s, %s, %s, %s)",
                        (city, temp, description, country_code)
                    )
                conn.commit()
        except Exception as db_err:
            logger.warning(f"request_id={request_id} db_write_failed={str(db_err)}")
        duration = round(time.time() - start, 3)
        logger.info(f"request_id={request_id} duration={duration}s status=success")
        return jsonify({
            "city": data["name"],
            "temperature": temp,
            "description": description,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "visibility": visibility,
            "country_code": country_code,
            "request_id": request_id
        })
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
                cur.execute("""
                    SELECT city, temperature, description, country_code, searched_at
                    FROM searches ORDER BY searched_at DESC LIMIT 10
                """)
                rows = cur.fetchall()
        results = [{"city": r[0], "temperature": r[1], "description": r[2], "country_code": r[3], "searched_at": str(r[4])} for r in rows]
        return jsonify(results)
    except Exception as e:
        logger.error(f"request_id={request_id} error={str(e)}")
        return jsonify([])

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
            "http://api.openweathermap.org/data/2.5/weather",
            params={"q": "Dublin", "appid": WEATHER_API_KEY, "units": "metric"},
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
