# encoding: UTF-8

'''
本文件中实现了行情数据记录引擎，用于汇总TICK数据，并生成K线插入数据库。

使用DR_setting.json来配置需要收集的合约，以及主力合约代码。
'''

import json
import csv
import os
from string import digits
import copy
import random
from string import digits
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta 
import time 
from Queue import Queue, Empty
from threading import Thread
from pymongo.errors import DuplicateKeyError

from vnpy.event import Event
from vnpy.trader.vtEvent import *
from vnpy.trader.vtFunction import todayDate, getJsonPath
from vnpy.trader.vtObject import VtSubscribeReq, VtLogData, VtBarData, VtTickData

# from vnpy.trader.app.ctaStrategy.ctaTemplate import BarGenerator
# from vnpy.trader.app.dataGenerate.jumpGenerator import JumpGenerator
# from vnpy.trader.app.dataGenerate.lineGenerator import LineGenerator
# from vnpy.trader.app.dataGenerate.potGenerator import PotGenerator


#from .drBase import *
from .language import text

#本应用只支持CTP  

########################################################################
class MarketEngine(object):
    """数据记录引擎"""
    
    settingFileName = 'Market_setting.json'
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
    def procecssTickEvent(self, event):
        """处理行情事件"""
        tick = event.dict_['data']
        vtSymbol = tick.vtSymbol


        
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
    
    def processAccountEvent(self, event):
        """处理账户事件"""
        # account = event.dict_['data']
        # self.accountDict[account.vtAccountID] = account    
        try:
            dbName ='futureauto' 
            collectionName = 'accountdetail'
            account = event.dict_['data']
            #print account.__dict__
            account = self.prodict( account.__dict__ )
            self.mainEngine.dbInsert(dbName, collectionName, account)
            print account
        except DuplicateKeyError:
            self.writeDrLog(u'键值重复插入失败，报错信息：%s' %traceback.format_exc())        

    def prodict(self, dictdata ):
        dictdata.pop('rawData')
        
        #print dictdata
        strDic = json.dumps( dictdata)
        strDic = strDic.lower()
        retDic = json.loads( strDic )
        #print strDic
 
        strTime = time.strftime("%Y-%m-%d", time.localtime())
   
        retDic['date'] = strTime
        retDic['id'] = self.randomid()
        return retDic
        pass

    def randomid(self):
        str = ""
        for i in range(6):
            ch = chr(random.randrange(ord('0'), ord('9') + 1))
            str += ch
        
        return str    

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
        vtSymbol = tick.vtSymbol

        tickdata =   tick.__dict__.copy()
        tickdata.pop('rawData')
        tickdata.pop('gatewayName')
        tickdata['rate'] =  ( tickdata['lastPrice'] - tickdata['preClosePrice'] ) /tickdata['preClosePrice'] *100
        tickdata['rate'] = round(tickdata['rate'], 2)
       
        self.mainEngine.db__setTick(  vtSymbol,  str(tickdata) )  
        self.mainEngine.db_Publish_Tick(  str(tickdata) ) 
               
        
        # if vtSymbol in self.tickSymbolSet:
        #     self.insertData(TICK_DB_NAME, vtSymbol, tick)
            
        #     if vtSymbol in self.activeSymbolDict:
        #         activeSymbol = self.activeSymbolDict[vtSymbol]
        #         self.insertData(TICK_DB_NAME, activeSymbol, tick)
            
            
        #     self.writeDrLog(text.TICK_LOGGING_MESSAGE.format(symbol=tick.vtSymbol,
        #                                                      time=tick.time, 
        #                                                      last=tick.lastPrice, 
        #                                                      bid=tick.bidPrice1, 
        #                                                      ask=tick.askPrice1))
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """分钟线更新"""
        vtSymbol = bar.vtSymbol
        
        # self.insertData(MINUTE_DB_NAME, vtSymbol, bar)
        
        # if vtSymbol in self.activeSymbolDict:
        #     activeSymbol = self.activeSymbolDict[vtSymbol]
        #     self.insertData(MINUTE_DB_NAME, activeSymbol, bar)                    
        
        # self.writeDrLog(text.BAR_LOGGING_MESSAGE.format(symbol=bar.vtSymbol, 
        #                                                 time=bar.time, 
        #                                                 open=bar.open, 
        #                                                 high=bar.high, 
        #                                                 low=bar.low, 
        #                                                 close=bar.close))        


    #----------------------------------------------------------------------
    def onExdata(self, exData ):
        """扩展数据更新"""
        vtSymbol = exData.vtSymbol

        #debug 1
        #print exData.__dict__
 
        # self.insertData(EXDATA_DB_NAME, vtSymbol, exData)

        pass

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.procecssTickEvent)
        self.eventEngine.register(EVENT_TIMER, self.processTimerEvent)
        self.eventEngine.register(EVENT_CONTRACT, self.processContractEvent)
        self.eventEngine.register(EVENT_ACCOUNT, self.processAccountEvent)

        #def onAccount(self, account):
 
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
    

    