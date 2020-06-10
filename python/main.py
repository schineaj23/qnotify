#! python3
import time, os
import discord, asyncio

token = "NzIwMjc4MjA4OTIxOTkzMjk3.XuEDQQ.Zp76NSVPqY8OLrBvN1sd552yym8"
client = discord.Client()

async def dm(msg):
    user = await client.fetch_user(528600920787779607)
    await user.send(embed=msg)

reconnecting = False
start_time = time.time()
loop = asyncio.get_event_loop()

def get_state():
    global reconnecting
    return reconnecting

def set_state(state):
    global reconnecting
    reconnecting = state

def minute_passed():
    global start_time
    ret = time.time() - start_time >= 60
    if ret:
        start_time = time.time()
    return ret

def hour_passed():
    global start_time
    ret = time.time() - start_time >= 3600
    if ret:
        start_time = time.time()
    return ret

def connected(cur_line, increased, first_time):
    print(cur_line)
    index = cur_line.find("e:")
    current_pos = int(cur_line[3+index:]) # our current position in queue
    print(current_pos)
    print(get_state())
    loc_time = time.localtime()
    if increased:
        print("Increased! sending msg")
        embed = discord.Embed()
        embed.title = "Welcome to queue!" if first_time else "Still in queue" 
        embed.description = "Current Time: `{:0>2d}:{:0>2d}`\nCurrent Position: `{}`".format(loc_time.tm_hour, loc_time.tm_min, current_pos)
        embed.color = 4437377
        loop.run_until_complete(dm(embed))
    elif get_state():
        embed = discord.Embed()
        embed.title = "Connected"
        embed.description = "Connected to 2b2t Queue Server!\nCurrent Position: `{}`".format(current_pos)
        embed.color = 4437377
        loop.run_until_complete(dm(embed))
        set_state(False)
    elif current_pos == 1:
        print("about to join server!")
        embed = discord.Embed()
        embed.title = "First in Queue!"
        embed.description = "Get to the computer now! You're first in line!"
        embed.color = 7506394
        loop.run_until_complete(dm(embed))
    elif current_pos <= 10:
        print("about to join server!")
        embed = discord.Embed()
        embed.title = "Close to joining!"
        embed.description = "Heads up, you're in the top 10!\nCurrent Position: `{}`".format(current_pos)
        embed.color = 16763904
        loop.run_until_complete(dm(embed))


def disconnected():
    loc_time = time.localtime()
    print("disconnected from 2b2t, sending msg")
    print("\nDisconnected from 2b2t as of {:0>2d}:{:0>2d}! Attempting to reconnect.".format(loc_time.tm_hour, loc_time.tm_min))
    embed = discord.Embed()
    embed.title = "Disconnected"
    embed.description = "Dropped from 2b2t Queue Server, attempting to reconnect.\nCurrent Time: `{:0>2d}:{:0>2d}`".format(loc_time.tm_hour, loc_time.tm_min)
    embed.color = 15746887
    loop.create_task(dm(embed))

def server_down():
    loc_time = time.localtime()
    print("server may be down, sending msg")
    embed = discord.Embed()
    embed.title = "Server Down"
    embed.description = "You have been dropped from the server >5 times. 2b2t may be down.\nCurrent Time: `{:0>2d}:{:0>2d}`".format(loc_time.tm_hour, loc_time.tm_min)
    embed.color = 15746887
    loop.create_task(dm(embed))

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
    set_state(False)
    asyncio.set_event_loop(loop)
    connection_count = 0
    try:
        print("logging into discord")
        loop.create_task(client.login(token))
        print("connecting")
        loop.create_task(client.connect())
    except KeyboardInterrupt:
        loop.run_until_complete(client.logout())
    print("connected, now running program")
    it = (line for line in loglines)
    for index, line in enumerate(it):
        if "[main/INFO]: [CHAT] Position in queue:" in line:
            if index == 0: # print our first position
                connected(line, True, True)
            connection_count = 0
            connected(line, hour_passed(), False)
            print("{:0>2d}:{:0>2d}".format(time.localtime().tm_hour, time.localtime().tm_min))
        elif "Started saving saved containers in a new thread" in line:
            disconnected()
            set_state(True)
        elif "[main/INFO]: Connecting to 2b2t.org, 25565" in line:
            connection_count += 1
            print("can't connect", connection_count)
            if connection_count >= 5 and not get_state():
                server_down()
                set_state(True)
