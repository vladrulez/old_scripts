#!/usr/bin/env python
# vim: set filetype=python ts=4 sw=4 et si
# -*- coding: utf-8 -*-
# Author: Vladimir Blokhin
###########################

import sys,re,MySQLdb,roundup.instance

def check_start_settings ():
    tracker_path = "/var/lib/roundup/trackers/default"
    mysql_db_host = "localhost"
    mysql_db_name = "glpi"
    mysql_db_user = "glpi_user"
    mysql_db_pwd = "PASSWORD"
    users_map_file = "/home/vlad/Downloads/users_map_file.txt"
    if not tracker_path or not mysql_db_host or not mysql_db_name or not mysql_db_user or not mysql_db_pwd:
        if len(sys.argv) < 5:
            print "\nMissing parameters, exiting ...\n"
            print "\nUsage: "+sys.argv[0]+" \"path to roundup tracker\" \"MySQL server hostname/IP\" \"GLPI MySQL database name\" \"GLPI MySQL db username\" [GLPI MySQL user password] \n"
            sys.exit(1)
        else:
            tracker_path = sys.argv[1]
            mysql_db_host = sys.argv[2]
            mysql_db_name = sys.argv[3]
            mysql_db_user = sys.argv[4]
            try:
                mysql_db_pwd = sys.argv[5]
            except IndexError:
                mysql_db_pwd = raw_input("Enter your GLPI database user password: ")
    return (tracker_path,mysql_db_host,mysql_db_name,mysql_db_user,mysql_db_pwd,users_map_file)

def sql_insert(sql_query):
    cur = mysql_db.cursor()
    try:
        cur.execute(sql_query)
    except:
        mysql_db.rollback()
        raise
    else:
        mysql_db.commit()
    cur.close()

def sql_select(sql_query):
    global row
    cur = mysql_db.cursor()
    try:
        cur.execute(sql_query)
    except:
        row = []
        raise
    else:
        row = cur.fetchone()
        return row
    cur.close()

def sql_update(sql_query):
    cur = mysql_db.cursor()
    try:
        cur.execute(sql_query)
    except:
        raise
    else:
        mysql_db.commit()
    cur.close()

def copy_user (userid,*is_active):
    global user
    global users_hash
    global row
    global users_reverse_hash
    if not is_active:
        if sq.user.is_retired(userid):
            is_active = '0'
        else:
            is_active = '1'
    else:
        is_active = '1'
    # getting next ID from MySQL
    row = sql_select("SELECT MAX(id)+1 FROM glpi_users;")
    userid_mysql = row[0]
    insert_user = "INSERT INTO `glpi_users` (`id`, `name`,`password`,`realname`,`firstname`,`authtype`,`mobile`,`is_active`,`usercategories_id`,`phone`,`comment`,`phone2`,`registration_number`,`usertitles_id`,`locations_id`,`is_deleted`,`entities_id`,`profiles_id`,`date_mod`) VALUES ('%s','%s','','%s','','1','%s','%s','0','','','','','0','0','0','0','0',now())" % (str(userid_mysql),user['username'],user['realname'],user['phone'],str(is_active))
    try:
        sql_insert(insert_user)
        users_hash[userid] = userid_mysql
        if user['address'] :
            sql_insert("INSERT INTO `glpi_useremails` (`email`,`users_id`,`is_default`) VALUES ('%s','%s','1')" % (user['address'],str(users_hash[userid])))
        if len(user['alternate_addresses']) > 0:
            for i in range(0,len(user['alternate_addresses'])):
                print "UserID = %s alternate email= %s" % (str(users_hash[userid]),user['alternate_addresses'][i])
                sql_insert("INSERT INTO `glpi_useremails` (`email`,`users_id`,`is_default`) VALUES ('%s','%s','0')" % (user['alternate_addresses'][i],str(users_hash[userid])))
        if 'Admin' in user['roles']:
            profile_id = '3'
        else:
            profile_id = '2'
        sql_insert("INSERT INTO `glpi_profiles_users` (`entities_id`,`profiles_id`,`users_id`,`is_recursive`,`is_dynamic`) VALUES (0,'%s','%s',0,'1')" % (profile_id,str(users_hash[userid])))
        users_reverse_hash[user['username']] = userid
    except:
        print "Couldn't create a user in MySQL DB with userid %s \n" % str(userid)
        print insert_user
        # adding 2013 to a username and try again
        user['username'] = str(user['username'])+"_20132013"
        print "retrying ... \n"
        copy_user(userid,'1')
    else:
        print "Roundup userID %s Created user ID is %s" % (userid,str(userid_mysql))

