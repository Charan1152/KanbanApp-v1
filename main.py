import os
from sqlite3 import Date
from flask import Flask,flash
from flask import render_template
from flask import request,url_for,redirect,session,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource,Api
from datetime import datetime
import sendmail as sm
from werkzeug.exceptions import HTTPException
import json


basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class LocalDevelopmentConfig(Config):
    SQLITE_DB_DIR = os.path.join(basedir)
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "database.sqlite3")
    DEBUG = True


db = SQLAlchemy()
Column = db.Column
Integer = db.Integer
String = db.String
ForeignKey = db.ForeignKey
Boolean = db.Boolean
DateTime = db.DateTime

current_dir = os.path.abspath(os.path.dirname(__file__))
app = None
api = None

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.secret_key = "kanbanforiitm"
    if os.getenv('ENV', "development") == "production":
      raise Exception("Currently no production config is setup.")
    else:
      print("Staring Local Development")
      app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    api = Api(app)
    app.app_context().push()
    return app, api

app, api = create_app()

#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+"database.sqlite3"
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
#app.config['SESSION_TYPE'] = 'filesystem'
#app.secret_key="kanbanforiitm"

class CardAPI(Resource):
    def get(self, list_id):
        l = List.query.get(list_id)
        if l:
            c = []
            for card in l.cards:
                c.append(card.name)
            return {'list_id': list_id, 'cards': c}
        else:
            raise NotFoundError(status_code=404)

class ListAPI(Resource):
    def get(self, user_id):
        user = Users.query.get(user_id)
        if user:
            l = []
            for lst in user.lists:
                l.append(lst.name)
            return {'user_id': user_id, 'lists': l}
        else:
            raise NotFoundError(status_code=404)

api.add_resource(ListAPI, "/api/lists/<user_id>", "/api/createlist/<user_id>", "/api/deletelist/<list_id>", "/api/updatelist/<list_id>")
api.add_resource(CardAPI, "/api/cards/<list_id>", "/api/createcard/<list_id>", "/api/deletecard/<card_id>", "/api/updatecard/<card_id>")

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
    last_updated_dt  = Column(DateTime,nullable=False)
   
class ActiveLists(object):
    @staticmethod
    def get_active_lists(username):
        userid = Users.query.filter_by(username=username).first().user_id
        lists = Lists.query.filter((Lists.uid == userid) & (Lists.isactive==1)).all()
        return lists

class ActiveCards(object):
    @staticmethod
    def get_active_cards(list_id):
        cards = Cards.query.filter((Cards.list_id == list_id) & (Cards.isactive==1)).all()
        return cards


db.create_all()


class NotFoundError(HTTPException):
    def __init__(self,statuscode):
        self.response = make_response('',statuscode)

class BusinessValidationError(HTTPException):
    def __init__(self,statuscode, errorcode, errormessage):
        message = {"Error Code": errorcode, "Message": errormessage}
        self.response = make_response(json.dumps(message),statuscode)

@app.route("/<username>/board/")
def loginsuccess(username):
    lists = ActiveLists.get_active_lists(username)
    d={}
    for i in lists:
        d[i] = ActiveCards.get_active_cards(i.list_id)
    #lists = Lists.query.filter_by((Lists.uid=userrow.user_id) & (Lists.isactive=1)).all()
    return render_template('login.html',user = username,lists=lists,length_lists=len(lists),dic=d)
    

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

@app.route('/<username>/board/createCard/<listid>',methods=['GET','POST'])
def createCard(username,listid):
    if request.method == 'POST':
        x = list(map(int,request.form.get("deadlinedt").split("-")))
        card = Cards(list_id=int(listid),card_title=request.form.get("cardtitle"),card_content=request.form.get("cardcontent"),deadline_dt=datetime(x[0],x[1],x[2]),iscomplete=0,isactive=1,created_dt=datetime.now(),last_updated_dt=datetime.now())
        db.session.add(card)
        db.session.commit()
        return redirect(url_for('loginsuccess',username=username))

@app.route('/<username>/board/markAsComplete/<cardid>',methods=['GET','POST'])
def markAsComplete(username,cardid):
        card = Cards.query.filter_by(card_id=cardid).first()
        card.iscomplete=1
        card.last_updated_dt=datetime.now()
        db.session.commit()
        return redirect(url_for('loginsuccess',username=username))

@app.route('/<username>/board/deleteCard/<cardid>',methods=['GET','POST'])
def deleteCard(username,cardid):
    card = Cards.query.filter_by(card_id=cardid).first()
    card.isactive=0
    db.session.commit()
    return redirect(url_for('loginsuccess',username=username))

@app.route('/<username>/board/markAsIncomplete/<cardid>',methods=['GET','POST'])
def markAsIncomplete(username,cardid):
        card = Cards.query.filter_by(card_id=cardid).first()
        card.iscomplete=0
        card.last_updated_dt=datetime.now()
        db.session.commit()
        return redirect(url_for('loginsuccess',username=username))

@app.route('/<username>/board/renameCard/<cardid>',methods=['GET','POST'])
def renameCard(username,cardid):
    card = Cards.query.filter_by(card_id=cardid).first()
    card.card_title = request.form.get('newcardname')
    card.last_updated_dt=datetime.now()
    db.session.commit()
    return redirect(url_for('loginsuccess',username=username))

@app.route('/<username>/board/changeCardContent/<cardid>',methods=['GET','POST'])
def changeCardContent(username,cardid):
    card = Cards.query.filter_by(card_id=cardid).first()
    card.card_content = request.form.get('newcardcontent')
    card.last_updated_dt = datetime.now()
    db.session.commit()
    return redirect(url_for('loginsuccess',username=username))    

@app.route('/<username>/board/transferCards/<listid>',methods=['GET','POST'])
def transferCards(username,listid):
    cards = ActiveCards.get_active_cards(listid)
    tolist = request.form.getlist('totransfer')[0]
    tlist_id = Lists.query.filter_by(listname=tolist).first().list_id
    for card in cards:
        card.list_id  = tlist_id
        card.last_updated_dt=datetime.now()
    db.session.commit()
    return redirect(url_for('loginsuccess',username=username))    

@app.route('/<username>/summary')
def summary(username):
    if request.method == 'GET':
        user = Users.query.filter_by(username=username).first()
        (labels, data1, data0) = ([], [], [])
        for l in user.lists:
            labels.append(l.listname)
            temp1 = 0
            temp0 = 0
            for card in l.cards:
                if card.iscomplete == 1:
                    temp1 += 1
                else:
                    temp0 += 1
            data1.append(temp1)
            data0.append(temp0)
        #print(labels, data1, data0)
        return render_template('summary.html', user = username, labels = json.dumps(labels), data1 = json.dumps(data1), data0 = json.dumps(data0) )        

@app.route('/<username>/board/transfersCard/<listid>/<cardid>',methods=['GET','POST'])
def transfersCard(username,listid,cardid):
    card = Cards.query.filter_by(card_id=cardid).first()
    tolist = request.form.getlist('totransfer')[0]
    card.list_id = Lists.query.filter_by(listname=tolist).first().list_id
    card.last_updated_dt=datetime.now()
    db.session.commit()
    return redirect(url_for('loginsuccess',username=username))  

if __name__=='__main__':
    app.run(debug=True,host='0.0.0.0') 