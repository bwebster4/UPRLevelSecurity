from flask import Flask, render_template, Response, request, jsonify, redirect, url_for

from application import app
from application.models import Alert, db

#Route for the home page
@app.route("/", methods=['POST', 'GET'])
def home():

    alerts = Alert.query.all()

    return render_template('home.html', alerts = alerts)

    
#Route for the robot control page
@app.route("/control", methods=['POST', 'GET'])
def control():

    return render_template('control.html')


#Route for the full records page
@app.route("/records", methods=['POST', 'GET'])
def records():

    return render_template('records.html')


#Route for the login page
@app.route("/login/", methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('home'))
    return render_template('login.html', error=error)


#API for receiving alerts
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