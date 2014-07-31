"""
Main bot loop.

Created on 2013-12-09
Author: Wiwiweb

"""

from configparser import ConfigParser
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import sqlite3
import sys
from time import sleep

import praw

from post_creator import PostCreator
from post_updater import PostUpdater

CONFIG_FILE = "../cfg/config.ini"
CONFIG_FILE_PRIVATE = "../cfg/config-private.ini"
config = ConfigParser()
config.read([CONFIG_FILE, CONFIG_FILE_PRIVATE])

VERSION = "2.0"
USER_AGENT = "EscapistVideoBot v" + VERSION + " by /u/Wiwiweb"

ESCAPIST_DOMAIN = "escapistmagazine.com"


if '--debug' in sys.argv:
    debug = True
else:
    debug = False
if '--no-new-posts' in sys.argv:
    no_new_posts = True
else:
    no_new_posts = False

if debug:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(asctime)s: %(message)s')
else:
    root_logger = logging.getLogger()
    timed_handler = TimedRotatingFileHandler(config['Files']['logfile'],
                                             'midnight')
    timed_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    timed_handler.setLevel(logging.INFO)
    debug_handler = RotatingFileHandler(config['Files']['debug_logfile'],
                                        maxBytes=1024000,
                                        backupCount=1)
    debug_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    debug_handler.setLevel(logging.DEBUG)
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(timed_handler)
    root_logger.addHandler(debug_handler)

# Silence python requests
requests_log = logging.getLogger('urllib3')
requests_log.setLevel(logging.WARN)


if __name__ == '__main__':
    logging.info("--- Starting EscapistVideoBot ---")
    if debug:
        logging.info("--- Debug mode ---")
    if no_new_posts:
        logging.info("--- New posts will not be created ---")
    reddit = praw.Reddit(user_agent=USER_AGENT)
    reddit.login(config['Reddit']['username'], config['Passwords']['reddit'])
    db_connection = sqlite3.connect(config['Files']['history'])
    db_cursor = db_connection.cursor()

    sql_query = \
        'CREATE TABLE IF NOT EXISTS history(submission_url TEXT)'
    db_cursor.execute(sql_query)
    sql_query = \
        'CREATE TABLE IF NOT EXISTS comments' \
        '(comment_url TEXT, js_page TEXT, mp4_link TEXT,' \
        ' date_created TEXT, date_modified TEXT)'
    db_cursor.execute(sql_query)

    post_creator = PostCreator(db_cursor, debug)
    post_updater = PostUpdater(db_cursor, reddit, debug)

    retries = 5

    try:
        while True:
            try:
                logging.info("Starting new cycle.")

                post_updater.check_all_posts()

                if not no_new_posts:
                    latest_submissions = reddit.get_domain_listing(
                        ESCAPIST_DOMAIN, sort='new',
                        limit=int(config['Main']['post_limit_per_run']))

                    for submission in latest_submissions:
                        logging.debug('{}: {}'.
                                      format(submission.id, submission))
                        post_creator.process_submission(submission)
                        db_connection.commit()

                retries = 5
            except Exception as e:
                logging.exception("ERROR: Unknown error: " + str(e))
                retries -= 1
                logging.error(
                    "Waiting another cycle. {} more tries".format(retries))

            sleep(int(config['Main']['frequency']))

    except KeyboardInterrupt:
        logging.info(
            "Keyboard interrupt detected, shutting down EscapistVideoBot.")
        quit()
