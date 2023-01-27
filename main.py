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
# from flask_security import UserMixin, RoleMixin,auth_required
import string, random
from application import workers
from application import config
from application.config import LocalDevelopmentConfig
from application import tasks
from application.models import Users, Lists, Cards, Role 
from application.database import db

current_dir = os.path.abspath(os.path.dirname(__file__))
app = None
api = None
celery = None
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
    CORS(app,supports_credentials=True)
    app.config['CORS_HEADERS'] = 'application/json'
    user_datastore = SQLAlchemySessionUserDatastore(db.session, Users, Role)
    security = Security(app, user_datastore)
    api = Api(app)
    app.app_context().push()
    
    # Create celery   
    celery = workers.celery

    # Update with configuration
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"]
    )

    celery.Task = workers.ContextTask
    app.app_context().push()
    return app, api, celery

app, api, celery = create_app()


list_fields = {
    'list_id': fields.Integer,
    'listname': fields.String,
    'uid': fields.Integer,
    'isactive' : fields.Boolean
}

list_parser = reqparse.RequestParser()
list_parser.add_argument('listname')
#list_parser.add_argument('description')

user_fields = {
    'username': fields.String,
    'password': fields.String,
    'email': fields.String
}

user_parser  = reqparse.RequestParser()
user_parser.add_argument("username")
user_parser.add_argument("password")
user_parser.add_argument("email")

class UsersListApi(Resource):
    @auth_required("token")
    def get(self, email):
        data = {}
        data["email"] = email
        print()
        user = Users.query.filter_by(email=email).first()
        print(user)
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
                        c['iscomplete'] = card.iscomplete
                        l['cards'].append(c)
                data['lists'].append(l)
        return data   
    
    @marshal_with(user_fields)
    def post(self):   
        args = user_parser.parse_args()
        newuname = args.get('username', None)
        password = args.get('password',None)
        email = args.get('email',None)
        fs_uniquifier = ''.join(random.choices(string.ascii_letters,k=10))
        newuser = Users(username = newuname,password = password,email = email,fs_uniquifier=fs_uniquifier,isactive=True,active=True)
        quer = Users.query.filter_by(email=email).first()
        if quer is  None:
            db.session.add(newuser)
            db.session.commit()
            user = Users.query.filter_by(email=email).first()
            user.id = user.user_id
            db.session.commit()
        else:
            raise BusinessValidationError(status_code=400,error_code="User001",error_message="User Already Exist")
        return quer, 201

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
card_parser.add_argument('card_title',type=str)
card_parser.add_argument('card_content',type=str)
card_parser.add_argument('deadline_dt',type=str)
# card_parser.add_argument('isactive')
card_parser.add_argument('list_id',type=str)
# card_parser.add_argument('iscomplete',type=str)

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

    # @auth_required("token")
    @marshal_with(card_fields)
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

    # @auth_required("token")
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
        print(1)
        card = Cards.query.get(card_id)
        if card is None:
            raise NotFoundError(status_code=404)
        print(2)
        args = card_parser.parse_args()
        print(args)
        card_title = args.get('card_title', None)
        card_content = args.get('card_content', None)
        deadline_dt = datetime.strptime(args.get('deadline_dt', None),'%Y-%m-%d')
        list_id = args.get('list_id', None)
        
        print(3)
        if list_id is None:
            raise BusinessValidationError(status_code=400, error_code='LIST003', error_message='List Id is required')

        # l = Lists.query.get(list_id)
        # if l is None:
        #     raise NotFoundError(status_code=404)
        print(4)
        if card_title is None:
            raise BusinessValidationError(status_code=400, error_code='CARD001', error_message='Card Name is required')
        print(5)
        if deadline_dt is None:
            raise BusinessValidationError(status_code=400, error_code='CARD002', error_message='Deadline is required')
        print(6)
        print(card)
        card.card_title = card_title
        card.card_content = card_content
        card.deadline_dt = deadline_dt
        card.isactive = True
        card.list_id = list_id
        card.last_updated_dt = datetime.now()
        print(7)
        db.session.commit()
        return card,200


card_parser_x = reqparse.RequestParser()
card_parser_x.add_argument('iscomplete',type=int)

class CardOps(Resource):
    @auth_required("token")
    @marshal_with(card_fields)
    def post(self,card_id):
        args = card_parser_x.parse_args()
        iscomplete = args.get('iscomplete',None)
        card = Cards.query.get(card_id)
        if iscomplete == 1:
            card.iscomplete = 1
            card.completed_dt = datetime.now()
        else:
            card.iscomplete=0
        card.last_updated_dt = datetime.now()

        db.session.commit()
        return card,200

# @app.route("/export",methods=["GET", "POST"])
# def export():
#     job = tasks.print_current_time_job.delay()
#     return str(job), 200

api.add_resource(ListAPI, "/api/lists/<user_id>", "/api/createList/<user_id>", "/api/deleteList/<list_id>", "/api/updateList/<list_id>")
api.add_resource(CardAPI, "/api/cards/<list_id>", "/api/createCard/<list_id>", "/api/deleteCard/<card_id>", "/api/updateCard/<card_id>")
api.add_resource(UsersListApi,"/api/<email>","/api/signUp")
api.add_resource(CardOps,"/api/markCom/<card_id>")


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
    
    