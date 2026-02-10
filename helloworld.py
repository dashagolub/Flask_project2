from flask import Flask, request, jsonify, render_template_string
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from datetime import timedelta
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

app = Flask(__name__)
@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bamboo Watering System</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>🎋Bamboo Watering System🎋</h1>
    <h2 id="warning" style="color: red; display: none;">⚠️ Water level is too low!</h2>
    <h2>Water Level Monitoring (last 5 days)</h2>
    <canvas id="waterChart" width="400" height="200"></canvas>
    <ul id="list"></ul>
    <script>
        fetch('/data/list')
            .then(response => response.json())
            .then(data => {
                const list = document.getElementById('list');
                const warning = document.getElementById('warning');
                data.forEach(row => {
                    const item = document.createElement('li');
                    item.textContent = `💧 ${row.water_level}| 🕰️ ${row.timestamp}`;
                    list.appendChild(item);
                });
                if (data.length > 0 && data[0].water_level < 500) {
                    warning.style.display = 'block';
                }
            });
    </script>
    <script>
    fetch('/data/chart')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.timestamp);
            const values = data.map(item => item.water_level);

            const ctx = document.getElementById('waterChart').getContext('2d');

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Water level',
                        data: values,
                        borderColor: 'blue',
                        fill: false,
                        tension: 0.2
                    }]
                },
                options: {
                    scales: {
                        y: {
                            min: 0,
                            max: 600
                        }
                    }
                }
            });
        });
    </script>
</body>
</html>
""")

@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    session = Session()
    sensor_data = SensorData(
        water_level=data.get("water_level"),
        timestamp=datetime.utcnow()
    )
    session.add(sensor_data)
    session.commit()
    session.close()
    return jsonify({"status": "saved"})
    """
    print(data)
    return jsonify({
        "status": "ok",
        "received": data
    })"""

@app.route("/data/list", methods=["GET"])
def get_data():
    session = Session()
    sensor_data = session.query(SensorData)\
        .order_by(SensorData.timestamp.desc())\
        .limit(20)\
        .all()
    session.close()
    result = []
    for row in sensor_data:
        result.append({
            "id": row.id,
            "water_level": row.water_level,
            "timestamp": row.timestamp.isoformat()
        })
    return jsonify(result)

@app.route("/data/chart", methods=["GET"])
def get_chart_data():
    session = Session()

    days_chart = datetime.utcnow() - timedelta(days=5)

    rows = session.query(SensorData)\
        .filter(SensorData.timestamp >= days_chart)\
        .order_by(SensorData.timestamp.asc())\
        .all()

    session.close()

    result = []
    for row in rows:
        result.append({
            "timestamp": row.timestamp.strftime("%Y-%m-%d"),
            "water_level": row.water_level
        })

    return jsonify(result)

def delete_old_data():
    session = Session()
    border = datetime.utcnow() - timedelta(days=10)
    session.query(SensorData).filter(SensorData.timestamp < border).delete()
    session.commit()
    session.close()

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True)
    water_level = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)



#app.run(debug=True) index
Base.metadata.create_all(engine)
delete_old_data()
app.run(host="0.0.0.0", port=5001, debug=True)