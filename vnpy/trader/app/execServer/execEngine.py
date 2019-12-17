# encoding: UTF-8

'''
本文件中实现了行情数据记录引擎，用于汇总TICK数据，并生成K线插入数据库。

使用DR_setting.json来配置需要收集的合约，以及主力合约代码。
'''

import json
import csv
import os,sys
from string import digits
import copy
from string import digits
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta, time
from Queue import Queue, Empty
from threading import Thread
from pymongo.errors import DuplicateKeyError

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

from six import text_type
from vnpy.event import Event
from vnpy.trader.vtEvent import *
from vnpy.trader.vtFunction import todayDate, getJsonPath
from vnpy.trader.vtObject import VtSubscribeReq, VtLogData, VtBarData, VtTickData,VtOrderReq, VtCancelOrderReq

 

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
sys.path.append( MYLIB_PATH + 'future' )

# mylib 
from  other import *

#from .drBase import *
from .language import text

#本应用只支持CTP  

########################################################################
class ExecOrderEngine(object):
    """数据记录引擎"""
    
    settingFileName = 'Exec_setting.json'
    settingFilePath = getJsonPath(settingFileName, __file__)  

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # 当前日期
        self.today = todayDate()
        
        # # 主力合约代码映射字典，key为具体的合约代码（如IF1604），value为主力合约代码（如IF0000）
        # self.activeSymbolDict = {}
        
        # # Tick对象字典
        # self.tickSymbolSet = set()
        
        # # K线合成器字典
        # self.bgDict = {}

        # # Line线合成器字典
        # self.linegDict = {}      
             
        # # Jump线合成器字典
        # self.jumpgDict = {}  

        # # Pot线合成器字典
        # self.potgDict = {}                      
        
        # # 配置字典
        # self.settingDict = OrderedDict()
        
        # # 负责执行数据库插入的单独线程相关
        self.active = False                     # 工作状态
        self.queue = Queue()                    # 队列
        self.thread = Thread(target=self.run)   # 线程
        
        # 收盘相关
        self.marketCloseTime = None             # 收盘时间
        self.timerCount = 0                     # 定时器计数
        self.lastTimerTime = None               # 上一次记录时间
        
        # 载入设置，订阅行情
        self.loadSetting()
        
        # 启动数据插入线程
        self.start()
    
        # 注册事件监听
        self.registerEvent()  
    
    #----------------------------------------------------------------------
    def loadSetting(self):

        """加载配置"""
        with open(self.settingFilePath) as f:
            drSetting = json.load(f)

            # 如果working设为False则不启动行情记录功能
            working = drSetting['working']
            if not working:
                return
            
            # 加载收盘时间
            if 'marketCloseTime' in drSetting:
                timestamp = drSetting['marketCloseTime']
                self.marketCloseTime = datetime.strptime(timestamp, '%H:%M:%S').time()

    
        # 订阅品种 
        # symbols = ['ru1909','fu1909']
        # gateway = 'CTP'
        # import time 
        # time.sleep(3)
        # print 'subscribe ------------------>'
        # for symbol in symbols:
        #     req = VtSubscribeReq()
        #     req.symbol = symbol
        #     req.exchange = u'' #contract.exchange('SHFE')
        #     print 'market subscribe ------------------>'
        #     print req.__dict__
        #     self.mainEngine.subscribe(req, gateway )

 
    #----------------------------------------------------------------------
    def getSetting(self):
        """获取配置"""
        return self.settingDict, self.activeSymbolDict

    #----------------------------------------------------------------------
    def processOrderEvent(self, event):
        """处理委托事件"""
        '''
{'orderID': '212', 'status': u'\u5168\u90e8\u6210\u4ea4', 'direction': u'\u7a7a', 'cancelTime': '', 
'gatewayName': 'CTP', 'exchange': 'SHFE', 'symbol': 'rb1910', 'tradedVolume': 1, 'orderTime': '14:41:30',
 'frontID': 1, 'sessionID': -2036638514, 'rawData': None, 
'offset': u'\u5e73\u4eca', 'vtOrderID': 'CTP.212', 'price': 3855.0, 'vtSymbol': 'rb1910', 'totalVolume': 1}        
        '''

        order = event.dict_['data']    
        orderDic = order.__dict__    

        print u'委托情况：' +  str( orderDic )        
        print orderDic['status']

        if( orderDic['status']==u'未成交' or orderDic['status']==u'未知' ):
            #保存   'frontID': 1, 'sessionID': -2133396273,  orderid 
            pass

        # orderDic['orderID']



        # txt = u'期货成交：' +  order['orderID'] +  order['direction'] +  order['offset'] +  str(order['tradedVolume']) +  str(order['price'])
        # sendwxmsg( txt )        
        
        # # 如果订单的状态是全部成交或者撤销，则需要从workingOrderDict中移除
        # if order.status in self.FINISHED_STATUS:
        #     if order.vtOrderID in self.workingOrderDict:
        #         del self.workingOrderDict[order.vtOrderID]
        # # 否则则更新字典中的数据        
        # else:
        #     self.workingOrderDict[order.vtOrderID] = order
            
        # # 更新到持仓细节中
        # detail = self.getPositionDetail(order.vtSymbol)
        # detail.updateOrder(order)            
            
    #----------------------------------------------------------------------
    def processTradeEvent(self, event):
        """处理成交事件"""
        '''
{'orderID': '3', 'direction': u'\u591a', 'gatewayName': 'CTP', 'tradeID': '     1959888', 'exchange': 'SHFE',
 'symbol': 'rb1910', 'volume': 1, 'tradeTime': '14:26:56', 'rawData': None, 'vtTradeID': 'CTP.     1959888',
  'offset': u'\u5f00\u4ed3', 'vtOrderID': 'CTP.3', 'price': 3856.0,
'vtSymbol': 'rb1910'}        
        '''
        trade = event.dict_['data']

    
        tradeDic = trade.__dict__    

        print u'------------- 成交情况：' +  str( tradeDic )        
       
        try:
            print str(tradeDic['price'])
            txt = u'--------- CTP.成交：' +   tradeDic['offset'] +'  '+ tradeDic['direction'] +'  '+  str(tradeDic['volume'])  +'  '+  str(tradeDic['price'])
            # +   tradeDic['offset'] +'  '+ tradeDic['direction'] +'  '+  str(tradeDic['volume']) +'  '+  str(tradeDic['price'])
            print txt
            sendwxmsg( txt )

        except Exception, e:
            print e


        
 
    #----------------------------------------------------------------------
    def procecssTickEvent(self, event):
        """处理行情事件"""
        tick = event.dict_['data']
        vtSymbol = tick.vtSymbol

        #debug
        # print tick
        # sendwxmsg( "发送数据" )


        
        # 生成datetime对象
        # if not tick.datetime:
        #     if '.' in tick.time:
        #         tick.datetime = datetime.strptime(' '.join([tick.date, tick.time]), '%Y%m%d %H:%M:%S.%f')
        #     else:
        #         tick.datetime = datetime.strptime(' '.join([tick.date, tick.time]), '%Y%m%d %H:%M:%S')

        if not tick.datetime:
            if '.' in tick.time:
                tick.datetime =  ' '.join([tick.date, tick.time]) 
            else:
                tick.datetime =  ' '.join([tick.date, tick.time]) 

        # print 'marketEngine procecssTickEvent -------> '
        # print tick.__dict__
    
    
        self.onTick(tick)
                             
            
    
    #----------------------------------------------------------------------
    def processTimerEvent(self, event):
        """处理定时事件"""
        #print 'processTimerEvent ---> ' 
        # debug
        # self.doExeOrder()

        #20:55下单  
        fTime = getFutureTime()
        if( fTime['timeclass']==3 or fTime['timeclass'] ==4 or fTime['timeclass'] ==7 or fTime['timeclass'] ==8 ):
            self.doExeOrder()
            pass
        else:
            pass          

        # 如果没有设置收盘时间，则无需处理
        if not self.marketCloseTime:
            return
        
        # # 10秒检查一次
        # self.timerCount += 1
        # if self.timerCount < 10:
        #     return
        # self.timerCount = 0
        
        # # 获取当前时间
        # currentTime = datetime.now().time()
        
        # if not self.lastTimerTime:
        #     self.lastTimerTime = currentTime
        #     return
        
        # # 上一个时间戳尚未到收盘时间，且当前时间戳已经到收盘时间
        # if (self.lastTimerTime < self.marketCloseTime and
        #     currentTime >= self.marketCloseTime):
        #     # 强制所有的K线生成器立即完成K线
        #     for bg in self.bgDict.values():
        #         bg.generate()

        #     for dataGenerator in self.linegDict.values():
        #         dataGenerator.generate( lastData = True )
        #         dataGenerator.clearTmepData()
        #     for dataGenerator in self.jumpgDict.values():
        #         dataGenerator.generate(  )  #lastData = True
        #         dataGenerator.clearTmepData()  
        #     for dataGenerator in self.potgDict.values():
        #         dataGenerator.generate(  )   #lastData = True
        #         dataGenerator.clearTmepData()

        # 记录新的时间
        self.lastTimerTime = currentTime
    

    #----------------------------------------------------------------------
    def processContractEvent(self, event ):
        """处理合约事件"""
        contract = event.dict_['data']
        
        # if( contract.__dict__[u'productClass']  == u'期货' ):
          
        #     contractTemp = contract.__dict__.copy()

        #     contractType =   contractTemp['symbol'].translate(None, digits)  
        #     contractTemp['type'] = contractType
        #     contractTemp.pop('lastTik')
        #     contractTemp.pop('rawData')
        #     contractTemp.pop('optionType')
        #     contractTemp.pop('strikePrice')
        #     contractTemp.pop('underlyingSymbol')
        #     #print contractTemp
        #     self.mainEngine.dbInsert( 'futureauto', 'futures', contractTemp ) 

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick更新"""

        fTime = getFutureTime()
    
        if( fTime['timeclass']==3 or fTime['timeclass'] ==4 or fTime['timeclass'] ==7 or fTime['timeclass'] ==8 ):
        
            # do exeorder
         
            self.doExeOrder()
            pass
        else:
            pass   

        #do get order
        # self.doExeOrder()

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """分钟线更新"""
        vtSymbol = bar.vtSymbol

        
               


    #----------------------------------------------------------------------
    def onExdata(self, exData ):
        """扩展数据更新"""
        vtSymbol = exData.vtSymbol
         

        #debug 1
        #print exData.__dict__
 
        # self.insertData(EXDATA_DB_NAME, vtSymbol, exData)

        pass

    #----------------------------------------------------------------------
    def doExeOrder( self  ):
        #get data from db
        ctpGateWay = self.mainEngine.getGateway("CTP")
        setting = ctpGateWay.getSetting()
        # print("ctp setting:",setting )
        if "userID" in setting:
            userID = str(setting['userID'])
        else:
            userID =""            
        # print userID    
        orders = self.mainEngine.dbQuery( 'futureauto', 'order', {"state":0, "execacc":userID} ) 

        # print( 'orders len '+ str( len( orders ) ) ) 
      
        if(len(orders) <= 0 ):
            return 
     
        self.mainEngine.writeLog( 'orders len '+ str( len( orders ) ) )

        #exec order 
        for order in  orders: 
            # update order state 0->1 
            order["state"] = 1
            order["execdt"] = getDt()
            Order_Frequency = 0.1 #指令之间间隔


            # send order 
            if( order['type']  == 'cancel'):
                req = VtCancelOrderReq()
                req.symbol = order['symbol'] #.encode('utf-8').decode('GBK')
                req.exchange = order['exchange']
                req.frontID = order['frontID']
                req.sessionID = order['sessionID']
                req.orderID = order['orderID']
                self.mainEngine.cancelOrder(req, 'CTP' )     
                time.sleep( Order_Frequency )           
                pass 

            else:
                directionStr = ''
                if( order['type'] =='buy' ):
                    directionStr =  u'多'
                if( order['type'] =='sell' ):
                    directionStr =  u'空'    

                offsetStr = ''
                if( order['offset'] =='open' ):
                    offsetStr =  u'开仓'
                if( order['offset'] =='close' ):
                    offsetStr =  u'平仓'    
                if( order['offset'] =='close_today' ):
                    offsetStr =  u'平今'   
                if( order['offset'] =='close_yes' ):
                    offsetStr =  u'平昨'                                                           
 
                priceTypeStr = u'限价'
                currency = text_type(u'CNY')
                productClass = text_type(u'期货')                  
                # 委托
                req = VtOrderReq()
                req.symbol = order['symbol'].encode('utf-8')
                req.exchange = order['exchange'].encode('utf-8')
                req.vtSymbol = order['symbol'].encode('utf-8')
                req.price = order['price'] 
                req.volume =  order['vol'] 
           
                req.direction = text_type( directionStr )
                req.priceType = text_type( priceTypeStr )
                req.offset = text_type( offsetStr )
                req.currency = currency
                req.productClass = productClass
                
                # strData = 'symbol %s exchange %s price %.2f volume %d direction %s offset %s  vtSymbol %s gatewayName %s'\
                # %(req.symbol,req.exchange,req.price,req.volume,req.direction,req.offset, vtSymbol, gatewayName )

                # print 'currency productClass ', currency,productClass
                
                self.mainEngine.sendOrder(req, 'CTP' )  
                time.sleep( Order_Frequency )    
                
                self.mainEngine.writeLog( str(req.__dict__)  )
                   

            
            flt ={ "symbol":order["symbol"], "insertdt":order["insertdt"], "orderidsys" : order["orderidsys"]  }
            self.mainEngine.dbUpdate('futureauto', 'order', order, flt )

            # add code             
            pass

 


        # print('sendOrder:', exchange, symbol,  vtSymbol , gatewayName )
        # # 委托
        # req = VtOrderReq()
        # req.symbol = symbol
        # req.exchange = exchange
        # req.vtSymbol = vtSymbol
        # req.price = price
        # req.volume = volume
        # req.direction = text_type(self.comboDirection.currentText())
        # req.priceType = text_type(self.comboPriceType.currentText())
        # req.offset = text_type(self.comboOffset.currentText())
        # req.currency = currency
        # req.productClass = productClass
        
        # # strData = 'symbol %s exchange %s price %.2f volume %d direction %s offset %s  vtSymbol %s gatewayName %s'\
        # # %(req.symbol,req.exchange,req.price,req.volume,req.direction,req.offset, vtSymbol, gatewayName )

        # print 'currency productClass ', currency,productClass

        # # print 'sendOrder req:'  
        # # print strData
        # self.mainEngine.sendOrder(req, gatewayName)   


        pass

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.procecssTickEvent)
        self.eventEngine.register(EVENT_TIMER, self.processTimerEvent)
        self.eventEngine.register(EVENT_CONTRACT, self.processContractEvent)
        self.eventEngine.register(EVENT_ORDER, self.processOrderEvent)
        self.eventEngine.register(EVENT_TRADE, self.processTradeEvent)        
 
    #----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """插入数据到数据库（这里的data可以是VtTickData或者VtBarData）"""
        self.queue.put((dbName, collectionName, data.__dict__))
        
    #----------------------------------------------------------------------
    def run(self):
        """运行插入线程"""
        while self.active:
            try:
                dbName, collectionName, d = self.queue.get(block=True, timeout=1)
                #debug
                if( dbName == EXDATA_DB_NAME ):
                    print 'queue.get:', d
                
                # 这里采用MongoDB的update模式更新数据，在记录tick数据时会由于查询
                # 过于频繁，导致CPU占用和硬盘读写过高后系统卡死，因此不建议使用
                #flt = {'datetime': d['datetime']}
                #self.mainEngine.dbUpdate(dbName, collectionName, d, flt, True)
                
                # 使用insert模式更新数据，可能存在时间戳重复的情况，需要用户自行清洗
                try:
                    self.mainEngine.dbInsert(dbName, collectionName, d)
                except DuplicateKeyError:
                    self.writeDrLog(u'键值重复插入失败，报错信息：%s' %traceback.format_exc())
            except Empty:

                pass
            
    #----------------------------------------------------------------------
    def start(self):
        """启动"""
        self.active = True
        self.thread.start()
        
    #----------------------------------------------------------------------
    def stop(self):
        """退出"""
        if self.active:
            self.active = False
            self.thread.join()
        
    #----------------------------------------------------------------------
    def writeDrLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_DATARECORDER_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)   
    

    