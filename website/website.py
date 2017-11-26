import os
import re
import smtplib
import sys

from os import listdir, getenv
from os.path import join, isfile, isdir, basename
from datetime import date
from email.mime.text import MIMEText
from flask import Flask, request, g, abort, render_template, jsonify

import secrets
import skills

app = Flask(__name__)
app.config.update(dict(
    DEBUG=False,
    SECRET_KEY=secrets.token_hex(40),
))
passwd = getenv("google_passwd")
assert passwd is not None and passwd != ""


def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


@app.route('/')
def index():
    skills_list = sorted(skills.skills, key=lambda x: -x["note"])
    age = calculate_age(date.fromtimestamp(799804800))
    return render_template('index.html', skills=skills_list, age=age)


@app.route('/contact', methods=['POST'])
def send_mail():
    sender = request.form['sender'].encode('ascii', errors='ignore').decode('ascii')
    receiver = 'hugodelval@gmail.com'
    message = request.form['message'].encode('ascii', errors='ignore').decode('ascii')
    response = {}
    if not isinstance(sender, str) or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', sender):
        response["msg"] = "Your email is empty or invalid."
    if not isinstance(message, str) or len(message) < 10 or len(message) > 10000:
        response["msg"] = "Your email is either too short or too long."
    if response.get("msg"):
        resp = jsonify(**response)
        resp.status_code = 500
        return resp
    response["msg"] = "An error occurred while sending mail."
    msg = MIMEText(message)
    msg['Subject'] = "New message from Website"
    msg['From'] = sender
    msg['Reply-to'] = sender
    msg['To'] = receiver
    try:
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.starttls()
        s.login('hugodelval@gmail.com', passwd)
        s.sendmail(sender, [receiver], msg.as_string())
        s.quit()
        response["msg"] = "Thank you for taking the time to send me this email. I will answer as fast as possible."
        resp = jsonify(**response)
        resp.status_code = 200
    except Exception as e:
        print(e, file=sys.stderr)
        response["msg"] = "Sorry an error occured while sending email. I'll be informed. You can contact me using hugodelval[at]gmail[dot]com"
        resp = jsonify(**response)
        resp.status_code = 500
    return resp


@app.route('/writeups', methods=['GET'])
def writeups():
    writeups_dirs = [join(app.root_path, "writeups", d) for d in listdir(join(app.root_path, "writeups")) if isdir(join(app.root_path, "writeups", d))]
    writeups = sum(map(lambda d: [(basename(d), f) for f in listdir(d) if isfile(join(d, f))], writeups_dirs), [])
    return render_template('ctfs.html', writeups=sorted(writeups, reverse=True))


@app.route('/writeup/<ctf>/<writeup>', methods=['GET'])
def writeup(ctf, writeup):
    if not re.match(r'^[ \w.-]+$', ctf):
        abort(403)
    if not isdir(join(app.root_path, "writeups", ctf)):
        abort(404)
    if not re.match(r'^[ \w.-]+$', writeup):
        abort(403)
    writeup_path = join(app.root_path, "writeups", ctf, writeup)
    if not isfile(writeup_path):
        abort(404)
    writeup = open(writeup_path).read()
    return render_template('writeup.html',
                           writeup=writeup.replace("\\", "\\\\").replace("\n", "\\n").replace("'", "\\'"),
                           return_text="Back to the writeup list",
                           return_url="/writeups",
                           type=0)


@app.route('/bug_bounties', methods=['GET'])
def bug_bounties():
    bug_bounties = [f for f in listdir(join(app.root_path, "bug_bounties")) if isfile(join(app.root_path, "bug_bounties", f))]
    return render_template('bugbounties.html', bugbounties=sorted(bug_bounties, reverse=True))


@app.route('/bug_bounties/<bb_name>', methods=['GET'])
def bug_bounty(bb_name):
    if not re.match(r'^[ \w.-]+$', bb_name):
        abort(403)
    bb_path = join(app.root_path, "bug_bounties", bb_name)
    if not isfile(bb_path):
        abort(404)
    writeup = open(bb_path).read()
    return render_template('writeup.html',
                           writeup=writeup.replace("\\", "\\\\").replace("\n", "\\n").replace("'", "\\'"),
                           return_text="Back to the bug bounty list",
                           return_url="/bug_bounties",
                           type=1)


if __name__ == "__main__":
    app.run()
