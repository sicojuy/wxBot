#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import datetime

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
    TaskContent = 3
    TaskID = 4

class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.tasks = []
        self.task_adding = {}
        self.input_type = None

    def tasks_list(self):
        if len(self.tasks) == 0:
            return "当前没有定时任务"
        msg = ""
        i = 1
        for task in self.tasks:
            if len(msg) > 0:
                msg += "\n\n"
            msg += "%d. 发送时间：%s；接收人：%s；内容：%s" % (i, task['time'].strftime("%m-%d %H:%M"), task['user']['name'], task['content'])
            i += 1
        return msg

    def handle_text_msg(self, msg):
        if self.input_type == InputType.TaskTime:
            items = msg.split(None, 1)
            if items[0] in ['今日', '今天']:
                date = datetime.date.today()
            elif items[0] in ['明日', '明天']:
                date = datetime.date.today() + datetime.timedelta(days=1)
            elif items[0] in ['后日', '后天']:
                date = datetime.date.today() + datetime.timedelta(days=2)
            elif items[0] in ['大后日', '大后天']:
                date = datetime.date.today() + datetime.timedelta(days=3)
            else:
                try:
                    date = datetime.datetime.strptime(items[0], "%m-%d")
                except ValueError: 
                    return '日期格式不对，请重新输入'
            try:
                time = datetime.datetime.strptime(items[1], "%H:%M")
            except ValueError: 
                return '时间格式不对，请重新输入'
            self.task_adding['time'] = datetime.datetime.combine(date, time.time())
            self.input_type = InputType.TaskUser
            return task_user_help
        elif self.input_type == InputType.TaskUser:
            self.task_adding['user'] = {
                "name": msg,
                "id": 111
            }
            self.input_type = InputType.TaskContent
            return task_content_help
        elif self.input_type == InputType.TaskContent:
            self.task_adding['content'] = msg
            self.input_type = None
            result = "成功添加任务\n\n"
            result += "发送时间：%s\n" % self.task_adding['time'].strftime("%m-%d %H:%M")
            result += "接收人：%s\n" % self.task_adding['user']['name']
            result += "内容：%s" % self.task_adding['content']
            self.tasks.append(self.task_adding)
            self.task_adding = {}
            return result
        elif self.input_type == InputType.TaskID:
            try:
                i = int(msg)
            except ValueError:
                return '任务编号为数字，请重新输入'
            if i > len(self.tasks) or i <= 0:
                return '任务不存在，请重新输入任务编号'
            self.tasks = self.tasks[:i-1] + self.tasks[i:]   
            self.input_type = None
            result = '成功删除定时任务'
            return result
        else:
            print "invalid text type: %d" % self.input_type
            return '内部异常'

    def handle_self_msg(self, msg):
        print "handle self msg"
        ctype = msg['content']['type']
        cdata = msg['content']['data'].encode('utf-8').strip()
        uid = msg['user']['id']
        if ctype == 0:
            if cdata in ['帮助', 'help']:
                self.send_msg_by_uid(help_msg, uid)
            elif cdata in ['001', '查看定时任务']:
                result = self.tasks_list()
                self.send_msg_by_uid(result, uid)
            elif cdata in ['002', '添加定时任务']:
                self.input_type = InputType.TaskTime
                self.send_msg_by_uid(task_time_help, uid)
            elif cdata in ['003', '删除定时任务']:
                self.input_type = InputType.TaskID
                result = self.tasks_list()
                if len(self.tasks) > 0:
                    result += "\n\n请输入要删除的任务编号"
                self.send_msg_by_uid(result, uid)
            elif cdata in ['004', '查看群组']:
                print self.group_list
            elif cdata in ['005', '查看联系人']:
                print self.contact_list
            elif self.input_type != None:
                result = self.handle_text_msg(cdata)
                self.send_msg_by_uid(result, uid)
            else:
                print "pass msg: %s" % msg
        else:
            print "unknown msg content type id: %d" % msg['content']['type']

    def handle_group_msg(self, msg):
        print "pass group msg"

    def handle_contact_msg(self, msg):
        print "pass contact msg"

    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 1:
            self.handle_self_msg(msg)
        elif msg['msg_type_id'] == 3:
            self.handle_group_msg(msg)
        elif msg['msg_type_id'] == 4:
            self.handle_contact_msg(msg)
        else:
            print "pass msg type id: %d" % msg['msg_type_id']


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'tty'
    bot.run()


if __name__ == '__main__':
    main()

