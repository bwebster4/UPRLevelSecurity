
from flask import Flask, render_template, Response
application = Flask(__name__)
app = application # AWS Beanstalk requires it to be called application, but we can just use app for everything else because it's shorter

from importlib import import_module
Camera = import_module('camera_opencv').Camera

@app.route("/")
def home():
    return render_template('home.html')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run()