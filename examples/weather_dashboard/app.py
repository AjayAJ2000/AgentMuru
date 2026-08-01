import brickflowui as db
import random
import time
import asyncio

app = db.App(title="WeatherFlow Dashboard")

# Mock data generation
def get_weather_data(city):
    current_temp = random.randint(15, 30)
    history = [
        {"time": f"{h:02d}:00", "temp": current_temp + random.randint(-5, 5)}
        for h in range(0, 24, 2)
    ]
    return {
        "city": city,
        "temp": current_temp,
        "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
        "humidity": random.randint(30, 80),
        "history": history
    }

@app.page("/", title="Current Weather", icon="Sun")
def weather_home():
    city, set_city = db.use_state("San Francisco")
    weather, set_weather = db.use_state(get_weather_data("San Francisco"))
    loading, set_loading = db.use_state(False)

    async def fetch_weather():
        set_loading(True)
        # Simulate network delay
        await asyncio.sleep(1)
        set_weather(get_weather_data(city))
        set_loading(False)

    return db.Column([
        db.Card([
            db.Row([
                db.Input(
                    name="city",
                    label="Search City", 
                    value=city, 
                    on_change=set_city,
                    placeholder="Enter city name..."
                ),
                db.Button(
                    "Search", 
                    variant="primary", 
                    on_click=lambda: asyncio.create_task(fetch_weather()),
                    disabled=loading
                )
            ], gap=4, align="end")
        ]),

        db.Grid([
            db.Card([
                db.Stat(
                    label="Current Temperature", 
                    value=f"{weather['temp']}°C", 
                    delta="+2°C", 
                    delta_type="increase"
                )
            ]),
            db.Card([
                db.Stat(
                    label="Condition", 
                    value=weather['condition']
                )
            ]),
            db.Card([
                db.Stat(
                    label="Humidity", 
                    value=f"{weather['humidity']}%"
                )
            ])
        ], cols=3, gap=4),

        db.Card([
            db.Text("24h Temperature Trend", variant="h3"),
            db.AreaChart(
                data=weather['history'], 
                x_key="time", 
                y_keys=["temp"],
                colors=["#3b82f6"]
            )
        ], title="Analytics")
    ], padding=8, gap=6)

@app.page("/forecast", title="7-Day Forecast", icon="Calendar")
def forecast_page():
    # Simple static list for demo
    forecast = [
        {"day": "Mon", "high": 22, "low": 15},
        {"day": "Tue", "high": 24, "low": 16},
        {"day": "Wed", "high": 21, "low": 14},
        {"day": "Thu", "high": 20, "low": 13},
        {"day": "Fri", "high": 25, "low": 18},
        {"day": "Sat", "high": 27, "low": 19},
        {"day": "Sun", "high": 23, "low": 17},
    ]

    return db.Column([
        db.Text("7-Day Forecast", variant="h2"),
        db.Table(
            data=forecast,
            columns=[
                {"key": "day", "label": "Day"},
                {"key": "high", "label": "High (°C)"},
                {"key": "low", "label": "Low (°C)"}
            ]
        ),
        db.BarChart(
            data=forecast,
            x_key="day",
            y_keys=["high", "low"],
            colors=["#ef4444", "#3b82f6"]
        )
    ], padding=8, gap=6)

if __name__ == "__main__":
    app.run()
