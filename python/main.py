import time, os
from twilio.rest import Client
from enum import Enum

class PhoneAccount:
    account_sid = ''
    auth_token = ''
    my_num = ''
    from_num = ''
    def __init__(self, s, t, m, f):
        self.account_sid = s
        self.auth_token = t
        self.my_num = m
        self.from_num = f

main_account = PhoneAccount("ACe0b4e6e6eecbe2fa0bc6db20a50626d7", "8569904a2f34497f5bc4dbc3e6a6c64f", "+12026312387", "+12055832157")
backup_account = PhoneAccount("ACaf1eff65f8caaa4759681d91b2ac6f5c", "ec8f7df43b9ff4b5dcfdf9125f39a1a4", "+2026312387", "+12055288797") # johnfortniteismydad@gmail.com:johnfortniteismydad
client = Client(main_account.account_sid, main_account.auth_token)
global reconnecting, start_time

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

def connected(cur_line, increased):
    print(cur_line)
    index = cur_line.find("e:")
    current_pos = int(cur_line[3+index:]) # our current position in queue
    print(current_pos)
    print(get_state())
    loc_time = time.localtime()
    if increased:
        print("Increased! sending msg")
        client.messages.create(
            to=main_account.my_num,
            from_=main_account.from_num,
            body="\nStill in 2b2t queue as of {}:{}!\nCurrent Position: {}".format(loc_time.tm_hour, loc_time.tm_min, current_pos)
        )
    elif get_state():
        client.messages.create(
            to=main_account.my_num,
            from_=main_account.from_num,
            body="\nReconnected to 2b2t queue as of {}:{}!\nCurrent Position: {}".format(loc_time.tm_hour, loc_time.tm_min, current_pos)
        )
        set_state(False)
    elif current_pos == 1:
        print("about to join server!")
        client.messages.create(
            to=main_account.my_num,
            from_=main_account.from_num,
            body="\nYou are first in 2b2t queue as of {}:{}!\nCome to the computer now!".format(loc_time.tm_hour, loc_time.tm_min)
        )

def disconnected():
    loc_time = time.localtime()
    print("disconnected from 2b2t, sending msg")
    print("\nDisconnected from 2b2t as of {}:{}! Attempting to reconnect.".format(loc_time.tm_hour, loc_time.tm_min))
    client.messages.create(
        to=main_account.my_num,
        from_=main_account.from_num,
        body="\nDisconnected from 2b2t as of {}:{}! Attempting to reconnect.".format(loc_time.tm_hour, loc_time.tm_min)
    )

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
    global start_time
    start_time = time.time()
    set_state(False)
    for line in loglines:
        if "[main/INFO]: [CHAT] Position in queue:" in line:
            connected(line, hour_passed())
            print("{}:{}".format(time.localtime().tm_hour, time.localtime().tm_min))
        elif "Started saving saved containers in a new thread" in line:
            disconnected()
            set_state(True)
