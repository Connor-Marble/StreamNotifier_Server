from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from models import *

import logging

class DatabaseManager():
    """
    responsible for performing all database access in the application
    """
    def __init__(self, app):
        self.app = app
        engine = create_engine(
            'postgresql://connor:postgresytrewq@localhost/Stream_Notifier')
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def add_channels(self, channels):
        for i in channels:
            logging.info('processing {}'.format(i))
            channel = Channel(name=i, status=0)
            try:
                self.session.add(channel)
                self.session.commit()
                logging.info('added new channel ' + i + ' to database')
        
            except IntegrityError as ex:
                self.session.rollback()

            except FlushError as ex:
                logging.warning('failed to insert channel: ' + i + 'due to flush error')

                self.session.rollback()
            
    def add_user(self, regid):
        user = self.session.query(User).filter_by(reg_id=regid).first()

        if user is None:
            user = User(reg_id=regid)
            self.session.add(user)
            self.session.commit()
            
        return user.user_id

    def add_subs(self, user_id, current_channels):
        existing_channels = [sub.channel_name for sub in self.session.query(Subscription).all()]
        new_channels = [ch for ch in current_channels if ch not in existing_channels]
        old_channels = [ch for ch in existing_channels if ch not in current_channels]

        #add new channels user has subbed to
        for channel in new_channels:
            sub = Subscription(user_num=user_id, channel_name=channel)
            self.session.add(sub)
            self.session.commit()

        #remove onld channels user has unsubbed from
        for channel in old_channels:
            sub = self.session.query(Subscription).filter_by(
                user_num=user_id, channel_name=channel).first()
            if sub is not None:
                self.session.delete(sub)
                self.session.commit()
            
            
    def get_all_channels(self):
        return self.session.query(Channel).all()

    def update_channels_status(self, channels, status):

        for channel_name in channels:
            channel = self.session.query(Channel).filter_by(name=channel_name).first()
            
            if channel is not None :
                channel.status=status
                logging.info("changing status of {0} to {1}"
                             .format(channel_name, status))
                try:
                    self.session.commit()
                except:
                    logging.info("problem updating status of []".format(channel_name))
                    self.session.rollback()


    def get_subbed_users(self, channels):
        users = set()
        queries=[]
        for ch_name in channels:
            queries.append(self.session.query(Subscription).filter_by(channel_name=ch_name).all())

        subscriptions = [sub for result in queries for sub in result]
        for sub in subscriptions:
            users.add(self.session.query(User).filter_by(user_id=sub.user_num).first())

        return users
                

    def clean(self):
        """
        removes users with no subscriptions and 
        channels with no subscribers
        """
        logging.info('cleaning db...')

        non_subbed_users=[]
        users=self.session.query(User).all()
        for user in users:
            sub = self.session.query(Subscription).filter_by(user_num=user.user_id).first()
            if sub is None:
                non_subbed_users.append(user)

        unused_channels=[]
        channels = self.session.query(Channel).all()
        for channel in channels:
            sub = self.session.query(Subscription).filter_by(channel_name=channel.name).first()

            if sub is None:
                unused_channels.append(channel)

        logging.info('{0} channels and {1} users can be removed'\
                     .format(len(unused_channels), len(non_subbed_users)))
            
        for channel in unused_channels:
            self.session.delete(channel)
            self.session.commit()

        for user in non_subbed_users:
            self.session.delete(user)
            self.session.commit()
