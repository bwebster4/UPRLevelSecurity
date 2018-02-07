from application import db
from sqlalchemy.sql import func

class Alert(db.Model):
	"""docstring for Alert"""
	
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(80), unique=False, nullable=False)
	text = db.Column(db.String(240), unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, unique=False, nullable=False, server_default=func.now())
	video_ref = db.Column(db.String(240), unique=False, nullable=True)


	def __repr__(self):
		return '<Title: {0}, Text: {1}, Timestamp: {2}, Video Reference: {3}>'.format(self.title, self.text, self.timestamp, self.video_ref)

	def serialize(self):
		return {
					"title":self.title,
					"text":self.text
				}


class Video(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(db.DateTime, unique=False, nullable=False)
	video = db.Column(db.String(240), unique=False, nullable=False)

	def __repr__(self):
		return '<Timestamp: {0}, Video URL: {1}>'.format(self.timestamp, self.video)


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=False, nullable=False)
	password = db.Column(db.String(80), unique=False, nullable=False)

	def __repr__(self):
		return '<Username: {0}, Password: {1}>'.format(self.username, self.password)