def check_user (userid):
    global user
    global users_hash
    global copyattribs
    global row
    global users_reverse_hash
    # Checking if we got a user in our users_hash{} dictionary already
    # this should mean that we have copied a user record to user{}
    try:
        value = users_hash[userid]
    except KeyError:
        # loading user records from sqlite DB to user{} dictionary
        user = {'username':'', 'address':'', 'realname':'', 'phone':'', 'roles':'', 'alternate_addresses':[]}
        for attrib in copyattribs:
            value = sq.user.get(userid, attrib)
            if value:
                user[attrib] = re.sub(r"'", "\\'", str(value))
            else :
                user[attrib] = ""
        if user['alternate_addresses']:
            user['alternate_addresses'] = user['alternate_addresses'].split("\n")
        else:
            user['alternate_addresses'] = []
        users_reverse_hash[user['username']] = userid

        #print "user username = %s email = %s  alternate = %s" % (user['username'],user['address'],user['alternate_addresses'])
        # checking if a user has been added to MySQL DB already
        # also checks for a username with added "_20132013" string

        select_user = "SELECT `glpi_users`.`id` FROM `glpi_users` INNER JOIN `glpi_useremails` ON (`glpi_users`.`id`=`glpi_useremails`.`users_id` AND (`glpi_users`.`name`='%s' OR `glpi_users`.`name`='%s' ) AND `realname`='%s' AND `glpi_users`.`mobile`='%s' AND `glpi_useremails`.`email`='%s' AND `glpi_useremails`.`is_default`='1')" % (user['username'],user['username']+"_20132013",user['realname'],user['phone'],user['address'])
        try:
            row = sql_select(select_user)
        except:
            print "mysql fail with "+select_user
        if row and len(row) == 1:
                # we have found a user in MySQL DB
                users_hash[userid] = int(row[0])
        else:
            copy_user(userid)

def copy_msg (msgid, issueid):
    global issue
    global issues_hash
    global users_hash
    global msg
    global msgs_hash
    global row

    users_id = users_hash[msg['author']]
    tickets_id = issues_hash[issueid]
    date = re.sub(r"\.", " ", str(msg['date']))
    try:
        sql_insert("INSERT INTO `glpi_ticketfollowups` (`content`,`tickets_id`,`requesttypes_id`,`is_private`,`users_id`,`date`) VALUES ('%s','%s','1','0','%s','%s' )" % (msg['content'], tickets_id, users_id, date))
    except:
        print "Couldn't insert message with %s ID" % msgid

    msgs_hash[msgid] = msgid
    sql_update("UPDATE `glpi_tickets` SET `date_mod` = '%s', `users_id_lastupdater` = '%s' WHERE `id`= '%s'" % (date, users_id, tickets_id))

