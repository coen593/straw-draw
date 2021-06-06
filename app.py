import os
import sqlite3
import json

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from random import randint

import mailBodys
from helpers import login_required, apology

mailer = mailBodys.Email()


# Configure application and mail
app = Flask(__name__)
app.config["MAIL_DEFAULT_SENDER"] = ("Straw Draw", os.getenv("SD_MAIL_NAME"))
app.config["MAIL_PASSWORD"] = os.getenv("SD_MAIL_PASS")
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("SD_MAIL_NAME")
mail = Mail(app)


# Link to DB
con = sqlite3.connect('draw.db', isolation_level=None, check_same_thread=False)
cur = con.cursor()


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Go to homepage
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create", methods=["GET","POST"])
def create():
    # POST indicates that create draw form is submitted
    if request.method == "POST":
        # Get variables from post request
        creatorcode = randint(10000,99999)
        creator = request.form.get("creator")
        email = request.form.get("mail")
        draw = request.form.get("draw")

        # Create code to use in copyable URL etc, ensuring no duplicates by while loop
        while creatorcode in cur.execute("SELECT code FROM creators GROUP BY code").fetchall():
            creatorcode = randint(10000,99999)

        # Check if creator already exists in persons table, if not, create entry, and set person_id
        personCheck = cur.execute("SELECT id FROM persons WHERE name = ? AND email = ?", (creator, email)).fetchone()
        if personCheck:
            person_id = personCheck[0]
        else:
            cur.execute("INSERT INTO persons (name, email) VALUES (?, ?)", (creator, email))   
            person_id = cur.execute("SELECT MAX(id) FROM persons").fetchone()[0]

        # Insert draw into creators table
        cur.execute("INSERT INTO creators (person_id, code, draw, straws, createdt) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (person_id, creatorcode, draw, request.form.get("straws")))
        creator_id = cur.execute("SELECT MAX(id) FROM creators").fetchone()[0]

        # Insert creator into participants table (as participant number 1)
        cur.execute("INSERT INTO participants (person_id, number, creator_id) VALUES (?, 1, ?)", (person_id, creator_id))
        participant_id = cur.execute("SELECT MAX(id) FROM participants").fetchone()[0]

        # Set session based on id created in participants table
        session["user_id"] = participant_id
        con.commit

        # Send email to creator
        body = mailer.drawCreate(creator, draw, creatorcode, request.url_root + "/participate?code=" + str(creatorcode), request.url_root + "/manage?code=" + str(creatorcode) + "&mail=" + email.replace("@","%40"))
        msg = Message("Straw Draw - you've created a new draw!", recipients=[email])
        msg.html = body
        mail.send(msg)

        # Redirect to manage draw page
        return redirect("/manage")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("create.html")


@app.route("/participate", methods=["GET","POST"])
def participate():
    # POST request indicates form was submitted
    if request.method == "POST":
        # Get form variables
        email = request.form.get("mail")
        name = request.form.get("name")
        code = request.form.get("code")

        # Get creator_id and draw name based on code
        creator_id = cur.execute("SELECT id FROM creators WHERE code = ?", (code,)).fetchone()[0]
        draw = cur.execute("SELECT draw FROM creators WHERE code = ?", (code,)).fetchone()[0]

        # Check if person exists already in person table, and if not, create
        emailCheck = cur.execute("SELECT email FROM persons WHERE email = ? AND name = ?", (email, name)).fetchone()
        if emailCheck:
            person_id = cur.execute("SELECT id FROM persons WHERE email = ? AND name = ?", (email, name)).fetchone()[0]
        else:
            cur.execute("INSERT INTO persons (name, email) VALUES (?, ?)", (name, email))
            person_id = cur.execute("SELECT MAX(id) FROM persons").fetchone()[0]

        # Check current number of particpants and adds one
        number = cur.execute("SELECT MAX(number) FROM participants WHERE creator_id = ?", (creator_id,)).fetchone()[0] + 1
        
        # Insert participants into participants table
        cur.execute("INSERT INTO participants (number, person_id, creator_id) VALUES (?, ?, ?)", (number, person_id, creator_id))
        participant_id = cur.execute("SELECT MAX(id) FROM participants").fetchone()[0]
        con.commit

        # Set session based on participant id
        session["user_id"] = participant_id

        # Send email to participant
        body = mailer.participate(name, draw, code, request.url_root + "/manage?code=" + str(code) + "&mail=" + email.replace("@","%40"))
        msg = Message("Straw Draw - you're participating in a draw!", recipients=[email])
        msg.html = body
        mail.send(msg)

        # Redirect to manage page
        return redirect("/manage")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Check if GET included code
        code = request.args.get('code', default = 0, type = int)

        # If no code and no session, render template requesting code
        if code == 0 and not session:
            return render_template("participate-new.html")

        # If code but no session, check if code exists, and if yes, get variables and render participate template
        elif not session:
            tableout = cur.execute("SELECT code FROM creators WHERE code = ?", (str(code),)).fetchone()
            if tableout:
                draw = cur.execute("SELECT draw FROM creators JOIN persons ON creators.person_id = persons.id WHERE code = ?", (str(code),)).fetchone()[0]
                cname = cur.execute("SELECT name FROM creators JOIN persons ON creators.person_id = persons.id WHERE code = ?", (str(code),)).fetchone()[0]
                triggeredCheck = cur.execute("SELECT id FROM creators WHERE code = ? AND triggerdt IS NULL", (str(code),)).fetchone()
                if triggeredCheck:
                    return render_template("participate.html", code=code, draw=draw, cname=cname)
                else:
                    return apology("Unable to participate - this draw has already been triggered!", 400)
            else:
                return apology("The code provided for this draw is incorrect", 400)
        
        # If a session exists, go to the manage page of that session
        elif session:
            return redirect("/manage")

# Deletes selected users when triggered by creator on manage page
@app.route("/delete", methods=["POST"])
@login_required
def delete():
    # Define various variables
    number = int(request.form.get("number"))
    code = request.form.get("code")
    person_id = cur.execute("SELECT id FROM persons WHERE id IN (SELECT person_id FROM participants WHERE number = ? AND creator_id IN (SELECT id FROM creators WHERE code = ?))", (str(number),str(code))).fetchone()[0]
    
    # Check in how many draws person participates
    count = cur.execute("SELECT COUNT(*) FROM participants WHERE person_id = ?", (person_id,)).fetchone()[0]
    # If participates only in one draw, delete person from persons as well
    if count == 1:
        cur.execute("DELETE FROM persons WHERE id = ?", (person_id,))
    # Delete from participants
    cur.execute("DELETE FROM participants WHERE id IN (SELECT id FROM participants WHERE person_id = ? AND creator_id IN (SELECT id FROM creators WHERE code = ?) LIMIT 1)", (person_id, code))
    return redirect("/manage")


# Selecting to do another draw logs out the current session.
@app.route("/other")
def other():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to homepage
    return redirect("/")


# Renders instruction page
@app.route("/howdoesitwork")
def howdoesitwork():
    return render_template("howdoesitwork.html")


# Manage route is used to show current participant and for creator to delete users and trigger the draw
@app.route("/manage", methods=["GET", "POST"])
def manage():
    if request.method == "POST":
        # Gets some initial variables for the rest
        creator_id = cur.execute("SELECT creator_id FROM participants WHERE id = ?", (session.get("user_id"),)).fetchone()[0]
        straws = cur.execute("SELECT straws FROM creators WHERE id = ?", (creator_id,)).fetchone()[0]
        participantNumber = cur.execute("SELECT MAX(number) FROM participants WHERE creator_id = ?", (creator_id,)).fetchone()[0]
        draw = cur.execute("SELECT draw FROM creators WHERE id = ?", (creator_id,)).fetchone()[0]

        # Checks if trigger runs for the first time (not after refresh) and continues with whole process if yes
        checkSelected = cur.execute("SELECT id FROM creators WHERE id = ? AND triggerdt IS NULL", (creator_id,)).fetchone()
        if checkSelected:
            # Generates random number to select participants, (checking straw number) and repeating when selecting double or when participant was removed
            i = int(0)
            selected = []
            while i < straws:
                x = randint(1, participantNumber)
                while (x in selected) or not cur.execute("SELECT id FROM participants WHERE number = ? AND creator_id = ?", (x, creator_id)).fetchone():
                    x = randint(1, participantNumber)
                selected.append(x)
                i += 1

            # Updates SQL participant table to reflect selected or not
            i = 1
            while i <= participantNumber:
                if i in selected:
                    select = 1
                else:
                    select = 0
                cur.execute("UPDATE participants SET selected = ? WHERE creator_id = ? AND number = ?", (select, creator_id, i))
                i += 1

            # Sets timestamp for trigger (used for statistics and to avoid repeating draw after refresh)
            cur.execute("UPDATE creators SET triggerdt = CURRENT_TIMESTAMP WHERE id = ?", (creator_id,))
            
            # Get all participants, their email, and whether they were selected
            participants = cur.execute("SELECT name, email, selected FROM persons JOIN participants ON persons.id = participants.person_id WHERE creator_id = ?", (creator_id,)).fetchall()
            
            # Send emails: different depending on whether participants is selected or not
            winners = cur.execute("SELECT name FROM persons WHERE id IN (SELECT person_id FROM participants WHERE creator_id = ? AND selected = 1)", (str(creator_id),)).fetchall()
            for i in participants:
                winnersMail = []
                for m in winners:
                    winnersMail.append(m[0])
                if i[0] in winnersMail:
                    winnersMail.remove(i[0])
                losers=""
                j = 0
                print(winnersMail)
                for k in winnersMail:
                    if j == len(winnersMail) - 1:
                        losers += k
                    elif j == len(winnersMail) - 2:
                        losers += (k + " and ")
                    else:
                        losers += (k + ", ")
                    j += 1
                if i[2] == 1 and straws > 1:
                    subject = "You drew the shortest straw!"
                    body = mailer.drawnMulti(i[0], draw, losers)
                elif i[2] == 1:
                    subject = "You drew the shortest straw!"
                    body = mailer.drawnOne(i[0], draw)
                elif straws > 1:
                    subject = "Your straw wasn't the shortest!"
                    body = mailer.notDrawnMulti(i[0], draw, losers)
                else:
                    subject = "Your straw wasn't the shortest!"
                    body = mailer.notDrawnOne(i[0], draw, losers)
                msg = Message("Straw Draw - " + subject, recipients=[i[1]], sender=("Straw Draw", "strawdrawww@gmail.com"))
                msg.html = body
                mail.send(msg)

        # Define "winners" (participants who were selected) for rendering template, and then render
        return render_template("selected.html", winners=winners, draw=draw, straws=straws)
    
    # If GET request (either by clicking link on page, or redirected from create/participate)
    else:
        # Check whether there is a code or email provided
        code = request.args.get('code', default = 0, type = int)
        email = request.args.get('mail', default = 'NA')

        # If there is no code and no current session, render a dedicated template returning GET request with code and email
        if code == 0 and not session:
            return render_template("manage-new.html")

        else:
            # If there is session but no code yet, set code based on session
            if code == 0:
                code = cur.execute("SELECT code FROM creators WHERE id IN (SELECT creator_id FROM participants WHERE id = ?)", (session.get("user_id"),)).fetchone()[0]
            # If vice versa, set session based on code and email
            if not session:
                userid = cur.execute("SELECT id FROM participants WHERE person_id IN (SELECT id FROM persons WHERE email = ?) AND creator_id IN (SELECT id FROM creators WHERE code = ?)", (email, code)).fetchone()
                if userid:
                    session["user_id"] = userid[0]
                else:
                    return apology("You have provided an incorrect code or email address", 400)
            
            # Checks whether user is creator or regular participant
            number = cur.execute("SELECT number FROM participants WHERE id = ?", (session.get("user_id"),)).fetchone()[0]
            iscreator = False
            if number == 1:
                iscreator = True

            # Get various variables to prepare rendering template
            creator_id = cur.execute("SELECT id FROM creators WHERE code = ?", (str(code),)).fetchone()[0]
            participants = cur.execute("SELECT name, number FROM persons JOIN participants ON persons.id = participants.person_id WHERE participants.creator_id = ?", (str(creator_id),)).fetchall()
            draw = cur.execute("SELECT draw FROM creators JOIN persons ON creators.person_id = persons.id WHERE code = ?", (str(code),)).fetchone()[0]
            cname = cur.execute("SELECT name FROM creators JOIN persons ON creators.person_id = persons.id WHERE code = ?", (str(code),)).fetchone()[0]
            
            # Check if draw has been previously triggered
            triggeredCheck = cur.execute("SELECT id FROM creators WHERE id = ? AND triggerdt IS NULL", (creator_id,)).fetchone()
            if triggeredCheck:
                return render_template("manage.html", iscreator=iscreator, draw=draw, participants=participants, code=code, cname=cname)
            else:
                winners = cur.execute("SELECT name FROM persons WHERE id IN (SELECT person_id FROM participants WHERE creator_id = ? AND selected = 1)", (str(creator_id),)).fetchall()
                straws = cur.execute("SELECT straws FROM creators WHERE id = ?", (creator_id,)).fetchone()[0]
                return render_template("selected.html", winners=winners, draw=draw, straws=straws)
                