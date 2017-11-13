from flask import Flask, render_template, Response, request, jsonify

from application import app
from application.models import Alert, db

@app.route("/")
def home():
    alerts = Alert.query.all()

    return render_template('home.html', alerts = alerts)

@app.route("/api/alert", methods=['POST'])
def create_alert():
    if not request.json or not 'title' in request.json or not 'text' in request.json:
        abort(400)
    alert = Alert(title=request.json['title'], text=request.json['text'])
    
    try:
        db.session.add(alert)
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)

    return jsonify(alert.serialize()), 201