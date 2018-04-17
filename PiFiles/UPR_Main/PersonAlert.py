import requests
import boto3
import time
import json
import subprocess
import os
from datetime import datetime

#SERVER_URL = 'http://192.168.1.2:5000'
SERVER_URL = "http://uprlevelsecurity-flask.us-east-1.elasticbeanstalk.com"

S3_BUCKET_NAME = 'upr-level-security-videostorage'
AWS_ACCESS_KEY='AKIAJB3FPOUEBYT2UTTA'
AWS_SECRET_KEY='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'

def sendAlert(title, text, videoID):
    time = datetime.now().isoformat()
    if videoID != -1:
        data = {"title": title, "text": text, "time": time, "videoID": videoID}
    else:
        data = {"title": title, "text": text, "time": time}
    header = {'Content-type': 'application/json'}
    r = requests.post(SERVER_URL + "/api/alert", headers = header, data = json.dumps(data), verify = False)
    #print(r)

def upload_video(filename):    
    new_filename = os.path.splitext(filename)[0] + '.mp4'
    command = 'ffmpeg -i ' + filename + ' -c:v copy -f mp4 ' + new_filename
    output = subprocess.check_output(command, stdout=subprocess.PIPE)
    
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    s3.upload_file(new_filename, S3_BUCKET_NAME, new_filename) # local name, bucket, s3 filename

    timestamp = datetime.now().isoformat()

    data = {"timestamp": timestamp, "video": new_filename}
    
##    header = {'Content-type': 'application/json'}
    r = requests.post(SERVER_URL + "/api/video_upload", json=data)
    
    os.remove(new_filename)
    os.remove(filename)
    return r.json()['id']
