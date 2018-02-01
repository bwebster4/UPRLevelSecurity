from flask import Flask, render_template, Response, request, jsonify

from application import db, app
import application.models as models

application = app
application.debug=True

@app.route("/", methods=['POST', 'GET'])
def home():

    alerts = models.Alert.query.all()

    return render_template('home.html', alerts = alerts)

@app.route("/api/alert", methods=['POST'])
def create_alert():
    if not request.json or not 'title' in request.json or not 'text' in request.json:
        abort(400)
    alert = models.Alert(title=request.json['title'], text=request.json['text'])
    
    try:
        db.session.add(alert)
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)

    return jsonify(alert.serialize()), 201


# This needs to be the last line
if __name__ == "__main__":
    application.run()