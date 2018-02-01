from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://buterrier:ConshredSpybot@seniordesign-dbinstance.cqwafy63ykmq.us-east-1.rds.amazonaws.com/flaskdb'
db = SQLAlchemy(app)

# for local db: 'sqlite:///test.db'