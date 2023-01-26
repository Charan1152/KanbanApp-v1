import os
from sqlite3 import Date
from flask import Flask,flash
from flask import render_template
from flask import request,url_for,redirect,session,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource,Api,marshal_with,reqparse,fields
from datetime import datetime
# import sendmail as sm
from werkzeug.exceptions import HTTPException
import json
from flask_cors import CORS,cross_origin
from flask_security import *
from flask_security import UserMixin, RoleMixin,auth_required



basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authentication-Token"

class LocalDevelopmentConfig(Config):
    SQLITE_DB_DIR = os.path.join(basedir)
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "database.sqlite3")
    DEBUG = True
    SECRET_KEY =  "ash ah secet"
    SECURITY_PASSWORD_HASH = "bcrypt"    
    SECURITY_PASSWORD_SALT = "really super secret" # Read from ENV in your case
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    WTF_CSRF_ENABLED = False


db = SQLAlchemy()
Column = db.Column
Integer = db.Integer
String = db.String
ForeignKey = db.ForeignKey
Boolean = db.Boolean
DateTime = db.DateTime

class Users(db.Model,UserMixin):
    __tablename__ = 'user'
    user_id = Column(Integer,primary_key = True,autoincrement=True)
    id = user_id
    username = Column(String, unique=True,nullable=False)
    password = Column(String,nullable=False)
    email = Column(String, nullable=False)
    isactive = Column(Boolean,nullable=False)
    fs_uniquifier = Column(String,nullable=False,unique=True)
    active = Column(Boolean)
    lists = db.relationship('Lists',backref = 'Users')
    
class Lists(db.Model):
    __tablename__ = 'lists'
    list_id = Column(Integer,nullable=False,autoincrement=True,primary_key=True)
    uid = Column(Integer,ForeignKey('user.user_id'),nullable=False )
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

