from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column('user_id' ,db.Integer, primary_key=True)
    reg_id = db.Column(db.Text, unique=True)
    
    def __init__(self, reg_id):
        self.reg_id = reg_id

class Channel(db.Model):
    __tablename__ = 'channel'
    name = db.Column(db.Text, primary_key=True)
    status = db.Column(db.SmallInteger)


class Subscription(db.Model):
    __tablename__ = 'subscription'
    subscription_id = db.Column(db.Integer, primary_key = True)
    user_num = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    channel_name = db.Column(db.Text, db.ForeignKey('channel.name'))

    channel = db.relationship('Channel', foreign_keys=channel_name)
    user = db.relationship('User', foreign_keys = user_num)
