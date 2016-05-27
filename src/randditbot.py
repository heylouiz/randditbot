#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint: disable=locally-disabled

"""
    Telegram bot that sends a random link from a given subreddit
    Author: Luiz Francisco Rodrigues da Silva <luizfrdasilva@gmail.com>
"""

import json
import logging
import random
import requests

from telegram.ext import Updater
from telegram.ext.dispatcher import run_async
from telegram.ext import CommandHandler, RegexHandler
from telegram.utils.botan import Botan

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

BASE_URL = 'http://www.reddit.com'
PAGES = 4

# Read configuration from the config file.
# It also contains the header used in requests.get
# Reddit limits drastically requests to their site if you are using
# the default python user-agent.
# They encorage you to use your own user-agent with a little information
# about your app.
# See: https://github.com/reddit/reddit/wiki/API
with open('config.json') as config_file:
    CONFIGURATION = json.load(config_file)

@run_async
def random_post(bot, update, last_request):
    """ Get a random post from a givem subreddit """

    request = update.message.text.split(" ")[0]

    if request.find("/more") >= 0:
        try:
            request = last_request[update.message.from_user.id]
        except KeyError:
            bot.send_message(update.message.chat_id, text="Failed to send more posts, please"
                                                          " make a new request.")
            return

    url = BASE_URL + request + '.json?count=25&after='

    # Open requests session to improve speed
    req = requests.Session()

    try:
        posts = list()
        after = ""
        # Get links from N pages
        for _ in range(PAGES):
            r = req.get(url=url + after, headers=CONFIGURATION["requests_header"]) # pylint: disable=invalid-name
            posts += [{"title": post["data"]["title"], "url": post["data"]["url"]}
                      for post in r.json()["data"]["children"]]
            after = r.json()["data"]["after"]
            if after is None:
                break
    except (requests.exceptions.RequestException, KeyError):
        bot.send_message(update.message.chat_id, text="Failed to send link, make sure the"
                                                      " subreddit you requested exist!")
        return

    # Save the user last request
    last_request[update.message.from_user.id] = request

    # Remove first link, its usually a fixed post of the subreddit
    posts = posts[1:]

    post_to_send = random.choice(posts)
    bot.send_message(update.message.chat_id,
                     text=post_to_send["title"] + "\n" + post_to_send["url"])


def help_command(bot, update):
    """ Get the help message of this bot """

    message = "Randditbot!\n" +\
              "This bot sends a random link from any subreddit.\n\n" +\
              "Usage example:\n" +\
              "Send \"/r/pics\" to the bot in a private or in a group chat and \n" +\
              "the bot will return a random link from \"/r/pics\".\n" +\
              "If you want more links from the previous request, use the command \"/more\".\n\n" +\
              "If you find any bugs or want to make a feature request just send me a message!\n" +\
              "Developer: @heylouiz\n" +\
              "Source code: https://github.com/heylouiz/randditbot.git"
    bot.send_message(update.message.chat_id, text=message)


def error_handler(update, error):
    """ Log all errors """

    LOGGER.warning('Update "%s" caused error "%s"', update, error)


def any_message(update, botan):
    """ Print to console and log activity with Botan.io """

    botan.track(update.message,
                update.message.text.split(" ")[0])

    LOGGER.info("New message\nFrom: %s\nchat_id: %d\nText: %s",
                update.message.from_user,
                update.message.chat_id,
                update.message.text)


def main():
    """ Main function of the bot """

    # Create a Botan tracker object
    botan = Botan(CONFIGURATION["botan_token"])

    # Last user request
    last_request = {}

    # Create the EventHandler and pass it your bot's token.
    token = CONFIGURATION["telegram_token"]
    updater = Updater(token)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(RegexHandler('/r/.*',
                                                lambda bot, update: random_post(bot,
                                                                                update,
                                                                                last_request)))
    updater.dispatcher.add_handler(CommandHandler('more',
                                                  lambda bot, update: random_post(bot,
                                                                                  update,
                                                                                  last_request)))
    updater.dispatcher.add_handler(RegexHandler('/r/.*',
                                                lambda bot, update: any_message(update, botan)),
                                   group=1)
    updater.dispatcher.add_handler(CommandHandler('more',
                                                  lambda bot, update: any_message(update, botan)),
                                   group=1)

    # log all errors
    updater.dispatcher.add_error_handler(lambda bot, update, error: error_handler(update, error))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
