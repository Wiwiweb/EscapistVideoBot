EscapistVideoBot
================

EscapistVideoBot is a reddit bot for fetching mp4 links to video articles from the [Escapist Magazine](http://www.escapistmagazine.com).  
It is made in Python 3 using the libraries [PRAW](https://github.com/praw-dev/praw), [Requests](http://docs.python-requests.org/en/latest/) and [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/)

Videos on the Escapist Magazine are not very convenient to watch. They are filled with ads, in a very small player, and not available for mobile users. A link to the mp4 file of the video is actually available somewhere 2 pages deep. Most people prefer watching the direct mp4 file for flexibility, even non-mobile users.

This bot monitors the escapistmagazine.com submissions on Reddit. If it finds a new one, it will check if the link contains a video. If that's the case, it fetches the mp4 link and posts it as a comment. Only the last 10 submissions are monitored, every 5 minutes, which seems to be enough to catch them all (There's only about 1 new submission per hour on average). Comment and submission history are stored in an SQLite database.

Because the link does not stay valid for very long, the bot will update its posts for 2 days. After that, the link will be removed. 

Usage
-----

Make sure you are using Python 3. If not done already, install the requirements:

`pip install -r requirements.txt`

After that, you will need to fill out the cfg/config-private.ini file with your reddit password, as well as modify the defaults in cfg/config.ini if needed.

Once done, run the bot using the `start.sh` script.

Contribute
----------

Pull requests are welcome, feel free to submit! Keep in mind the code respects [PEP8](http://www.python.org/dev/peps/pep-0008/) and [PEP257](http://www.python.org/dev/peps/pep-0257/). You can verify if they are respected using the existing command line scripts: Download them with `pip install pep8 pep257`.
