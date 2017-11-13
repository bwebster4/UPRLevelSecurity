from application import app

from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class Alert(db.Model):
	"""docstring for Alert"""
	
	id = db.Column(db.Integer, primary_key=True)
	header = db.Column(db.String(80), unique=True, nullable=False)
	information = db.Column(db.String(240), unique=True, nullable=False)

	def __repr__(self):
		return '<Header: {0}, Information: {1}>'.format(self.header, self.information)