def check_msg (msgid,issueid):
    global issues_hash
    global users_hash
    global msg
    global msgs_hash
    global msg_attribs
    global row

    try:
        value = msgs_hash[msgid]
    except KeyError:
        msg = {'author':'', 'content':'', 'date':'', 'inreplyto':'', 'recipients':''}
        for msg_attrib in msg_attribs:
            value = sq.msg.get(msgid,msg_attrib)
            if value:
                msg[msg_attrib] = value
            else:
                msg[msg_attrib] = ""
        msg['content'] = re.sub(r"'", "\\'", str(msg['content'])).decode("utf-8")
        try:
            value = msg['author']
            value = users_hash[msg['author']]
        except KeyError:
            check_user(msg['author'])
        select_msg = "SELECT `id` FROM `glpi_ticketfollowups` WHERE (`content`='%s' and `tickets_id`='%s' and `users_id`='%s')" % (msg['content'], issues_hash[issueid], users_hash[msg['author']])
        row = sql_select(select_msg)

        if row:
            if len(row) == 1:
                msgs_hash[msgid] = int(row[0])
        else:
            copy_msg(msgid,issueid)

def copy_issue (issueid):
    global user
    global issue
    global users_hash
    global issues_hash
    global issue_attribs
    global row
    ticket_status = {1:'new', 2:'new', 3:'assign', 4:'plan', 5:'assign', 6:'waiting', 7:'solved', 8:'closed'}
    ticket_priority = {1:'5', 2:'4', 3:'3', 4:'2', 5:'1'}

    status = str(ticket_status[int(issue['status'])])
    priority = str(ticket_priority[int(issue['priority'])])
    title = issue['title'].decode("utf-8")

    if issue['content']:
        content = issue['content'].decode("utf-8")
        msgs_hash[issue['messages'][0]] = issue['messages'][0]
    else:
        content = ''

    if issue['creator']:
        creator = str(users_hash[issue['creator']])
    else:
        creator = '0'

    if issue['date']:
        date = re.sub(r"\.", " ", str(issue['date']))
    else:
        date = 'now()'

    insert_issue = "INSERT INTO `glpi_tickets` (`id`,`date`,`due_date`,`slas_id`,`type`,`itilcategories_id`,`entities_id`,`suppliers_id_assign`,`status`,`requesttypes_id`,`urgency`,`impact`,`itemtype`,`priority`,`actiontime`,`name`,`content`,`users_id_lastupdater`,`users_id_recipient`,`global_validation`,`items_id`,`date_mod`) VALUES ('%s','%s',NULL,'0','2','0','0','0','%s','2','%s','%s','','%s','0','%s','%s','%s','%s','none',0,'%s')" % (str(issueid),date,status,priority,priority,priority,title,content,creator,creator,date)

    try:
        sql_insert(insert_issue)
    except:
        print "Couldn't create an issue in MySQL DB with issueid "+str(issueid)+"\n"
        print insert_issue
        pass

    issues_hash[issueid] = issueid

    ticket_users = []
    ticket_users_role = {}
    if issue['assignedto']:
        if issue['assignedto'] not in ticket_users:
            ticket_users.append(issue['assignedto'])
        ticket_users_role[issue['assignedto']] = 2
    if issue['creator']:
        if issue['creator'] not in ticket_users:
            ticket_users.append(issue['creator'])
        ticket_users_role[issue['creator']] = 1
    if len(issue['nosy']) > 0:
        for userid in issue['nosy']:
            if userid not in ticket_users:
                ticket_users.append(userid)
            try:
                value = ticket_users_role[userid]
            except KeyError:
                ticket_users_role[userid] = 3

    for userid in ticket_users:
        insert_issue_users = "INSERT INTO `glpi_tickets_users` (`tickets_id`,`users_id`,`type`) VALUES ('%s','%s','%s')" % (str(issues_hash[issueid]), str(users_hash[userid]), str(ticket_users_role[userid]))
        try:
            sql_insert(insert_issue_users)
        except:
            print "Couldn't create an issue_users in MySQL DB tickets_id %s \n" % str(issues_hash[issueid])
            print "SQL query - %s" % insert_issue_users

    print "issue with %s ID has been copied" % issueid

