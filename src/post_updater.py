"""
Edits existing Reddit posts with updated information.

Created on 2014-05-22
Author: Wiwiweb

"""


class PostUpdater:
    def __init__(self, db_cursor, debug=False):
        self.db_cursor = db_cursor
        self.debug = debug

    def check_all_posts(self):
        """Check every previous comment to see if they need to be updated"""
        pass

    def fetch_new_link(self, js_page):
        """Get the mp4 link from a js page"""
        pass

    def update_post(self, post_url, mp4_link):
        """Update the reddit comment with the new mp4 link"""
        pass

    def expire_post(self, post_url):
        """Strikeout the mp4 link from an old reddit comment"""
        pass