#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint: disable=locally-disabled

"""
    Telegram bot that sends a random link from a given subreddit
    Author: Luiz Francisco Rodrigues da Silva <luizfrdasilva@gmail.com>
"""

import sys

import json
import logging
import random
import requests
from telegram import Updater
from telegram.dispatcher import run_async

# Use botan to bot analytics
sys.path.insert(0, 'botan/sdk')
import botan # pylint: disable=import-error

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

BASE_URL = 'http://www.reddit.com'
PAGES = 4

last_request = {} #pylint: disable=invalid-name

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
def random_post(bot, update, **kwargs): # pylint: disable=unused-argument
    """ Get a random post from a givem subreddit """

    global last_request # pylint: disable=global-variable-not-assigned,invalid-name

    request = update.message.text.split(" ")[0]

    if request.find("/more") >= 0:
        try:
            request = last_request[update.message.from_user.id]
        except KeyError as e: # pylint: disable=invalid-name
            print(e)
            bot.sendMessage(update.message.chat_id, text="Failed to send more posts, please"
                                                         " make a new request.")
            return

    url = BASE_URL + request + '.json?count=25&after='

    try:
        posts = []
        after = ""
        # Get links from N pages
        for _ in range(PAGES):
            r = requests.get(url=url + after, headers=CONFIGURATION["requests_header"]) # pylint: disable=invalid-name
            posts += [{"title": post["data"]["title"], "url": post["data"]["url"]}
                      for post in r.json()["data"]["children"]]
            after = r.json()["data"]["after"]
            if after is None:
                break
    except (requests.exceptions.RequestException, KeyError) as e: # pylint: disable=invalid-name
        bot.sendMessage(update.message.chat_id, text="Failed to send link, make sure the"
                                                     " subreddit you requested exist!")
        return

    # Save the user last request
    last_request[update.message.from_user.id] = request

    # Remove first link, its usually a fixed post of the subreddit
    posts = posts[1:]

    post_to_send = random.choice(posts)
    bot.sendMessage(update.message.chat_id, text=post_to_send["title"] + "\n" + post_to_send["url"])


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
              "Source code: https://github.com/heylouiz/radditbot.git"
    bot.sendMessage(update.message.chat_id, text=message)


def error_handler(bot, update, error): # pylint: disable=unused-argument
    """ Log all errors """

    LOGGER.warn('Update "%s" caused error "%s"', update, error) # pylint: disable=deprecated-method


def any_message(bot, update): # pylint: disable=unused-argument
    """ Print to console and log activity with Botan.io """

    botan.track(CONFIGURATION["botan_token"],
                update.message.from_user.id,
                update.message.to_dict(),
                update.message.text.split(" ")[0])

    LOGGER.info("New message\nFrom: %s\nchat_id: %d\nText: %s",
                update.message.from_user,
                update.message.chat_id,
                update.message.text)


def main():
    """ Main function of the bot """

    # Create the EventHandler and pass it your bot's token.
    token = CONFIGURATION["telegram_token"]
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher # pylint: disable=invalid-name

    # on different commands - answer in Telegram
    dp.addTelegramRegexHandler('^\/r\/.*', random_post)  # pylint: disable=anomalous-backslash-in-string
    dp.addTelegramRegexHandler('^/more.*', random_post)
    dp.addTelegramRegexHandler('.*', any_message)
    dp.addTelegramCommandHandler("help", help_command)

    # log all errors
    dp.addErrorHandler(error_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