def check_issue (issueid):
    global user
    global issue
    global users_hash
    global issues_hash
    global issue_attribs
    global row

    try:
        value = issues_hash[issueid]
    except KeyError:
        issue = {'assignedto':'', 'title':'', 'messages':'', 'nosy':'', 'priority':'', 'status':'', 'creator':'', 'content':'', 'date':''}
        for issue_attrib in issue_attribs:
            value = sq.issue.get(issueid,issue_attrib)
            if value:
                issue[issue_attrib] = value
            else:
                issue[issue_attrib] = ""
        issue['title'] = re.sub(r"'", "\\'", str(issue['title']))

        if len(issue['messages']) > 0:
            issue['creator'] = sq.msg.get(issue['messages'][0],'author')
            issue['content'] = sq.msg.get(issue['messages'][0],'content')
            issue['content'] = re.sub(r"'", "\\'", str(issue['content']))
            issue['date'] = sq.msg.get(issue['messages'][0],'date')

        if issue['assignedto']:
            check_user(issue['assignedto'])
        if issue['creator']:
            check_user(issue['creator'])
        if len(issue['nosy']) > 0:
            for userid in issue['nosy']:
                check_user(userid)

        select_issue = "SELECT `id` FROM `glpi_tickets` WHERE `id`='%s'" % str(issueid)
        row = sql_select(select_issue)

        if row:
            if len(row) == 1 and int(row[0]) == int(issueid):
                issues_hash[issueid] = int(issueid)
                if len(issue['messages']) > 0:
                    msgs_hash[issue['messages'][0]] = issue['messages'][0]
                if len(issue['messages']) > 1:
                    for i in range(1,len(issue['messages'])):
                        check_msg(issue['messages'][i], issueid)
            else:
                print "Fuckup again! row[0] = %s and issueid = %s" % (str(row[0]), str(issueid))
            # we have found a issue in MySQL DB
        else:
            copy_issue(issueid)
            if len(issue['messages']) > 1:
                #print "messages:"
                for i in range(1,len(issue['messages'])):
                    check_msg(issue['messages'][i], issueid)

def copy_missed_messages (missed_messages):
    global row
    row = []
    date = "2013-02-14 09:00:00"
    status = 'closed'
    priority = '1'
    title = "Missed messages are here"
    content = "This ticket contains missed messages from removed roundup tickets, DB errors, etc"
    creator = '3'
    insert_issue = "INSERT INTO `glpi_tickets` (`date`,`due_date`,`slas_id`,`type`,`itilcategories_id`,`entities_id`,`suppliers_id_assign`,`status`,`requesttypes_id`,`urgency`,`impact`,`itemtype`,`priority`,`actiontime`,`name`,`content`,`users_id_lastupdater`,`users_id_recipient`,`global_validation`,`items_id`,`date_mod`) VALUES ('%s',NULL,'0','2','0','0','0','%s','2','%s','%s','','%s','0','%s','%s','%s','%s','none',0,'%s')" % (date,status,priority,priority,priority,title,content,creator,creator,date)
    select_issue = "SELECT `id` FROM `glpi_tickets` WHERE `date`='2013-02-14 09:00:00' AND `users_id_recipient`='3' AND `name`='Missed messages are here'"

    row = sql_select(select_issue)
    if not row or len(row) < 1:
        try:
            sql_insert(insert_issue)
        except:
            print "Failed to create a ticket for missed messages"
            print insert_issue
    try:
        row = sql_select(select_issue)
    except:
        print "Couldn't find created ticket ID for ticket with missed messages"
        print select_issue
    else:
        issueid = row[0]
        issues_hash[issueid] = issueid
        print "Ticket with missed messages has been created or is already exist with %s ID" % str(issueid)
        if len(missed_messages) > 0:
            for msgid in missed_messages:
                check_msg(msgid,issueid)

