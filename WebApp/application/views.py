from flask import Flask, render_template, Response, request

from application import app
from application.models import Alert

@app.route("/")
def home():
    alerts = Alert.query.all()

    return render_template('home.html', alerts = alerts)

@app.route("/api/alert", methods=['POST'])
def create_alert():
    if not request.json or not 'title' in request.json:
        abort(400)
    alert = Alert(title=request.json['title'], text=request.json['text'])
    db.session.add(alert)
    db.session.commit()

    return jsonify(alert), 201