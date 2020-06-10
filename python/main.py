#! python3
import time, os
import discord, asyncio

class Globals:
    token = "***REMOVED***"
    client = discord.Client()
    reconnecting = False
    start_time = time.time()
    loop = asyncio.get_event_loop()
    last_pos = 0

    def get_state(self):
        return self.reconnecting

    def set_state(self, state):
        self.reconnecting = state

    def get_last_pos(self):
        return self.last_pos
    
    def set_last_pos(self, new_pos):
        self.last_pos = new_pos

g = Globals()

async def dm(msg):
    user = await g.client.fetch_user(***REMOVED***)
    await user.send(embed=msg)

def notify(title, desc, color):
    embed = discord.Embed()
    embed.title = title
    embed.description = desc
    embed.color = color
    g.loop.run_until_complete(dm(embed))

def minute_passed():
    ret = time.time() - g.start_time >= 60
    if ret:
        g.start_time = time.time()
    return ret

def hour_passed():
    ret = time.time() - g.start_time >= 3600
    if ret:
        g.start_time = time.time()
    return ret

def connected(cur_line, increased, first_time):
    index = cur_line.find("e:")
    current_pos = int(cur_line[3+index:]) # our current position in queue
    loc_time = time.localtime()
    if g.get_last_pos() == current_pos:
            return
    if increased:
        print("Increased! sending msg")
        notify("Welcome to queue!" if first_time else "Still in queue", "Current Time: `{:0>2d}:{:0>2d}`\nCurrent Position: `{}`".format(loc_time.tm_hour, loc_time.tm_min, current_pos), 4437377)
    elif g.get_state():
        notify("Connected", "Connected to 2b2t Queue Server!\nCurrent Position: `{}`".format(current_pos), 4437377)
        g.set_state(False)
    elif current_pos == 1:
        print("about to join server!")
        notify("First in Queue!", "Get to the computer now! You're first in line!", 7506394)
    elif current_pos <= 10:
        print("about to join server!")
        notify("Close to joining!", "Heads up, you're in the top 10!\nCurrent Position: `{}`".format(current_pos), 16763904)
    g.set_last_pos(current_pos)


def disconnected():
    loc_time = time.localtime()
    print("disconnected from 2b2t, sending msg")
    notify("Disconnected", "Dropped from 2b2t Queue Server, attempting to reconnect.\nCurrent Time: `{:0>2d}:{:0>2d}`".format(loc_time.tm_hour, loc_time.tm_min), 15746887)

def server_down():
    loc_time = time.localtime()
    print("server may be down, sending msg")
    notify("Server Down", "You have been dropped from the server >5 times. 2b2t may be down.\nCurrent Time: `{:0>2d}:{:0>2d}`".format(loc_time.tm_hour, loc_time.tm_min), 15746887)

def follow(thefile):
    thefile.seek(0,2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

if __name__ == "__main__":
    logfile = open(os.getenv("APPDATA")+"/.minecraft/logs/latest.log", "r")
    loglines = follow(logfile)
    g.set_state(False)
    asyncio.set_event_loop(g.loop)
    connection_count = 0
    try:
        print("logging into discord")
        g.loop.create_task(g.client.login(g.token))
        print("connecting")
        g.loop.create_task(g.client.connect())
    except KeyboardInterrupt:
        g.loop.run_until_complete(g.client.logout())
    print("connected, now running program")
    it = (line for line in loglines)
    for index, line in enumerate(it):
        if "[main/INFO]: [CHAT] Position in queue:" in line:
            if index == 0: # print our first position
                connected(line, True, True)
            connection_count = 0
            connected(line, hour_passed(), False)
        elif "Started saving saved containers in a new thread" in line:
            disconnected()
            g.set_state(True)
        elif "[main/INFO]: Connecting to 2b2t.org, 25565" in line:
            connection_count += 1
            print("can't connect", connection_count)
            if connection_count >= 5 and not g.get_state():
                server_down()
                g.set_state(True)
        elif "[CHAT] Connecting to the server..." in line:
            notify("Joining 2b2t", "You made it! You are now joining 2b2t", 7506394)
            exit()