def users_map_check (users_map_file):
    global users_reverse_hash
    global row
    global user
    global users_hash
    good_users = []
    if users_map_file:
        f = open(users_map_file,'r+')
    else:
        pass
    i = 20000
    for line in f:
        login,firstname,secondname = line.split(" ")
        try:
            userid = users_reverse_hash[login]
            userid_mysql = users_hash[userid]
        except KeyError:
            userid = i
            print "Login = %s name = %s %s" % (login,firstname,secondname)
            user = {}
            user['username'] = login
            user['address'] = login+"@cupid.com"
            user['realname'] = firstname+" "+secondname
            user['phone'] = ""
            user['roles'] = "User"
            user['alternate_addresses'] = []
            copy_user(str(userid),'1')
            i = i + 1
        good_users.append(str(userid))
        sql_update("UPDATE `glpi_users` SET `realname`='%s', `firstname`='%s', `is_active`='1' WHERE `id`='%s'" % (secondname,firstname,str(users_hash[str(userid)])) )
        row = []
        row = sql_select("SELECT `id` FROM `glpi_useremails` WHERE `users_id`='%s' AND `email`='%s' AND `is_default`='1'" % (str(users_hash[str(userid)]),login+"@cupid.com") )
        if row:
            if len(row) < 1:
                sql_insert("INSERT INTO `glpi_useremails` (`email`,`users_id`,`is_default`) VALUES ('%s','%s','1')" % (login+"@cupid.com",str(users_hash[str(userid)])))
    for userid in users_hash.keys():
        if userid not in good_users:
            sql_update("UPDATE `glpi_users` SET `is_active`='0' WHERE `id`='%s'" % (users_hash[str(userid)]) )


if __name__ == "__main__":
    (tracker_path,mysql_db_host,mysql_db_name,mysql_db_user,mysql_db_pwd,users_map_file) = check_start_settings()
    try:
        mysql_db = MySQLdb.connect(host=mysql_db_host,
                                    user=mysql_db_user,
                                    passwd=mysql_db_pwd,
                                    db=mysql_db_name,
                                    charset='utf8')
        print "Opened MySQL database"
    except:
        print "Can't open MySQL database"
        sys.exit(1)
    try:
        instance1 = roundup.instance.open(tracker_path)
        print "Opened source instance: %s" % tracker_path
    except:
        print "Can't open source instance: %s" % tracker_path
        sys.exit(1)

    sq = instance1.open('admin')

    # global lists and dictionaries for proper functions work
    row = []
    users_hash = {}
    users_reverse_hash = {}
    copyattribs = ['username', 'address', 'realname', 'phone', 'roles', 'alternate_addresses']
    user = {'username':'', 'address':'', 'realname':'', 'phone':'', 'roles':'', 'alternate_addresses':[]}
    issues_hash = {}
    issue_attribs = ['assignedto', 'title', 'messages', 'nosy', 'priority', 'status']
    issue = {'assignedto':'', 'title':'', 'messages':'', 'nosy':'', 'priority':'', 'status':'', 'creator':'', 'content':'', 'date':''}
    msgs_hash = {}
    msg_attribs = ['author', 'content', 'date', 'recipients']
    msg = {'author':'', 'content':'', 'date':'', 'recipients':''}

    # coping tickets (issues in roundup) and all releated users and messages

    issuelist = map(int, sq.issue.list())
    issuelist = sorted(issuelist, reverse=True)
    issuelist = map(str, issuelist)

    #issuelist = ['113', '114', '115', '121', '510','5840', '5841', '5842', '5843', '5844', '5845', '5846']
    print "Tickets list length is %s" % str(len(issuelist))
    print "copy_tickets started"
    for issueid in issuelist:
        check_issue(issueid)
    print "copy_tickets completed"

    # checking are any users not copied and copy them
    users = sq.user.list()
    print "Users list length is %s" % str(len(users))
    for userid in users:
        check_user(userid)

    # checking are any messages not copied and copy them
    missed_messages = []
    messages = sq.msg.list()
    print "Messages list length is %s" % str(len(messages))
    for messageid in messages:
        try:
            value = msgs_hash[messageid]
        except KeyError:
            missed_messages.append(messageid)
    copy_missed_messages(missed_messages)

    users_map_check(users_map_file)

    try:
        sq.close()
        mysql_db.close ()
        print "Databases closed."
    except:
        print "Couldn't close the databases"
