from flask import Flask
from flask_sqlalchemy import SQLAlchemy

application = Flask(__name__)
app = application # AWS Beanstalk requires it to be called application, but we can just use app for everything else because it's shorter
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://buterrier:ConshredSpybot@seniordesign-dbinstance.cqwafy63ykmq.us-east-1.rds.amazonaws.com/flaskdb'
db = SQLAlchemy(app)