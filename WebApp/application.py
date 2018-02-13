from flask import Flask, render_template, Response, request, jsonify, redirect, url_for, session, flash, abort, g
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
import boto3

from application import db, app, S3_BUCKET_NAME
import application.models as models

application = app
application.debug=True

VIDEO_FORMAT = ".mp4"

#-------------------------------------------LOGIN RELATED WORK------------------------------------------

#Login Manager Instatiation
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Loading user based on ID
@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))


#Register page, might get rid of it but just for ease of use
@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    user = models.User(request.form['username'] , request.form['password'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))


#Route for the login page
@app.route("/login/", methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = models.User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('home'))


#Saving user's profile
@app.before_request
def before_request():
    g.user = current_user


#Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) 


#---------------------------------------END OF LOGIN RELATED WORK-------------------------------------
#Route for the home page
@app.route("/", methods=['POST', 'GET'])
@login_required
def home():
    alerts = models.Alert.query.all()
    return render_template('home.html', alerts = alerts)

    
#Route for the robot control page
@app.route("/control", methods=['POST', 'GET'])
@login_required
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
@login_required
def records():
    return render_template('records.html')


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
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    application.run()