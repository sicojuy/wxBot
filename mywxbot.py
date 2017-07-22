#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import threading
import datetime
import time
import json
import os

help_msg = '''支持以下命令：

001. 查看定时任务
002. 添加定时任务
003. 删除定时任务'''

task_time_help = '''请输入发送日期和时间（使用空格分隔日期跟时间），例如：
今天 07:30
明天 19:30
后天 12:12
08-08 20:20
10-10 07:07
'''

task_user_help = '''请输入接收人'''

task_content_help = '''请输入发送内容'''


class InputType:
    TaskTime = 1
    TaskUser = 2
    TaskUserID = 3
    TaskContent = 4
    TaskID = 5

class Tasker(threading.Thread):
    def __init__(self, wxbot):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.tasks = []
        self.wxbot = wxbot
        self.load_tasks()

    def load_tasks(self):
        if os.path.isfile("./tasks"):
            f = open("./tasks", "r")
            try:
                self.tasks = json.load(f)
            except:
                self.tasks = []
            f.close()
        else:
            self.tasks = []

    def save_tasks(self):
        f = open("./tasks", "w")
        json.dump(self.tasks, f)
        f.close()

    def add_task(self, task):
        self.lock.acquire()
        i = len(self.tasks) - 1
        self.tasks.append(None)
        while i >= 0:
            if self.tasks[i]['time']['timestamp'] > task['time']['timestamp']:
                self.tasks[i+1] = self.tasks[i]
                i -= 1
        self.tasks[i+1] = task
        self.save_tasks()
        self.lock.release()

    def del_task(self, pos):
        self.lock.acquire()
        if pos > len(self.tasks) or pos <= 0:
            self.lock.release()
            return -1
        self.tasks = self.tasks[:i-1] + self.tasks[i:]   
        self.save_tasks()
        self.lock.release()
        return 0

    def get_tasks(self):
        self.lock.acquire()
        if len(self.tasks) == 0:
            self.lock.release()
            return "当前没有定时任务"
        result = ""
        i = 1
        for task in self.tasks:
            msg += "%d. 发送时间：%s；接收人：%s；内容：%s\n" % (i, task['time']['format'], task['user']['name'].encode('utf-8'), task['content'].encode('utf-8'))
            i += 1
        self.lock.release()
        return msg[:-1]

    def stop(self):
        self.stop_event.set()

    def run(self):
        while(not self.stop_event.is_set()):
            print("tasker running")
            self.stop_event.wait(30)


