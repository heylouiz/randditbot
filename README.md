# randditbot

A Telegram bot written in Python that sends a random link from a given subreddit.
Note: Only works in Python 3!

Dependencies

Python Telegram Bot (https://github.com/python-telegram-bot/python-telegram-bot):
To install in Debian based distributions:
sudo pip3 install python-telegram-bot

requests (http://docs.python-requests.org/en/latest/):
sudo pip3 install requests

botan.io (https://github.com/botanio/sdk/):
It's added as a git submodule, just run: git submodule init && git submodule update

After all the requirements are installed you can run the bot using the command:
python3 randditbot.py

Theres a script to keep the bot running "forever", you can run it with ./run_forever.sh

If you have any doubts let me know!
