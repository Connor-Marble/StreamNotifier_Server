"""
Module to handle the main update loop of the application
"""

import re
import json
import http.client
import logging

from queue import Queue
from time import sleep, time
from requests import post

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from twitch_check import rate_limit_check
from config import *
from db_manager import DatabaseManager

class Dispatcher():
    """
    Class is responsible for notifying users when
    their subscribed channels going online
    """
    def __init__(self, app):
        self.db_manager=DatabaseManager(app)
        self.app = app
        self.post_data_queue = Queue()
        self.newly_online_channels = []

    def run(self):
        """
        loops through duties of the dispatcher
        for as long as the server is running
        """
        self.running = True

        last_clean=time()
        while self.running:
            logging.info('Beginning update cycle')
            
            cycle_start = time()
            
            self.process_user_post()
            self.update_channel_status()
            self.notify_users()

            extra_time = CYCLE_TIME-(time()-cycle_start)

            if (time()-last_clean)>CLEAN_PERIOD:
                self.db_manager.clean()
                last_clean=time()
            
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
        