class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.lock = threading.Lock()
        self.tasker = Tasker(self)
        self.tasker.start()
        self.task_adding = {}
        self.input_type = None
        self.user_search = []

    def run(self):
        WXBot.run(self)
        print("stop tasker")
        self.tasker.stop()
        print("wait tasker to exit")
        self.tasker.join()

    def find_users(self, name):
        name = name.lower()
        self.user_search = []
        for user in self.contact_list:
            if len(user['RemarkName']) > 0 and user['RemarkName'].lower().find(name) != -1:
                self.user_search.append({'UserName': user['UserName'], 'DisplayName': user['RemarkName']})
            elif len(user['RemarkPYQuanPin']) > 0 and user['RemarkPYQuanPin'].lower().find(name) != -1:
                self.user_search.append({'UserName': user['UserName'], 'DisplayName': user['RemarkName']})
            elif len(user['NickName']) > 0 and user['NickName'].lower().find(name) != -1:
                self.user_search.append({'UserName': user['UserName'], 'DisplayName': user['NickName']})
            elif len(user['PYQuanPin']) > 0 and user['PYQuanPin'].lower().find(name) != -1:
                self.user_search.append({'UserName': user['UserName'], 'DisplayName': user['NickName']})
        for group in self.group_list:
            if len(group['RemarkName']) > 0 and group['RemarkName'].lower().find(name) != -1:
                self.user_search.append({'UserName': group['UserName'], 'DisplayName': group['RemarkName']})
            elif len(group['RemarkPYQuanPin']) > 0 and group['RemarkPYQuanPin'].lower().find(name) != -1:
                self.user_search.append({'UserName': group['UserName'], 'DisplayName': group['RemarkName']})
            elif len(group['NickName']) > 0 and group['NickName'].lower().find(name) != -1:
                self.user_search.append({'UserName': group['UserName'], 'DisplayName': group['NickName']})
            elif len(group['PYQuanPin']) > 0 and group['PYQuanPin'].lower().find(name) != -1:
                self.user_search.append({'UserName': group['UserName'], 'DisplayName': group['NickName']})

    def handle_input_msg(self, msg):
        if self.input_type == InputType.TaskTime:
            items = msg.split(None, 1)
            if items[0] in [u'今日', u'今天']:
                date = datetime.date.today()
            elif items[0] in [u'明日', u'明天']:
                date = datetime.date.today() + datetime.timedelta(days=1)
            elif items[0] in [u'后日', u'后天']:
                date = datetime.date.today() + datetime.timedelta(days=2)
            elif items[0] in [u'大后日', u'大后天']:
                date = datetime.date.today() + datetime.timedelta(days=3)
            else:
                try:
                    date = datetime.datetime.strptime(items[0], "%m-%d")
                except ValueError: 
                    return '日期格式不对，请重新输入'
            try:
                dttime = datetime.datetime.strptime(items[1], "%H:%M")
            except ValueError: 
                return '时间格式不对，请重新输入'
            dt = datetime.datetime.combine(date, dttime.time())
            self.task_adding['time'] = {
                'format': dt.strftime("%m-%d %H:%M"),
                'timestamp': time.mktime(dt.timetuple())
            }
            self.input_type = InputType.TaskUser
            return task_user_help
        elif self.input_type == InputType.TaskUser:
            self.find_users(msg)
            if len(self.user_search) == 0:
                return '联系人不存在，请重新输入'
            elif len(self.user_search) == 1:
                self.task_adding['user'] = {
                    "name": self.user_search[0]['DisplayName'],
                    "id": self.user_search[0]['UserName']
                }
                self.input_type = InputType.TaskContent
                return task_content_help
            else:
                result = ""
                i = 1
                for user in self.user_search:
                    result += "%d. %s\n" % (i, user['DisplayName'].encode('utf-8'))
                    i += 1
                result += '\n请输入联系人编号选择联系人'
                self.input_type = InputType.TaskUserID
                return result
        elif self.input_type == InputType.TaskUserID:
            try:
                i = int(msg)
            except ValueError:
                return '联系人编号为数字，请重新输入'
            if i > len(self.user_search) or i <= 0:
                return '联系人编号不正确，请重新输入'
            self.task_adding['user'] = {
                "name": self.user_search[i-1]['DisplayName'],
                "id": self.user_search[i-1]['UserName']
            }
            self.input_type = InputType.TaskContent
            return task_content_help
        elif self.input_type == InputType.TaskContent:
            self.task_adding['content'] = msg
            self.input_type = None
            result = "成功添加任务\n\n"
            result += "发送时间：%s\n" % self.task_adding['time']['format']
            result += "接收人：%s\n" % self.task_adding['user']['name'].encode('utf-8')
            result += "内容：%s" % self.task_adding['content'].encode('utf-8')
            self.tasker.add_task(self.task_adding)
            self.task_adding = {}
            return result
        elif self.input_type == InputType.TaskID:
            try:
                i = int(msg)
            except ValueError:
                return '任务编号为数字，请重新输入'
            rt = self.tasker.del_task(i)
            if rt == 0:
                self.input_type = None
                return '成功删除定时任务'
            elif rt == -1:
                return '任务不存在，请重新输入任务编号'

    def send_msg_by_uid(self, msg, uid):
        self.lock.acquire()
        WXBot.send_msg_by_uid(self, msg, uid)
        self.lock.release()

    def handle_msg(self, msg):
        print("handle self msg")
        ctype = msg['content']['type']
        cdata = msg['content']['data'].strip()
        uid = msg['user']['id']
        if ctype == 0:
            if cdata in [u'帮助', 'help']:
                self.send_msg_by_uid(help_msg, uid)
            elif cdata in ['001', u'查看定时任务']:
                result = self.tasker.get_tasks()
                self.send_msg_by_uid(result, uid)
            elif cdata in ['002', u'添加定时任务']:
                self.input_type = InputType.TaskTime
                self.send_msg_by_uid(task_time_help, uid)
            elif cdata in ['003', u'删除定时任务']:
                self.input_type = InputType.TaskID
                result = self.tasker.get_tasks()
                if result[0] == '1':
                    result += "\n\n请输入要删除的任务编号"
                self.send_msg_by_uid(result, uid)
            elif cdata in [u'查看群组']:
                print(self.group_list)
            elif cdata in [u'查看联系人']:
                print(self.contact_list)
            elif self.input_type != None:
                result = self.handle_input_msg(cdata)
                self.send_msg_by_uid(result, uid)

    def handle_self_msg(self, msg):
        print("handle self msg")
        self.handle_msg(msg)

    def handle_group_msg(self, msg):
        print("pass group msg")

    def handle_contact_msg(self, msg):
        print("pass contact msg")

    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 1:
            self.handle_self_msg(msg)
        elif msg['msg_type_id'] == 3:
            self.handle_group_msg(msg)
        elif msg['msg_type_id'] == 4:
            self.handle_contact_msg(msg)


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'tty'
    bot.run()


if __name__ == '__main__':
    main()

