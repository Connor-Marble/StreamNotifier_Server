import re
import json
import logging

from queue import Queue
from time import sleep, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from models import *
from twitch_check import rate_limit_check
from config import *

class Dispatcher():

    def __init__(self, db, app):
        self.db_manager=DatabaseManager(db)
        self.app = app
        self.post_data_queue = Queue()

    def run(self):
        self.running = True

        while self.running:
            logging.info('Beginning update cycle')
            
            cycle_start = time()
            
            self.process_user_post()
            self.update_channel_status()
            self.notify_users()

            extra_time = CYCLE_TIME-(time()-cycle_start)

            if extra_time > 0:
                logging.info('waiting %s seconds before next refresh' % int(extra_time))
                sleep(extra_time)

    def process_user_post(self):
        
        while not self.post_data_queue.empty():
            data = json.loads(self.post_data_queue.get())
            data['Channels'] = self.sanitize_channels(data['Channels'])
            self.db_manager.add_channels(data['Channels'])
            
            user_id = self.db_manager.add_user(data['regID'])
            
            self.db_manager.add_subs(user_id, data['Channels'])

        logging.info('all post data processed')

    def sanitize_channels(self, channels):
        return ["".join(re.findall("[a-zA-Z0-9_]", name)) for name in channels]
        
    def update_channel_status(self):
        logging.info('updating channel status')

        with self.app.app_context():
            channels = self.db_manager.get_all_channels()

        db_status = {channel.name:channel.status for channel in channels}
        server_status = rate_limit_check(list(db_status.keys()))
        logging.info (server_status)

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
                logging.warning('failed to insert new channel: ' +
                             i + ' because it already exists.')
                self.db.session.rollback()

            except FlushError as ex:
                logging.warning('failed to insert channel: ' + i + 'due to flush error')

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
