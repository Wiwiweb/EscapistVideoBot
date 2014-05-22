"""
Fetches the mp4 link of Escapist videos and posts it on Reddit.

Created on 2013-12-09
Author: Wiwiweb

"""

from configparser import ConfigParser
import json
import logging
import urllib.parse
import re
import sqlite3

from bs4 import BeautifulSoup
import praw
import requests

CONFIG_FILE = "../cfg/config.ini"
CONFIG_FILE_PRIVATE = "../cfg/config-private.ini"
config = ConfigParser()
config.read([CONFIG_FILE, CONFIG_FILE_PRIVATE])


class PostCreator:
    def __init__(self, db_cursor, debug=False):
        self.db_cursor = db_cursor
        self.debug = debug

    def process_submission(self, submission):
        if self.is_new_submission(submission):
            logging.info("Found new submission: {} - {}".format(
                submission.short_link, submission))
            logging.info("url: " + submission.url)
            mp4_link = self.get_mp4_link(submission.url)

            if mp4_link:
                logging.info("mp4 link: " + str(mp4_link))
                success = self.post_to_reddit(submission, mp4_link)
                logging.info("Comment posted.")
            else:
                logging.info("No video in this link")
                success = True

            if success:
                self.add_to_history(submission)
                logging.info("Submission remembered.")

    def is_new_submission(self, submission):
        """Check the history file and return True if the submission is new."""
        history = open(config['Files']['history'], 'r')
        next_line = history.readline().strip()
        for _ in range(int(config['Main']['post_limit_per_run'])):
            while next_line:
                if next_line == submission.id:
                    history.close()
                    return False
                next_line = history.readline().strip()
        history.close()
        return True

    def get_mp4_link(self, url):
        """Return the mp4 link from the escapist ur or None."""
        req = requests.get(url)
        soup = BeautifulSoup(req.text)
        soup_object = soup.find('object', id='player_api')
        if soup_object:
            soup_param = soup_object.find('param', attrs={'name': 'flashvars'})
            soup_href = urllib.parse.unquote(soup_param.get('value'))
            js_url = re.search(r'config=(http://.+?\.js)', soup_href).group(1)
            logging.debug("js_url: " + js_url)
            headers = {'User-Agent': config['Main']['user_agent']}
            req = requests.get(js_url, headers=headers)

            # Single quote is not valid JSON
            js_text = req.text.replace('\'', '"')
            js_object = json.loads(js_text)
            mp4_link = js_object['playlist'][1]['url']
            return mp4_link
        else:
            return None

    def post_to_reddit(self, submission, mp4_link):
        """Post the link to the reddit thread. Return True if succeeded."""
        comment = "[Direct mp4 link]({})" \
            .format(mp4_link)
        if not self.debug:
            try:
                submission.add_comment(comment)
                return True
            except praw.errors.RateLimitExceeded as e:
                logging.error("ERROR: RateLimitExceeded: " + str(e))
                logging.error("Skipping to next link.")
                return False
            except praw.errors.APIException as e:
                if e.error_type == 'DELETED_LINK':
                    logging.error("ERROR: Submission was deleted.")
                    return True
                else:
                    raise e
        else:
            logging.debug("Comment that would have been posted: " + comment)
            return True

    def add_to_history(self, submission):
        """Add the submission id to the top of the history file."""
        history = open(config['Files']['history'], 'r+')
        old = history.read()
        history.seek(0)
        if not self.debug:
            history.write(submission.id + '\n' + old)
        history.close()