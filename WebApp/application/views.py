from flask import Flask, render_template, Response, request

from application import app
from application.models import Alert

@app.route("/")
def home():
	alerts = Alert.query.all()

	return render_template('home.html', alerts = alerts)
