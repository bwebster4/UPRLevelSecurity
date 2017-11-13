from flask import Flask, render_template, Response, request
application = Flask(__name__)
app = application # AWS Beanstalk requires it to be called application, but we can just use app for everything else because it's shorter

@app.route("/")
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run()