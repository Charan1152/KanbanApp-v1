from flask_security import UserMixin, RoleMixin

from .database import db

Column = db.Column
Integer = db.Integer
String = db.String
ForeignKey = db.ForeignKey
Boolean = db.Boolean
DateTime = db.DateTime

class Users(db.Model,UserMixin):
    __tablename__ = 'user'
    user_id = Column(Integer,primary_key = True,autoincrement=True)
    id = Column(Integer)
    username = Column(String,nullable=False)
    password = Column(String,nullable=False)
    email = Column(String, nullable=False,unique=True)
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