#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import datetime

task_help = '''通过以下命令来管理定时发送任务：
查看
添加
删除'''

task_time_help = '''请输入发送日期和时间（注意使用空格分隔日期跟时间），例如：
今天 07:30
明天 19:30
后天 12:12
08-08 20:20
10-10 07:07
'''

task_user_help = '''请输入接收人/群'''

task_content_help = '''请输入发送内容'''

del_task_help = '''请输入要删除的任务编号'''


class TextType:
    Normal = 0
    TaskTime = 1
    TaskUser = 2
    TaskContent = 3
    DelTask = 4

class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.sessions = {}
        self.tasks = []
        self.task_adding = {}
        self.text_type = 0

    def show_tasks(self):
        if len(self.tasks) == 0:
            return "当前没有定时发送任务"
        msg = ""
        i = 1
        for task in self.tasks:
            if len(msg) > 0:
                msg += "\n\n"
            msg += "%d. 发送时间：%s；接收人：%s；内容：%s" % (i, task['time'].strftime("%m-%d %H:%M"), task['user']['name'], task['content'])
            i += 1
        return msg

    def handle_text_msg(self, msg):
        if self.text_type == TextType.TaskTime:
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
            self.text_type = TextType.TaskUser
            return task_user_help
        elif self.text_type == TextType.TaskUser:
            self.task_adding['user'] = {
                "name": msg,
                "id": 111
            }
            self.text_type = TextType.TaskContent
            return task_content_help
        elif self.text_type == TextType.TaskContent:
            self.task_adding['content'] = msg
            self.text_type = TextType.Normal
            result = "成功添加任务\n\n"
            result += "发送时间：%s\n" % self.task_adding['time'].strftime("%m-%d %H:%M")
            result += "接收人：%s\n" % self.task_adding['user']['name']
            result += "内容：%s" % self.task_adding['content']
            self.tasks.append(self.task_adding)
            self.task_adding = {}
            return result
        elif self.text_type == TextType.DelTask:
            try:
                i = int(msg)
            except ValueError:
                return '任务编号为数字，可以输入"查看"获取任务编号'
            if i > len(self.tasks) or i <= 0:
                return '任务不存在，请重新输入任务编号'
            self.tasks = self.tasks[:i-1] + self.tasks[i:]   
            self.text_type = TextType.Normal
            result = '成功删除任务'
            return result
        else:
            print "invalid text type: %d" % self.text_type
            return '内部异常'

    def handle_self_msg(self, msg):
        print "handle self msg"
        ctype = msg['content']['type']
        cdata = msg['content']['data'].encode('utf-8')
        uid = msg['user']['id']
        if ctype == 0:
            if cdata == '帮助':
                self.send_msg_by_uid(task_help, uid)
            elif cdata == '查看':
                self.send_msg_by_uid(self.show_tasks(), uid)
            elif cdata == '添加':
                self.text_type = TextType.TaskTime
                self.send_msg_by_uid(task_time_help, uid)
            elif cdata == '删除':
                self.text_type = TextType.DelTask
                self.send_msg_by_uid(del_task_help, uid)
            elif self.text_type != TextType.Normal:
                result = self.handle_text_msg(cdata)
                self.send_msg_by_uid(result, uid)
            else:
                self.send_msg_by_uid('无法识别指令, ' + task_help, uid)
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
    bot.conf['qr'] = 'png'

    bot.run()


if __name__ == '__main__':
    main()

