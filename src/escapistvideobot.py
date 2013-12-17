"""
Fetches the mp4 link of Escapist videos and posts it on Reddit.

Created on 2013-12-09
Author: Wiwiweb

"""

from configparser import ConfigParser
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import re
import sys
from time import sleep
import urllib.parse

from bs4 import BeautifulSoup
import praw
import requests

CONFIG_FILE = "../cfg/config.ini"
CONFIG_FILE_PRIVATE = "../cfg/config-private.ini"
config = ConfigParser()
config.read([CONFIG_FILE, CONFIG_FILE_PRIVATE])

VERSION = "1.0"
USER_AGENT = "SakuraiBot v" + VERSION + " by /u/Wiwiweb"

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


def is_new_submission(submission):
    """Check the history file to see if the submission is new."""
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


def get_mp4_link(url):
    """Get the mp4 link from the escapist url, or None if it has no video."""
    req = requests.get(url)
    soup = BeautifulSoup(req.text)
    soup_link = soup.find('link', rel='video_src')
    if soup_link:
        soup_href = urllib.parse.unquote(soup_link.get('href'))
        js_url = re.search(r'config=(http://.+?\.js)', soup_href).group(1)
        req = requests.get(js_url)
        # Single quote is not valid JSON
        js_text = req.text.replace('\'', '"')
        mp4_link = json.loads(js_text)['playlist'][1]['url']
        return mp4_link
    else:
        return None


def post_to_reddit(submission, mp4_link):
    """Post the link to the reddit thread. Return True if succeeded."""
    comment = "[Direct mp4 link]({})".format(mp4_link)
    if not debug:
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


def add_to_history(submission):
    """Add the submission id to the top of the history file."""
    history = open(config['Files']['history'], 'r+')
    old = history.read()
    history.seek(0)
    if not debug:
        history.write(submission.id + '\n' + old)
    history.close()


if __name__ == '__main__':
    r = praw.Reddit(user_agent=USER_AGENT)
    r.login(config['Reddit']['username'], config['Passwords']['reddit'])

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

                    if is_new_submission(submission):
                        logging.info("Found new submission: {} - {}".format(
                            submission.short_link, submission))
                        logging.info("url: " + submission.url)
                        mp4_link = get_mp4_link(submission.url)

                        if mp4_link:
                            logging.info("mp4 link: " + str(mp4_link))
                            success = post_to_reddit(submission, mp4_link)
                            logging.info("Comment posted.")
                        else:
                            logging.info("No video in this link")
                            success = True

                        if success:
                            add_to_history(submission)
                            logging.info("Submission remembered.")

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