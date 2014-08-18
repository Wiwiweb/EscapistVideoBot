"""
Edits existing Reddit posts with updated information.

Created on 2014-05-22
Author: Wiwiweb

"""

from configparser import ConfigParser
from datetime import datetime, timedelta
import json
import logging

import requests

CONFIG_FILE = "../cfg/config.ini"
CONFIG_FILE_PRIVATE = "../cfg/config-private.ini"
config = ConfigParser()
config.read([CONFIG_FILE, CONFIG_FILE_PRIVATE])


class PostUpdater:
    def __init__(self, db_cursor, reddit, debug=False):
        self.db_cursor = db_cursor
        self.reddit = reddit
        self.debug = debug

    def check_all_posts(self):
        """Check every previous comment to see if they need to be updated."""
        sql_query = 'SELECT * FROM comments'
        self.db_cursor.execute(sql_query)
        result = self.db_cursor.fetchall()
        time_now = datetime.utcnow()
        logging.debug("The time is " + str(time_now))
        for comment_table in result:
            # comment table structure:
            # comment_url, js_page, mp4_link, date_created, date_modified
            logging.debug(comment_table[0])

            submission = self.reddit.get_submission(comment_table[0])
            comment = submission.comments[0]
            logging.debug("Score: " + str(comment.score))

            if comment.score < 0:
                logging.info("Deleting post " + comment_table[0])
                self.delete_post(comment)
                logging.info("Deleted post.")
                return

            created_time = datetime.strptime(comment_table[3], '%Y-%m-%d %H:%M:%S')
            modified_time = datetime.strptime(comment_table[4], '%Y-%m-%d %H:%M:%S')
            logging.debug("Created at " + str(created_time))
            logging.debug("Modified at " + str(modified_time))
            expire_hours = int(config['Main']['expire_hours'])
            update_minutes = int(config['Main']['update_minutes'])

            if created_time + timedelta(hours=expire_hours) < time_now:
                logging.info("Expiring post " + comment_table[0])
                self.expire_post(comment)
                logging.info("Expired post.")
            elif modified_time + timedelta(minutes=update_minutes) < time_now:
                logging.info("Updating post " + comment_table[0])
                new_mp4_link = self.fetch_new_link(comment_table[1])
                if new_mp4_link != comment_table[2]:
                    self.update_post(comment, new_mp4_link)
                    logging.info("Updated post.")
                else:
                    logging.info("Did not update, link hasn't changed.")

    def fetch_new_link(self, js_page):
        """Get the mp4 link from a js page."""
        headers = {'User-Agent': config['Main']['user_agent']}
        req = requests.get(js_page, headers=headers)
        req.connection.close()
        # Single quote is not valid JSON
        js_text = req.text.replace('\'', '"')
        js_object = json.loads(js_text)
        mp4_link = js_object['playlist'][1]['url']
        return mp4_link

    def update_post(self, comment, mp4_link):
        """Update the reddit comment with the new mp4 link."""
        body = config['Comment']['body']\
            .format(mp4_link, config['Main']['dereferrer'])
        if not self.debug:
            comment.edit(body)
            sql_query = "UPDATE comments " \
                        "SET mp4_link=?, date_modified=datetime('now') " \
                        "WHERE comment_url=?"
            self.db_cursor.execute(sql_query, (mp4_link, comment.permalink))
        else:
            logging.debug("Comment that would have been edited: " + body)

    def expire_post(self, comment):
        """Strikeout the mp4 link from an old reddit comment."""
        body = config['Comment']['expired_body'] \
            .format(config['Main']['expire_hours'])
        if not self.debug:
            comment.edit(body)
            sql_query = "DELETE FROM comments " \
                        "WHERE comment_url=?"
            self.db_cursor.execute(sql_query, (comment.permalink,))
        else:
            logging.debug("Comment that would have been expired: " + body)

    def delete_post(self, comment):
        """Delete the comment due to negative score."""
        if not self.debug:
            comment.delete()
            sql_query = "DELETE FROM comments " \
                        "WHERE comment_url=?"
            self.db_cursor.execute(sql_query, (comment.permalink,))
        else:
            logging.debug("This comment would have been deleted.")