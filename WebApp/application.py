from flask import Flask, render_template, Response, request, jsonify, redirect, url_for
import boto3

from application import db, app, S3_BUCKET_NAME
import application.models as models

application = app
application.debug=True

VIDEO_FORMAT = ".mp4"

#Route for the home page
@app.route("/", methods=['POST', 'GET'])
def home():

    alerts = models.Alert.query.all()

    return render_template('home.html', alerts = alerts)

    
#Route for the robot control page
@app.route("/control", methods=['POST', 'GET'])
def control():

    return render_template('control.html')


def download_video(video_id):
    video = models.Video.query.filter_by(id=video_id).first()
    s3 = boto3.client('s3')
    try:
        s3.BUCKET(S3_BUCKET_NAME).download_file(video.video + VIDEO_FORMAT, video.video + "_temp_local" + VIDEO_FORMAT)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

#Route for the full records page
@app.route("/records", methods=['POST', 'GET'])
def records():

    return render_template('records.html')


#Route for the login page
@app.route("/login/", methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        # if request.form['username'] != 'admin' or request.form['password'] != 'admin':
        #     error = 'Invalid Credentials. Please try again.'
        # else:
        #     return redirect(url_for('home'))
        return redirect(url_for('home'))
    return render_template('login.html', error=error)


#API for receiving alerts
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