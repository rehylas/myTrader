#encoding=utf-8


#coding=utf-8
import os
import urllib
import urllib2
import re
import cookielib
import json

'''
访问地址：

www.bangnikanzhe.com/DXBizGate/server?cmd=sendmsg4client

参数：

{'userid':'10011001','userpwd':'123456','txt':'002230 科大讯飞要涨了' }

'''

 
SM_URL = "http://www.bangnikanzhe.com/DXBizGate/server?cmd=sendmsg4client"


headers = {}
headers['Content-Type'] = 'application/json; charset=utf-8'
values =  {'userid':'80010121','userpwd':'888888','txt':'002230 科大讯飞要涨了' }


def data2jdata( values ):
    post_data = urllib.urlencode(values)
    j_data = json.dumps(values)
    return j_data
 
def jsonPost( jdata  ):
    res = ''
    try:
        req = urllib2.Request(SM_URL, jdata, headers)
        respone = urllib2.urlopen(req)
        #print 'respone:',respone
        res = respone.read()
        
        uRes =  res.decode('utf8').encode('gb2312') #gb2312 utf8
        print uRes        
        # print res
        respone.close()
    except Exception ,e :
        print 'except ??', e 
        print e.message
  
    return res


def stockMsgSend( data ):
    #jdata = data2jdata(data)
    #jsonPost( jdata )

    pass

#debug 
# data = {'userid':'80010121','userpwd':'888888','txt':'002230 科大讯飞要涨了 002415' }
# res = stockMsgSend( data )


