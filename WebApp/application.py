from flask import Flask
application = Flask(__name__)
app = application # AWS Beanstalk requires it to be called application, but we can just use app for everything else because it's shorter

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()