import os
from sqlite3 import Date
from flask import Flask,flash
from flask import render_template
from flask import request,url_for,redirect,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from random import randint
import smtplib
#server = smtplib.SMTP('smtp.gmail.com',587)

#server.starttls()

#server.login('kanbaniitm@gmail.com','tsslafciqjfvffgz')

#server.sendmail('kanbaniitm@gmail.com','saicharankmrs@gmail.com','<b>Mail From Python!!</b>')
#print("mailsent")

current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+"database.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key="kanbanforiitm"
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

db = SQLAlchemy()
db.init_app(app)
app.app_context().push()
Column = db.Column
Integer = db.Integer
String = db.String
ForeignKey = db.ForeignKey
Boolean = db.Boolean
DateTime = db.DateTime


class Users(db.Model):
    __tablename__ = 'users'
    user_id = Column(Integer,primary_key = True,autoincrement=True)
    username = Column(String, unique=True,nullable=False)
    password = Column(String,nullable=False)
    email = Column(String, nullable=False)
    isactive = Column(Boolean,nullable=False,default=True)
    lists = db.relationship('Lists',backref = 'Users')

class Lists(db.Model):
    __tablename__ = 'lists'
    list_id = Column(Integer,nullable=False,autoincrement=True,primary_key=True)
    uid = Column(Integer,ForeignKey('users.user_id'),nullable=False )
    listname = Column(String(30),nullable=False)
    isactive = Column(Boolean,default=True)
    cards = db.relationship('Cards',backref = 'Lists')

class Cards(db.Model):
    __tablename__ = 'cards'
    card_id = Column(Integer,nullable=False,autoincrement=True,primary_key=True)
    list_id = Column(Integer,ForeignKey('lists.list_id'),nullable=False)
    card_title = Column(String(20),nullable=False)
    card_content = Column(String(50),nullable=False)
    deadline_dt = Column(DateTime,nullable=False)
    iscomplete = Column(Boolean,nullable=False)
    isactive = Column(Boolean,nullable=False)
    completed_dt = Column(DateTime,nullable=True)
    created_dt  = Column(DateTime,nullable=False)
    last_updated_dt  = Column(DateTime,nullable=False,default=created_dt)
   
class ActiveLists(object):
    @staticmethod
    def get_active_lists(username):
        userid = Users.query.filter_by(username=username).first().user_id
        lists = Lists.query.filter((Lists.uid == userid) & (Lists.isactive==1)).all()
        return lists


db.create_all()

global ul
ul=[]


@app.route("/<username>/board/")
def loginsuccess(username):
    lists = ActiveLists.get_active_lists(username)
    #lists = Lists.query.filter_by((Lists.uid=userrow.user_id) & (Lists.isactive=1)).all()
    return render_template('login.html',user = username,lists=lists,length_lists=len(lists))
    

@app.route("/",methods=['GET','POST'])
def home():
    if request.method=='GET':
        return render_template('home.html')
    if request.method=='POST':
        uname = request.form['uname']
        pword = request.form['pword']
        if uname=='':
            flash('Invalid Credentials')
            return redirect(url_for('home'))
        result = Users.query.filter_by(username=uname).first()
        if result ==None:
            flash('Invalid credentials, Try Again')
            return redirect(url_for('home'))
        elif result.password != pword :
            flash('Invalid credentials, Try Again')
            return redirect(url_for('home'))
        else:
            session['uname'] = uname
            return redirect(url_for('loginsuccess',username=uname))

@app.route("/<username>/logout",methods=['GET','POST'])
def logout(username):
    session.pop('username',None)
    return redirect(url_for('home'))

@app.route("/signUp",methods=['GET','POST'])
def signUp():
    if request.method=='GET':
        return render_template('signUp.html')
    if request.method == 'POST':
        newuname = request.form.get('newuname')
        newpass=request.form.get('newpass')
        email = request.form.get('email')
        newuser = Users(username = newuname,password = newpass,email = email)
        quer = Users.query.filter_by(username=newuname).first()
        if quer is  None:
            db.session.add(newuser)
            db.session.commit()
            flash("User Created Successfully, Please Login now")
            return redirect(url_for('home'))
        else:
            flash("User Already Exists, Please use different credentials")
            return redirect(url_for('signUp'))

@app.route('/forgotCredentials', methods=['GET','POST'])
def forgotCredentials():
    if request.method =='GET':
        return render_template('forgotCred.html')
    if request.method == 'POST':
        email = request.form['resetmail']
        return redirect(url_for('home',email=email))

@app.route('/<username>/board/createList', methods=['GET','POST'])
def createList(username):
    if request.method == 'GET':
        return render_template('createList.html',user = username)
    if request.method == 'POST':
        list_name = request.form.get("listname")
        user = Users.query.filter_by(username=username).first()
        newlist = Lists(uid = user.user_id,listname = list_name)
        db.session.add(newlist)
        db.session.commit()
        return redirect(url_for('loginsuccess',username=username))

@app.route("/<username>/board/renameList/<listid>", methods=["GET","POST"])
def renameList(username,listid):
    print(listid)
    listrow = Lists.query.filter_by(list_id=listid).first()
    listrow.listname = request.form.get("newlistname")
    db.session.commit()
    return redirect(url_for('loginsuccess',username=username))

@app.route("/<username>/board/deleteList/<listid>",methods=['GET','POST'])
def deleteList(username,listid):
    user = Users.query.filter_by(username=username).first()
    lists = user.lists
    for i in lists:
        if i.list_id==int(listid):
            i.isactive=0
            db.session.commit()
    return redirect(url_for('loginsuccess',username=username))

if __name__=='__main__':
    app.run(debug=True,host='0.0.0.0') 