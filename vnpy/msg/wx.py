
# -*- coding: utf-8 -*-  
import itchat
 

def sendwx( ):
    print 'itchat.login '
    itchat.login()
 
    # friends = itchat.get_friends()
   
    friends = itchat.get_friends() #.search(name = u'杭漂漂')
    friend = itchat.search_friends(u'hylas-张')
    # print type(friends)
    # print len(friend)
    if( len(friend) >= 1):
        msgReceiver = friend[0]
        return msgReceiver
    else:
        print 'sendwx  get friend error!'
        return None
    pass


def test():
    msgReceiver = sendwx()
    msgReceiver.send(u'aa')

#test()

'''
itchat.login()
itchat.send(u'你好', 'filehelper')
# friends = itchat.get_friends()
# print friends
friends = itchat.get_friends() #.search(name = u'杭漂漂')
friend = itchat.search_friends(u'杭漂漂')
print type(friends)
print len(friend)
rec = friend[0]
print rec
rec.send(u'微信信息发送测试')


'''

