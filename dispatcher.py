import re
from queue import Queue
import logging
from time import sleep

from sqlalchemy.exc import IntegrityError

from models import *
from twitch_check import rate_limit_check

class Dispatcher():

    def __init__(self, db, app):
        self.db_manager=DatabaseManager(db)
        self.app = app
        self.post_data_queue = Queue()

    def run(self):
        self.running = True

        while self.running:
            self.process_user_post()
            self.update_channel_status()
            self.notify_users()

    def process_user_post(self):
        
        while not self.post_data_queue.empty():
            data = json.loads(self.post_data_queue.get())
            data['Channels'] = self.sanitize_channels(data['Channels'])
            self.db_manager.add_channels(data['Channels'])
            
            user_id = db_manager.add_user(data['regID'])
            
            self.db_manager.add_subs(user_id, data['Channels'])

        logging.info('all post data processed')

    def sanitize_channels(self, channels):
        return [re.sub('[!@#$%^&*(){}[];\':"?<>,.=-+]','',name) for name in channels]
        
    def update_channel_status(self):
        logging.info('updating channel status')

        with self.app.app_context():
            channels = self.db_manager.get_all_channels()

        db_status = {channel.name:channel.status for channel in channels}
        twitch_status = rate_limit_check(list(db_status.keys()), 5, 1)

    def notify_users(self):
        logging.info('notifying users of channel status')


class DatabaseManager():

    def __init__(self, db):
        self.db = db

    def add_channels(self, channels):
        for i in channels:

            channel = Channel(name=i, status=0)
            try:
                self.db.session.add(channel)
                self.db.session.commit()
                logging.info('added new channel ' + i + ' to database')
        
            except IntegrityError as ex:
                logging.info('failed to insert new channel: ' +
                             i + ' because it already exists.')
                self.db.session.rollback()

                
    def add_user(self, regid):
        user = User.query.filter_by(reg_id=regid).first()

        if user is None:
            user = User(reg_id=regid)
            self.db.session.add(user)
            self.db.session.commit()
            
        return user.user_id

    def add_subs(self, user_id, channels):
        existing_channels = [sub.channel_name for sub in Subscription.query.filter_by()]
        new_channels = [channel for channel in channels if channel not in existing_channels] 
    
        for channel in new_channels:
            sub = Subscription(user_num=user_id, channel_name=channel)
            self.db.session.add(sub)
            self.db.session.commit()

    def get_all_channels(self):
        return Channel.query.filter_by(status=0)        
