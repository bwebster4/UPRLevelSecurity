from application.models import db, Alert, Video
from application import S3_BUCKET_NAME
import boto3
import random

from datetime import datetime

video = Video(timestamp=datetime.now(), video='test_video')
db.session.add(video)
db.session.commit()

titles = ["Human Detected", "Gauge Issue"]
texts = ["Human intruder detected at substation.", "An equipment guauge has been detected with a value outside the normal safety standards."]

for i in range(10):
	tt_index = random.randint(0, len(titles) - 1)
	alert = Alert(title=titles[tt_index], text=texts[tt_index], video_ref=video.id)
	try:
		db.session.add(alert)
		db.session.commit()
	except:
		print "Unexpected error:", sys.exc_info()[0]
		db.session.rollback()

alerts = Alert.query.all()
print alerts
