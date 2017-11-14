from application.models import db, Alert

db.drop_all()
db.create_all()

print Alert.query.all()