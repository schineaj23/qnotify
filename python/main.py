#! python3
import os
import sys
import time
import asyncio
import discord


class Globals:
    token = ""
    user_id = 0
    channel_id = 0
    client = discord.Client()
    reconnecting = False
    loop = asyncio.get_event_loop()
    last_pos = 0
    debug = False
    start_pos = 0
    first_time = True

    def get_state(self):
        return self.reconnecting

    def set_state(self, state):
        self.reconnecting = state

    def get_last_pos(self):
        return self.last_pos

    def set_last_pos(self, new_pos):
        self.last_pos = new_pos


g = Globals()
START_TIME = 0


def get_start_time():
    global START_TIME
    return START_TIME


def set_start_time(n):
    global START_TIME
    START_TIME = n


async def dm(msg):
    user = await g.client.fetch_user(g.user_id)
    await user.send(embed=msg)


async def txt(msg):
    text_channel = await g.client.fetch_channel(g.channel_id)
    await text_channel.send(embed=msg)


def notify(title, desc, color, field=False, field_stats=""):
    embed = discord.Embed()
    if field:
        embed.add_field(name="Your Stats", value=field_stats)
    if g.debug:
        embed.title = "DEBUG: " + title
        embed.description = "**This is a test from GitHub**\n**Platform:** `{}`\n".format(
            sys.platform) + desc
        embed.color = color
        g.loop.run_until_complete(txt(embed))
    else:
        embed.title = title
        embed.description = desc
        embed.color = color
        g.loop.run_until_complete(dm(embed))


def minute_passed():
    ret = time.time() - get_start_time() >= 59
    print("{} {}".format(ret, time.time()-get_start_time()))
    if ret:
        set_start_time(time.time())
    return ret


def hour_passed():
    ret = time.time() - get_start_time() >= 3599
    print("{} {}".format(ret, time.time()-get_start_time()))
    if ret:
        set_start_time(time.time())
    return ret


def connected(cur_line, increased):
    index = cur_line.find("e:")
    current_pos = int(cur_line[3+index:])  # our current position in queue
    loc_time = time.localtime()
    if g.get_last_pos() == current_pos:
        return
    if g.first_time:
        g.start_pos = current_pos
    if increased:
        print("Increased! sending msg")
        msg = "Current Time: `{:0>2d}:{:0>2d}`\nCurrent Position: `{}`".format(
            loc_time.tm_hour, loc_time.tm_min, current_pos)
        notify("Welcome to queue!" if g.first_time else "Still in queue", msg, 4437377)
    elif g.get_state():
        notify("Connected", "Connected to 2b2t Queue Server!\nCurrent Position: `{}`".format(
            current_pos), 4437377)
        g.set_state(False)
    elif current_pos == 1:
        print("about to join server!")
        notify("First in Queue!",
               "Get to the computer now! You're first in line!", 7506394)
    elif current_pos <= 10:
        print("about to join server!")
        notify("Close to joining!", "Heads up, you're in the top 10!\nCurrent Position: `{}`".format(
            current_pos), 16763904)
    g.first_time = False
    g.set_last_pos(current_pos)


def disconnected():
    loc_time = time.localtime()
    print("disconnected from 2b2t, sending msg")
    notify("Disconnected", "Dropped from 2b2t Queue Server, attempting to reconnect.\nCurrent Time: `{:0>2d}:{:0>2d}`".format(
        loc_time.tm_hour, loc_time.tm_min), 15746887)


def server_down():
    loc_time = time.localtime()
    print("server may be down, sending msg")
    notify("Server Down", "You have been dropped from the server >5 times. 2b2t may be down.\nCurrent Time: `{:0>2d}:{:0>2d}`".format(
        loc_time.tm_hour, loc_time.tm_min), 15746887)


def follow(thefile):
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

def get_platform_lines():
    try:
        if sys.platform.startswith('win32'):
            logfile = open(os.getenv("APPDATA") +
                           "/.minecraft/logs/latest.log", "r")
        elif sys.platform.startswith('linux'):  # linux people be like:
            logfile = open("~/.minecraft/logs/latest.log", "r")
        else:  # mac people be like
            logfile = open("~/Library/Application Support/minecraft", "r")
        loglines = follow(logfile)
    except:  # imagine not having minecraft
        logfile = open(".test/batch.txt")
        loglines = logfile.readlines()
        g.debug = True
    return loglines

def connect_to_discord():
    try:
        g.token = os.getenv('API_TOKEN')
        g.user_id = int(os.getenv('API_USER'))
        if(g.debug):
            g.channel_id = int(os.getenv('API_TEST'))
    except:
        print("could not find any environment variables, using vars from globals")
    try:
        print("logging into discord")
        g.loop.create_task(g.client.login(g.token))
        print("connecting")
        g.loop.create_task(g.client.connect())
    except KeyboardInterrupt:
        g.loop.run_until_complete(g.client.logout())

if __name__ == "__main__":
    loglines = get_platform_lines()
    g.set_state(False)
    asyncio.set_event_loop(g.loop)
    connect_to_discord()
    CONNECTION_COUNT = 0
    TOTAL_CONNECTION_COUNT = 0
    ABSOLUTE_START_TIME = time.time()
    print("connected, now running program")
    it = (line for line in loglines)
    for index, line in enumerate(it):
        if "[main/INFO]: [CHAT] Position in queue:" in line:
            if g.first_time:  # print our first position
                connected(line, True)
            CONNECTION_COUNT = 0
            connected(line, minute_passed())
            print(line)
        elif "Started saving saved containers in a new thread" in line:
            disconnected()
            g.set_state(True)
        elif "[main/INFO]: Connecting to 2b2t.org, 25565" in line:
            CONNECTION_COUNT += 1
            TOTAL_CONNECTION_COUNT += 1
            print("can't connect", CONNECTION_COUNT)
            if CONNECTION_COUNT >= 5:
                server_down()
                g.set_state(True)
                CONNECTION_COUNT = 0
        elif "[CHAT] Connecting to the server..." in line:
            notify("Joining 2b2t", "You made it! You are now joining 2b2t", 7506394, True, "Time Elapsed: `{}` minutes\nStarting Position: `{}`\nDisconnections: `{}`".format(
                int((time.time()-ABSOLUTE_START_TIME)/60), g.start_pos, TOTAL_CONNECTION_COUNT))
            sys.exit()
