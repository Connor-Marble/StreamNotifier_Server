import re
import json
import http.client
import logging

from queue import Queue
from time import sleep, time
from requests import post

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from models import *
from twitch_check import rate_limit_check
from config import *

class Dispatcher():

    def __init__(self, db, app):
        self.db_manager=DatabaseManager(db, app)
        self.app = app
        self.post_data_queue = Queue()
        self.newly_online_channels = []

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

        channels = self.db_manager.get_all_channels()

        db_status = {channel.name.lower():channel.status for channel in channels}
        server_status = rate_limit_check(list(db_status.keys()))

        new_online = []
        new_offline = []
        
        for channel_name in db_status.keys():
            if db_status[channel_name]<server_status[channel_name]:
                new_online.append(channel_name)
                self.newly_online_channels.append(channel_name)
                
            elif db_status[channel_name]>server_status[channel_name]:
                new_offline.append(channel_name)


        logging.info('{} channels just came online'.format(len(new_online)))
        logging.info(('{} channels just went offline').format(len(new_offline)))

        logging.info(self.newly_online_channels)
        
        self.db_manager.update_channels_status(new_offline, 0)
        self.db_manager.update_channels_status(new_online, 1)

    def notify_users(self):

        users = self.db_manager.get_subbed_users(self.newly_online_channels)
        

        
        if len(users) is 0:
            logging.info('no users need to be notified')
            return

        logging.info('notifying users of channel status')
        reg_ids = []
        for user in users:
            logging.info(('notifying user {user.user_id} of status').format(user=user))
            reg_ids.append(user.reg_id)

        data = {'registration_ids':reg_ids}
        
        content = json.dumps(data)
        headers ={"Content-type":"application/json", "Authorization":"key="+API_KEY}

        response = post(url='https://android.googleapis.com/gcm/send', data=content, headers=headers)
        logging.info(response.text)

        self.newly_online_channels = []
        

class DatabaseManager():

    def __init__(self, db, app):
        self.db = db
        self.app = app

    def add_channels(self, channels):
        for i in channels:
            logging.info('processing {}'.format(i))
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
        with self.app.app_context():
            return Channel.query.all()

    def update_channels_status(self, channels, status):

        for channel_name in channels:
            channel = Channel.query.filter_by(name=channel_name).first()
            
            if channel is not None :

                new_channel = Channel(name=channel_name, status=status)
                db.session.delete(channel)
                db.session.add(new_channel)
                
                logging.info("changing status of {0} to {1}"
                             .format(channel_name, status))
                try:
                    self.db.session.commit()
                except:
                    logging.info("problem updating status of []".format(channel_name))
                    self.db.session.rollback()

        self.db.session.commit()

    def get_subbed_users(self, channels):
        users = set()
        queries=[]
        with self.app.app_context():
            for ch_name in channels:
                queries.append(Subscription.query.filter_by(channel_name=ch_name).all())

            subscriptions = [sub for result in queries for sub in result]
            for sub in subscriptions:
                users.add(User.query.filter_by(user_id=sub.user_num).first())

        return users
                
