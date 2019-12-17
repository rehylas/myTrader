# encoding: UTF-8

# 重载sys模块，设置默认字符串编码方式为utf8
try:
    reload         # Python 2
except NameError:  # Python 3
    from importlib import reload

import sys
from sys import argv
reload(sys)
import time 

try:
    sys.setdefaultencoding('utf8')
except AttributeError:
    pass

# 判断操作系统
import platform
system = platform.system()

if (system == "Linux"): 
    MYLIB_PATH = '/home/hylas/opt/mylib/python/'
    WORK_PATH = '/home/hylas/opt/ido'
else:     
    MYLIB_PATH = 'E:/work/mylib/python/' 
    WORK_PATH = '.'

sys.path.append( MYLIB_PATH )
#sys.path.append( MYLIB_PATH +'future')

# mylib 
from  base import *
 
# vn.trader模块 t
sys.path.append('..')
sys.path.append('../..')
from six import text_type
from vnpy.event import EventEngine
from vnpy.event import EventEngine2
from vnpy.trader.vtEngine import MainEngine

from vnpy.trader.vtObject import VtSubscribeReq 

# 加载底层接口
from vnpy.trader.gateway import (ctpGateway   )

 
# 加载上层应用
# from vnpy.trader.app import (riskManager, ctaStrategy, 
#                              spreadTrading, algoTrading,signalMonitor)

from vnpy.trader.app import ( execServer )

#----------------------------------------------------------------------
def main( argv ):
    """主程序入口"""
    # futureTime = getFutureTime()
    # if( futureTime['isWeek67'] ):
    #     return 

    sendwxmsg(argv[0] + ' 启动')
     
 
    # 创建事件引擎
    ee = EventEngine2()

    # 创建主引擎
    me = MainEngine(ee)

    # 添加交易接口
    me.addGateway(ctpGateway)
    #me.addGateway(ibGateway)

    if system == 'Windows':
        pass
        # me.addGateway(femasGateway)
        # me.addGateway(xspeedGateway)
        # me.addGateway(secGateway)
 
    # 添加上层应用
    #me.addApp(signalMonitor)
    me.addApp( execServer )  
 

    #启动后自动连接CTP， 同时也连接了数据库
    me.connect("CTP")

    #订阅观察的品种，测试性能
    #subFutures()

    # time.sleep(3)
    # req = VtSubscribeReq()
    # req.symbol = 'ru1909'
    # req.exchange = u'' # 'SHFE' 
    # print 'market subscribe ------------------>'
    # print req.__dict__
    # me.subscribe(req, 'CTP' )  

    #订阅所有期货品种
    nCount = 10
    time.sleep(5)
    contracts = me.getAllContracts()  
    for connect in contracts :
        #print connect.__dict__.['symbol']
        req = VtSubscribeReq()
        req.symbol = connect.__dict__['symbol']
        req.exchange = u'' # 'SHFE' 
        # print 'market subscribe ------------------>'
        # print req.__dict__
        me.subscribe(req, 'CTP' )  
        nCount = nCount -1 
        if(nCount<=0):
            break        

    # 订阅 ru1909
    req = VtSubscribeReq()
    req.symbol = 'ru1909'
    req.exchange = u'' # 'SHFE' 
    me.subscribe(req, 'CTP' )  

    # 在主线程中启动 事件循环
    sys.exit( doWhile( me ) )
    

def doWhile( mainEngine ):
    count  = 3600*10   #12 小时
    while(True):
        time.sleep(1)
        if( count <= 0 ):
            break
        count = count -1    

        timeStr = getTime()
        hour =  timeStr[0:2]
        if(hour =='16' or hour =='02' ):
            print 'exit by time ', hour
            sendwxmsg( 'execFOrder.py exit by time ')
            break 

    pass
    mainEngine.exit()
    print 'do while over'


if __name__ == '__main__':
    main( argv )


