"""
Main bot loop.

Created on 2013-12-09
Author: Wiwiweb

"""

from configparser import ConfigParser
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from time import sleep

import praw
import sqlite3

from post_creator import PostCreator
from post_updater import PostUpdater

CONFIG_FILE = "../cfg/config.ini"
CONFIG_FILE_PRIVATE = "../cfg/config-private.ini"
config = ConfigParser()
config.read([CONFIG_FILE, CONFIG_FILE_PRIVATE])

VERSION = "1.0"
USER_AGENT = "EscapistVideoBot v" + VERSION + " by /u/Wiwiweb"

ESCAPIST_DOMAIN = "escapistmagazine.com"

if len(sys.argv) > 1 and '--debug' in sys.argv:
    debug = True
else:
    debug = False

if debug:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(asctime)s: %(message)s')
else:
    root_logger = logging.getLogger()
    timed_handler = TimedRotatingFileHandler(config['Files']['logfile'],
                                             'midnight')
    timed_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    timed_handler.setLevel(logging.INFO)
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(timed_handler)

# Silence python requests
requests_log = logging.getLogger('requests')
requests_log.setLevel(logging.ERROR)


if __name__ == '__main__':
    r = praw.Reddit(user_agent=USER_AGENT)
    r.login(config['Reddit']['username'], config['Passwords']['reddit'])
    db_connection = sqlite3.connect(config['Files']['history'])
    db_cursor = db_connection.cursor()

    post_creator = PostCreator(db_cursor, debug)

    retries = 5

    try:
        while True:
            try:
                logging.info("Starting new cycle.")
                latest_submissions = r.get_domain_listing(
                    ESCAPIST_DOMAIN, sort='new',
                    limit=int(config['Main']['post_limit_per_run']))

                for submission in latest_submissions:
                    logging.debug('{}: {}'.format(submission.id, submission))
                    post_creator.process_submission(submission)

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
