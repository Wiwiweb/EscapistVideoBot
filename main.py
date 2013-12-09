"""
Fetches the mp4 link of Escapist videos and posts it on Reddit.

Created on 2013-12-09
Author: Wiwiweb

"""

import logging
import sys
from time import sleep

from bs4 import BeautifulSoup
import praw
import requests

VERSION = "1.0"
USER_AGENT = "SakuraiBot v" + VERSION + " by /u/Wiwiweb"

FREQUENCY = 500
POST_LIMIT_PER_RUN = 10

ESCAPIST_DOMAIN = "escapistmagazine.com"

HISTORY_FILENAME = './res/history.txt'

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(asctime)s: %(message)s')

r = praw.Reddit(user_agent=USER_AGENT)


def is_new_submission(submission):
    """Check the history file to see if the submission is new."""
    history = open(HISTORY_FILENAME, 'r')
    next_line = history.readline().strip()
    for _ in range(POST_LIMIT_PER_RUN):
        while next_line:
            if next_line == submission.id:
                return False
            next_line = history.readline().strip()
    return True


def get_mp4_link(url):
    return ''


def post_to_reddit(mp4_link):
    pass


def add_to_history(submission):
    """Add the submission id to the top of the history file."""
    history = open(HISTORY_FILENAME, 'r+')
    old = history.read()
    history.seek(0)
    history.write(submission.id + "\n" + old)
    history.close()


if __name__ == '__main__':
    while True:
        latest_submissions = r.get_domain_listing(ESCAPIST_DOMAIN,
                                                  sort='new',
                                                  limit=POST_LIMIT_PER_RUN)
        for submission in latest_submissions:
            logging.debug('{}: {}'.format(submission.id, submission))
            if is_new_submission(submission):
                logging.info("Found new submission: " + submission.short_link)
                logging.info("url: " + submission.url)
                mp4_link = get_mp4_link(submission.url)
                logging.info("mp4 link: " + mp4_link)
                post_to_reddit(mp4_link)
                logging.info("Comment posted.")
                add_to_history(submission)
                logging.info("Submission remembered.")

        sleep(FREQUENCY)
