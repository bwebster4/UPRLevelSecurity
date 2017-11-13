Repository for senior design project

WebApp in WebApp folder
Commands to set up the WebApp (all to be run in WebApp directory):
```
pip install virtualenv
virtualenv venv
. venv/bin/activate
git clone https://github.com/bwebster4/UPRLevelSecurity.git
git checkout develop


pip install -r requirements.txt
export FLASK_APP=application
export FLASK_DEBUG=true
pip install -e .
python
cd application
from application.models import db
db.create_all()

// if you want to add something to the database, like a test alert:
from application.models import Alert
alert = Alert(title="Test", text="Test text")
db.session.add(alert)
db.session.commit()

quit()
```
To run the webapp:

`flask run`


Useful Links:
Doc page for a minimal Flask App, has a little bit of information on just about everything, good place to start: http://flask.pocoo.org/docs/0.12/quickstart/#a-minimal-application

Amazon AWS (Elastic Beanstalk) Docs page for setting up Flask with Beanstalk:
http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html#configure-your-flask-application-for-eb

Slightly more helpful guide specifically on using AWS Beanstalk with Flask:
http://blog.uptill3.com/2012/08/25/python-on-elastic-beanstalk.html