#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
import smtplib
import sys
from email.mime.text import MIMEText
from email.header import Header
 

''' 

接收服务器地址为：pop.sina.com或pop3.sina.com，
发送服务器地址为：smtp.sina.com

'''
# 第三方 SMTP 服务
mail_host="smtp.sina.com"  #设置服务器
mail_user="mytradermsg"    #用户名
mail_pass="zhang123"   #口令 

sender = 'mytradermsg@sina.com'
receivers = ['284851828@qq.com','mytradermsg@sina.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
 
def sendmail( subject , Text ): 
 
    message = MIMEText( Text , 'plain', 'utf-8')
    message['To'] =  Header('284851828@qq.com', 'utf-8')
    message['From'] = Header( sender )
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP() 
   
        smtpObj.connect(mail_host, 25 )    # 25 为 SMTP 端口号
        smtpObj.login(mail_user,mail_pass)  
        smtpObj.sendmail(sender, receivers, message.as_string())
        print "send mail ok"
    except smtplib.SMTPException,e:
        print "Error: send error ",e
 
if __name__ == "__main__":
    pass
    if( len(sys.argv) != 2 ):
        exit()
    if(  sys.argv[1] != 'test'  ):
        exit()        
 
    sendmail(u'标题sdf', u'内容sdf' )

