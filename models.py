from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column('user_id' ,Integer, primary_key=True)
    reg_id = Column(Text, unique=True)
    

class Channel(Base):
    __tablename__ = 'channel'
    name = Column(Text, primary_key=True)
    status = Column(SmallInteger)


class Subscription(Base):
    __tablename__ = 'subscription'
    subscription_id = Column(Integer, primary_key = True)
    user_num = Column(Integer, ForeignKey('users.user_id'))
    channel_name = Column(Text, ForeignKey('channel.name'))

    channel = relationship('Channel', foreign_keys=channel_name)
    user = relationship('User', foreign_keys = user_num)
