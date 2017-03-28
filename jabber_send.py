#!/usr/bin/env python
# vim: set filetype=python ts=4 sw=4 et si
# -*- coding: utf-8 -*-
# Author: Vladimir Blokhin
###########################

import xmpp,sys

def send_message(xmpp_jid,xmpp_pwd,room_jid,payload):
    jid = xmpp.protocol.JID(xmpp_jid)
    room_presense = room_jid + '/' + xmpp_jid.split('@')[0]

    #client = xmpp.Client(jid.getDomain())
    # without debug
    client = xmpp.Client(jid.getDomain(), debug=[])
    client.connect()
    client.auth(jid.getNode(),str(xmpp_pwd),resource='xmpppy')
    NS_MUC = 'http://jabber.org/protocol/muc'
    presence = xmpp.Presence(to=room_presense)
    presence.setTag('x', namespace=NS_MUC).setTagData('password', '')
    client.send(presence)
    client.send(xmpp.Message(room_jid,payload,typ='groupchat'))
    client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 4 :
        print "\nMissing parameters, exiting..."
        print "Usage: "+sys.argv[0]+" Groupchat Subject Message\n"
        sys.exit(1)

    xmpp_jid = 'USERNAME@DOMAIN.COM'
    xmpp_pwd = 'PASSWORD'

    room_jid   = sys.argv[1]
    subj = sys.argv[2]
    msg  = sys.argv[3]
    payload = subj + '\n' + msg

    send_message(xmpp_jid,xmpp_pwd,room_jid,payload)