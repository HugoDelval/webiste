import os, sys
from email.mime.text import MIMEText
from sqlite3 import dbapi2 as sqlite3

from datetime import date

import re
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify

import smtplib
import skills, secrets

app = Flask(__name__)

# Load default config
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'website.db'),
    DEBUG=True,
    SECRET_KEY=secrets.key,
))


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


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
    sender = request.form['sender'].encode('ascii',errors='ignore').decode('ascii')
    receiver = 'hugodelval@gmail.com'
    message = request.form['message'].encode('ascii',errors='ignore').decode('ascii')
    response = {"msg" : "An error occurred while sending mail."}
    if not isinstance(sender, str) or not re.match(r'[^@\s]+@[^@\s]+\.[^@\s]+', sender):
        response["msg"] = "Your email is empty or invalid."
    if not isinstance(message, str) or len(message) < 10 or len(message) > 10000:
        response["msg"] = "Your email is either too short or too long."
    msg = MIMEText(message)
    msg['Subject'] = "New message from Website"
    msg['From'] = sender
    msg['Reply-to'] = sender
    msg['To'] = receiver
    try:
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.starttls()
        s.login('hugodelval@gmail.com', secrets.passwd)
        s.sendmail(sender, [receiver], msg.as_string())
        s.quit()
        response["msg"] = "Thank you for taking the time to send me this mail. I will answer as fast as possible."
        resp = jsonify(**response)
        resp.status_code = 200
    except Exception as e:
        print(e, file=sys.stderr)
        response["msg"] = "Sorry an error occured while sending email. I'll be informed. You can contact me using hugodelval[at]gmail[dot]com"
        resp = jsonify(**response)
        resp.status_code = 500
    return resp


# if not session.get('logged_in'):
#     abort(401)
# db = get_db()
# db.execute('insert into entries (title, text) values (?, ?)',
#            [request.form['title'], request.form['text']])
# db.commit()
# flash('New entry was successfully posted')
# return redirect(url_for('show_entries'))

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ["initdb", "run"]:
        print("Need 1 argument from (initdb, run)", file=sys.stderr)
        sys.exit(1)
    if sys.argv[1] == "initdb":
        init_db()
    elif sys.argv[1] == "run":
        app.run()