class Role(db.Model,RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer,primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

   
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
    CORS(app,supports_credentials=True)
    app.config['CORS_HEADERS'] = 'application/json'
    user_datastore = SQLAlchemySessionUserDatastore(db.session, Users, Role)
    security = Security(app, user_datastore)
    return app, api

app, api = create_app()


list_fields = {
    'list_id': fields.Integer,
    'listname': fields.String,
    'uid': fields.Integer,
    'isactive' : fields.Boolean
}

list_parser = reqparse.RequestParser()
list_parser.add_argument('listname')
#list_parser.add_argument('description')


class UsersListApi(Resource):
    # @auth_required("token")
    def get(self, user_id):
        data = {}
        data["user_id"] = user_id
        user = Users.query.filter_by(user_id=user_id).first()
        data['username'] = user.username 
        data['lists'] = []
        for list in user.lists:
            if list.isactive==1:
                l={}
                l['list_id'] = list.list_id
                l['listname'] = list.listname
                l['cards'] = []
                for card in list.cards:
                    if card.isactive==1:
                        c={}
                        c['card_id'] = card.card_id
                        c['list_id'] = card.list_id
                        c['card_title'] = card.card_title
                        c['card_content'] = card.card_content
                        c['deadline_dt'] = str(card.deadline_dt)
                        c['isactive'] = card.isactive
                        l['cards'].append(c)
                data['lists'].append(l)
        return data   

class ListAPI(Resource):
    @auth_required("token")
    def get(self, user_id):
        user = Users.query.get(user_id)
        if user:
            l = []
            for lst in user.lists:
                l.append(lst.listname)
            return {'user_id': user_id, 'lists': l}
        else:
            raise NotFoundError(status_code=404)


    @marshal_with(list_fields)
    @auth_required("token")
    def post(self, user_id):
        args = list_parser.parse_args()
        listname = args.get('listname', None)
        if listname is None:
            raise BusinessValidationError(status_code=400, error_code='LIST001', error_message='List Name is required')

        l = Lists.query.filter_by(listname=listname,uid=user_id).first()
        if l is not None:
            raise BusinessValidationError(status_code=400, error_code='LIST002', error_message='List Name already exists')
        
        l = Lists(listname=listname ,uid = user_id)
        db.session.add(l)
        db.session.commit()
        return l, 201
    @auth_required("token")
    def delete(self, list_id):
        l = Lists.query.get(list_id)
        if l is None:
            raise NotFoundError(status_code=404)
        else:
            l.isactive=0
            db.session.commit()
            return "Successfully Deleted" 

    @auth_required("token")
    @marshal_with(list_fields)
    def put(self, list_id):
        l = Lists.query.get(list_id)
        if l is None:
            raise NotFoundError(status_code=404)

        args = list_parser.parse_args()
        listname = args.get('listname', None)

        if listname is None:
            raise BusinessValidationError(status_code=400, error_code='LIST001', error_message='List Name is required')

        new = Lists.query.filter_by(listname=listname,uid=l.uid).first()
        if l.listname == listname or new == None:
            l.listname = listname
            db.session.commit()
            return l,200
        else:
            raise BusinessValidationError(status_code=400, error_code='LIST002', error_message='List Name already exists')


#CARD API
card_fields = {
    'card_id': fields.Integer,
    'card_title': fields.String,
    'card_content': fields.String,
    'deadline_dt': fields.String,
    'isactive': fields.String,
    'list_id': fields.Integer
}

card_parser = reqparse.RequestParser()
card_parser.add_argument('card_title')
card_parser.add_argument('card_content')
card_parser.add_argument('deadline_dt')
card_parser.add_argument('isactive')
card_parser.add_argument('list_id')
card_parser.add_argument('iscomplete')

class CardAPI(Resource):
    @auth_required("token")
    def get(self, list_id):
        l = Lists.query.get(list_id)
        if l:
            c = []
            for card in l.cards:
                c.append(card.card_title)
            return {'list_id': list_id, 'cards': c}
        else:
            raise NotFoundError(status_code=404)
    
    @marshal_with(card_fields)
    @auth_required("token")
    def post(self, list_id):
        args = card_parser.parse_args()
        card_title = args.get('card_title', None)
        card_content = args.get('card_content', None)
        deadline_dt = datetime.strptime(args.get('deadline_dt', None),'%Y-%m-%d')
        dummy = args.get('deadline_dt', None)
        created_dt = datetime.now()
        ludt = datetime.now()

        if card_title is None:
            raise BusinessValidationError(status_code=400, error_code='CARD001', error_message='Card Name is required')

        if deadline_dt is None:
            raise BusinessValidationError(status_code=400, error_code='CARD002', error_message='Deadline is required')

        today = datetime.today().strftime('%Y-%m-%d')
        if dummy < today:
            raise BusinessValidationError(status_code=400, error_code='CARD003', error_message='Date must be bigger or Equal to today date')

        card = Cards.query.filter_by(card_title=card_title,list_id=list_id).first()
        if card is not None:
            raise BusinessValidationError(status_code=400, error_code='CARD004', error_message='Card Name already exists in the given list')
        
        c = Cards(card_title=card_title, card_content=card_content, deadline_dt=deadline_dt, created_dt=created_dt ,list_id=list_id,last_updated_dt=ludt,iscomplete=False,completed_dt=None,isactive=True)
        db.session.add(c)
        db.session.commit()
        return c, 201

    @auth_required("token")
    def delete(self, card_id):
        card = Cards.query.get(card_id)
        if card is None:
            raise NotFoundError(status_code=404)
        else:
            card.isactive=0
            db.session.commit()
            return "Successfully Deleted"

    @auth_required("token")
    @marshal_with(card_fields)
    def put(self, card_id):
        card = Cards.query.get(card_id)
        if card is None:
            raise NotFoundError(status_code=404)

        args = card_parser.parse_args()
        card_title = args.get('card_title', None)
        card_content = args.get('card_content', None)
        deadline_dt = datetime.strptime(args.get('deadline_dt', None),'%Y-%m-%d')
        dummy = args.get('deadline_dt', None)
        list_id = args.get('list_id', None)
        iscomplete = args.get('iscomplete',None)

        if list_id is None:
            raise BusinessValidationError(status_code=400, error_code='LIST003', error_message='List Id is required')

        l = Lists.query.get(list_id)
        if l is None:
            raise NotFoundError(status_code=404)

        if card_title is None:
            raise BusinessValidationError(status_code=400, error_code='CARD001', error_message='Card Name is required')
        
        if deadline_dt is None:
            raise BusinessValidationError(status_code=400, error_code='CARD002', error_message='Deadline is required')

        if iscomplete is None:
            raise BusinessValidationError(status_code=400, error_code='CARD003', error_message='Card Status required')

        card.card_title = card_title
        card.card_content = card_content
        card.deadline_dt = deadline_dt
        card.isactive = True
        if iscomplete == '1':
            card.iscomplete = 1
            card.completed_dt = datetime.now()
        else:
            card.iscomplete=0
        card.last_updated_dt = datetime.now()
        db.session.commit()
        return card,200

api.add_resource(ListAPI, "/api/lists/<user_id>", "/api/createList/<user_id>", "/api/deleteList/<list_id>", "/api/updateList/<list_id>")
api.add_resource(CardAPI, "/api/cards/<list_id>", "/api/createCard/<list_id>", "/api/deleteCard/<card_id>", "/api/updateCard/<card_id>")
api.add_resource(UsersListApi,"/api/<user_id>")


# class Users(db.Model):
#     __tablename__ = 'users'
#     user_id = Column(Integer,primary_key = True,autoincrement=True)
#     username = Column(String, unique=True,nullable=False)
#     password = Column(String,nullable=False)
#     email = Column(String, nullable=False)
#     isactive = Column(Boolean,nullable=False,default=True)
#     lists = db.relationship('Lists',backref = 'Users')


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
    def __init__(self,status_code):
        self.response = make_response('',status_code)

class BusinessValidationError(HTTPException):
    def __init__(self,status_code, error_code, error_message):
        message = {"Error Code": error_code, "Message": error_message}
        self.response = make_response(json.dumps(message),status_code)

if __name__=='__main__':
    app.run(debug=True,host='0.0.0.0') 
    
    
