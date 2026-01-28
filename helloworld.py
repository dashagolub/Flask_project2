from flask import Flask, request, jsonify, render_template_string
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://localhost/sensors"
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
</head>
<body>
    <h1>Bamboo Watering System</h1>
    <h2>Water Level Monitoring</h2>
    <ul id="list"></ul>
    <script>
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const list = document.getElementById('list');
                data.forEach(row => {
                    const item = document.createElement('li');
                    item.textContent = `💧 ${row.water_level}% | 🕰️ ${row.timestamp}`;
                    list.appendChild(item);
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

@app.route("/data", methods=["GET"])
def get_data():
    session = Session()
    sensor_data = session.query(SensorData)\
        .order_by(SensorData.timestamp.desc())\
        .limit(10)\
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

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True)
    water_level = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)



#app.run(debug=True)
app.run(host="0.0.0.0", port=5001, debug=True)