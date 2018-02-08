from application.models import db, Alert
import random


titles = ["Human Detected", "Gauge Issue"]
texts = ["Human intruder detected at substation.", "An equipment guauge has been detected with a value outside the normal safety standards."]
videos = ["www.fake_awss3.fake/videos"]

for i in range(10):
	tt_index = random.randint(0, len(titles) - 1)
	alert = Alert(title=titles[tt_index], text=texts[tt_index], video_ref=videos[random.randint(0, len(videos) - 1)])
	try:
		db.session.add(alert)
		db.session.commit()
	except:
		print "Unexpected error:", sys.exc_info()[0]
		db.session.rollback()

alerts = Alert.query.all()
print alerts