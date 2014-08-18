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
            logging.info("Found new submission in /r/{}: {} - {}".format(
                submission.subreddit, submission.short_link, submission))
            logging.info("url: " + submission.url)
            comment_url = None
            js_page = None
            mp4_link = None
            if '/videos/' in submission.url:
                mp4_link, js_page = self.get_mp4_link(submission.url)
                if mp4_link:
                    logging.info("mp4 link: " + str(mp4_link))
                    success, comment_url =\
                        self.post_to_reddit(submission, mp4_link)
                    logging.info("Comment posted.")
                else:
                    logging.info("No video in this link")
                    success = True
            else:
                logging.info("Does not contain '/video/' in URL")
                success = True

            if success:
                self.add_to_history(submission)
                logging.info("Submission remembered.")
                if comment_url:
                    self.add_to_comment_list(comment_url, js_page, mp4_link)
                    logging.info("Comment remembered.")

    def is_new_submission(self, submission):
        """Check the history file and return True if the submission is new."""
        sql_query = \
            'SELECT submission_url FROM history WHERE submission_url=? LIMIT 1'
        self.db_cursor.execute(sql_query, (submission.id,))
        result = self.db_cursor.fetchone()
        return result is None

    def get_mp4_link(self, url):
        """Return the mp4 link and js page from an escapist url or None."""
        req = requests.get(url)
        req.connection.close()
        soup = BeautifulSoup(req.text)
        soup_object = soup.find('object', id='player_api')
        if soup_object:
            soup_param = soup_object.find('param', attrs={'name': 'flashvars'})
            soup_href = urllib.parse.unquote(soup_param.get('value'))
            js_page = re.search(r'config=(http://.+?\.js)', soup_href).group(1)
            logging.debug("js_url: " + js_page)
            headers = {'User-Agent': config['Main']['user_agent']}
            req = requests.get(js_page, headers=headers)
            req.connection.close()

            # Single quote is not valid JSON
            js_text = req.text.replace('\'', '"')
            js_object = json.loads(js_text)
            mp4_link = js_object['playlist'][1]['url']
            return mp4_link, js_page
        else:
            return None, None

    def post_to_reddit(self, submission, mp4_link):
        """Post the link to the reddit thread.

        Return True and the permalink to the comment if succeeded.
        """
        body = config['Comment']['body']\
            .format(mp4_link, config['Main']['dereferrer'])
        if not self.debug:
            try:
                comment = submission.add_comment(body)
                return True, comment.permalink
            except praw.errors.RateLimitExceeded as e:
                logging.error("ERROR: RateLimitExceeded: " + str(e))
                logging.error("Skipping to next link.")
                return False, None
            except praw.errors.APIException as e:
                if e.error_type == 'DELETED_LINK':
                    logging.warning("WARNING: Submission was deleted.")
                    return True, None
                else:
                    raise e
            except requests.HTTPError as e:
                if 403 in str(e):
                    logging.warning("WARNING: Banned from the subreddit.")
                    return True, None
                else:
                    raise e
        else:
            logging.debug("Comment that would have been posted: " + body)
            return True, None

    def add_to_history(self, submission):
        """Add the submission id to the history database."""
        if not self.debug:
            sql_query = 'INSERT INTO history VALUES (?)'
            self.db_cursor.execute(sql_query, (submission.id,))

    def add_to_comment_list(self, comment_url, js_page, mp4_link):
        if not self.debug:
            sql_query = "INSERT INTO comments VALUES " \
                        "(?,?,?,datetime('now'),datetime('now'))"
            self.db_cursor.execute(sql_query, (comment_url, js_page, mp4_link))
