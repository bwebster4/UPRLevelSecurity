from flask import Flask
from flask_sqlalchemy import SQLAlchemy

S3_BUCKET_NAME = 'upr-level-security-videostorage'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://buterrier:ConshredSpybot@seniordesign-dbinstance.cqwafy63ykmq.us-east-1.rds.amazonaws.com/flaskdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'video_storage_folder/'
db = SQLAlchemy(app)

# for local db: 'sqlite:///test.db'