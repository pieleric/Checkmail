#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This script check the mail in an imap folder and turn on the led if new mail
is found. This done every 30s. The information about the imap folder are
contained in a file ~/.checkmailrc as three tab separated fields: the server
name, the user name and the password rot13.

"""

import imaplib
import time
import os
import re
import socket
import csv
import subprocess
import sys

INTERVAL = 30

# Contains the path to the led for the mails
mailLed = ""
def find_mail_led():
    """Initialize the mail led to the best possible found"""
    global mailLed
    mailLed = ""
    # Find a directory matching ".*:.*:.*mail.*" in /sys/class/leds/
    try:
        names = os.listdir("/sys/class/leds/")
    except os.error:
        return

    for name in names:
        if re.match(".*:.*:.*mail.*", name):
            mailLed = "/sys/class/leds/" + name
            return


def set_mail_led(status):
    """change the status of the mail led
    # False => off
    # True => on
    # if mailLed is empty, it uses the keyboard scroll-lock
    
    """
    # if no special led, use the scrolllock led
    if mailLed == "":
        if status:
            subprocess.Popen(["xset", "led", "3"])
        else:
            subprocess.Popen(["xset", "-led", "3"])
    else:
        if status:
            bright = "255"
        else:
            bright = "0"
        brightness_file = open(mailLed + "/brightness", "w")
        brightness_file.write(bright)
        brightness_file.close()

def check_mail():
    """Check for new mail, endlessly until a network error arises"""
    try:
        M = imaplib.IMAP4(serverName)
        M.login(loginName, loginPwd)
        M.select(readonly=1)

        prevNotSeen = ''
        while True:
            #Find only non read email
            type, data = M.search(None, '(NOT SEEN)')

            # Everything read => force to off
            if data[0] == '':
                set_mail_led(False)
            else:
                # only turn on the led if there is unseen mail different from before
                newMail = False
                for num in data[0].split():
                    if num not in prevNotSeen:
                        #print num, " and ", prevNotSeen
                        newMail = True
                        break
                if newMail:
                    set_mail_led(True)
                #print data
            prevNotSeen = data[0]
            time.sleep(INTERVAL)

    except (imaplib.IMAP4.error, socket.error), err:
        print "connection failure %s\n" % (err)
    except  (KeyboardInterrupt, SystemExit), e: # mainly to handle KILL signals
        M.close()
        M.logout()
        sys.exit(1)


if __name__ == "__main__":
    # initialises
    find_mail_led()
    reader = csv.reader(open(os.path.expanduser("~/.checkmailrc"), "rb"),
                delimiter="\t",
                quoting=csv.QUOTE_NONE)
    try:
        row = reader.next()
        serverName = row[0]
        loginName = row[1]
        loginPwd = row[2].decode("rot13")
    except Exception, e:
        print "Couldn't read configuration file: %s\n" % (e)
        sys.exit(1)

    while True:
        check_mail()
        time.sleep(2 * 60)

# vim:shiftwidth=4:expandtab:spelllang=en_gb:spell: 
