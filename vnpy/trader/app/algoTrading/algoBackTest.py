# encoding: UTF-8

'''
本文件中包含的是CTA模块的回测引擎，回测引擎的API和CTA引擎一致，
可以使用和实盘相同的代码进行回测。
'''
from __future__ import division
from __future__ import print_function

from datetime import datetime, timedelta
from collections import OrderedDict
from itertools import product
import multiprocessing
import copy

import pymongo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from vnpy.rpc import RpcClient, RpcServer, RemoteException


# 如果安装了seaborn则设置为白色风格
try:
    import seaborn as sns       
    sns.set_style('whitegrid')  
except ImportError:
    pass


from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtObject import VtTickData, VtBarData, VtSignal    
from vnpy.trader.vtConstant import *
from vnpy.trader.vtGateway import VtOrderData, VtTradeData
from vnpy.trader.vtEngine import LogEngine

SIGNALTRADING_DB_NAME = 'MyTrader_AlgoTrading_Db'     # SignalMonitor 数据库名

SETTING_COLLECTION_NAME = 'AlgoSetting'             # 信号配置集合名
HISTORY_COLLECTION_NAME = 'AlgoHistory'             # 信号历史集合名
SIGNAL_COLLECTION_NAME  = 'AlgoRecord'              # 信号数据集合名


#from .ctaBase import *  algoBackTest.py

########################################################################
class AlgoBackEngine(object):
    """
    算法交易回测引擎
    函数接口和信号引擎保持一样，
    从而实现同一套代码从回测到实盘。
    """
    
    TICK_MODE = 'tick'
    BAR_MODE = 'bar'

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.mainEngine = None
        self.dataStartDate = None       # 回测数据开始日期，datetime对象
        self.dataEndDate = None         # 回测数据结束日期，datetime对象   
        self.dt = None      # 最新的时间
        self.logList = []               # 日志记录  

        # 日志引擎实例
        self.logEngine = None
        self.initLogEngine()           


    #----------------------------------------------------------------------
    def initLogEngine(self):
        """初始化日志引擎"""
        if not globalSetting["logActive"]:
            return
        
        # 创建引擎
        self.logEngine = LogEngine()
        
        # 设置日志级别
        levelDict = {
            "debug": LogEngine.LEVEL_DEBUG,
            "info": LogEngine.LEVEL_INFO,
            "warn": LogEngine.LEVEL_WARN,
            "error": LogEngine.LEVEL_ERROR,
            "critical": LogEngine.LEVEL_CRITICAL,
        }
        level = levelDict.get(globalSetting["logLevel"], LogEngine.LEVEL_CRITICAL)
        self.logEngine.setLogLevel(level)
        
        # 设置输出
        if globalSetting['logConsole']:
            self.logEngine.addConsoleHandler()
            
        if globalSetting['logFile']:
            self.logEngine.addFileHandler()
            
        # 注册事件监听
        #self.registerLogEvent(EVENT_LOG)

    #------------------------------------------------
    # 通用功能
    #------------------------------------------------    
    
    #----------------------------------------------------------------------
    def roundToPriceTick(self, price):
        """取整价格到合约最小价格变动"""
        if not self.priceTick:
            return price
        
        newPrice = round(price/self.priceTick, 0) * self.priceTick
        return newPrice

    #----------------------------------------------------------------------
    def output(self, content):
        """输出内容"""
        print(str(datetime.now()) + "\t" + content)  


    #------------------------------------------------
    # 参数设置相关
    #------------------------------------------------
    
    #----------------------------------------------------------------------
    def setStartDate(self, startDate='20100416', initDays=0):
        """设置回测的启动日期"""
        self.startDate = startDate
        self.initDays = initDays
        
        self.dataStartDate = datetime.strptime(startDate, '%Y%m%d')
        
        initTimeDelta = timedelta(initDays)
        self.strategyStartDate = self.dataStartDate + initTimeDelta
        
    #----------------------------------------------------------------------
    def setEndDate(self, endDate='20100416' ):
        self.dataEndDate = datetime.strptime(endDate, '%Y%m%d')
 
    #----------------------------------------------------------------------
    def setBacktestingMode(self, mode):
        """设置回测模式"""
        self.mode = mode
    
    #----------------------------------------------------------------------
    def setDatabase(self, dbName, symbol):
        """设置历史数据所用的数据库"""
        self.dbName = dbName
        self.symbol = symbol
    
        
    #----------------------------------------------------------------------
    def setSize(self, size):
        """设置合约大小"""
        self.size = size
 
    #----------------------------------------------------------------------
    def setPriceTick(self, priceTick):
        """设置价格最小变动"""
        self.priceTick = priceTick                    

    #------------------------------------------------
    # 数据回放相关x
    #------------------------------------------------    
#   出错。嗡嗡嗡的【图 ftl",k'/..mmmnnvcxssweropkl''  ;. /
    #----------------------------------------------------------------------
    def loadHistoryData(self):
        """载入历史数据"""
        self.dbClient = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
        collection = self.dbClient[self.dbName][self.symbol]          

        self.output(u'开始载入数据')
        
        # 首先根据回测模式，确认要使用的数据类
        if self.mode == self.BAR_MODE:
            dataClass = VtBarData
            func = self.newBar
        else:
            dataClass = VtTickData
            func = self.newTick

        # 载入初始化需要用的数据   

        flt = {'datetime':{'$gte':self.dataStartDate, '$lt':self.strategyStartDate}}        
        initCursor = collection.find(flt).sort('datetime')

        print('flt:',flt )
        print( self.dbName, self.symbol  )
        
        # 将数据从查询指针中读取出，并生成列表
        self.initData = []              # 清空initData列表
        for d in initCursor:
            data = dataClass()
            data.__dict__ = d
            self.initData.append(data)      
        
        # 载入回测数据
        if not self.dataEndDate:
            flt = {'date':{'$gte':self.strategyStartDate}}   # 数据过滤条件  self.strategyStartDate
        else:
            flt = {'date':{"$gte":"20181106", "$lte":"20181106"}}   # self.dataEndDate
        self.dbCursor = collection.find(flt).sort('datetime')
        print('flt:',flt )
        print( self.dbName, self.symbol  )        
        
        if isinstance(self.dbCursor, list):
            count = len(initCursor) + len(self.dbCursor)
        else:
            count = initCursor.count() + self.dbCursor.count()
        self.output(u'载入完成，数据量：%s' %count)
        
    #----------------------------------------------------------------------
    def runBacktesting(self):
        """运行回测"""
        # 载入历史数据
        self.loadHistoryData()
        
        # 首先根据回测模式，确认要使用的数据类
        if self.mode == self.BAR_MODE:
            dataClass = VtBarData
            func = self.newBar
        else:
            dataClass = VtTickData
            func = self.newTick

        self.output(u'开始回测')
        
        #self.strategy.onInit()
        #self.strategy.inited = True
        self.output(u'策略初始化完成')
        
        self.strategy.trading = True
        self.strategy.onStart()
        self.output(u'策略启动完成')
        
        self.output(u'开始回放数据')

        for d in self.dbCursor:
            data = dataClass()
            data.__dict__ = d
            func(data)     
            
        self.output(u'数据回放结束')
        
    #----------------------------------------------------------------------
    def newBar(self, bar):
        """新的K线"""
        self.bar = bar
        self.dt = bar.datetime
 
        self.strategy.onBar(bar)    # 推送K线到策略中
        
        self.updateDailyClose(bar.datetime, bar.close)
    
    #----------------------------------------------------------------------
    def newTick(self, tick):
        """新的Tick"""
        self.tick = tick
        self.dt = tick.datetime
        
 
        self.strategy.onTick(tick)
        
        self.updateDailyClose(tick.datetime, tick.lastPrice)
        
    #----------------------------------------------------------------------
    def initStrategy(self, algoClass, setting=None):
        """
        初始化策略
        setting是策略的参数设置，如果使用类中写好的默认设置则可以不传该参数
        """
        self.strategy = algoClass(self, setting, algoClass.templateName )
        self.strategy.name = self.strategy.className
    
 
    #------------------------------------------------
    # 策略接口相关
    #------------------------------------------------    
    #----------------------------------------------------------------------

    def subscribe(self, call, vtSymbol):
        """回测中忽略"""
        pass

    def putStrategyEvent(self, name):
        """发送策略更新事件，回测中忽略"""
        pass

    #----------------------------------------------------------------------
    def putVarEvent(self, call, d):
        """更新变量"""
        pass
        
    #----------------------------------------------------------------------
    def putParamEvent(self, call, d):
        """发送策略更新事件，回测中忽略"""
        pass


    #----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """考虑到回测中不允许向数据库插入数据，防止实盘交易中的一些代码出错"""
        pass
    
    #----------------------------------------------------------------------
    def putSignalEvent(self, signal, d):
        """出现信号"""
        className = signal.className
        
        d['signalName'] = className
        # event = Event(EVENT_SIGNAL_PARAM)
        # event.dict_['data'] = d
        # self.eventEngine.put( event )  
        # self.mainEngine.dbInsert(  SIGNALTRADING_DB_NAME, SIGNAL_COLLECTION_NAME, d) 
        # print( d )
        self.log(  'debug', d )

    def log(self, level, msg ):
       
        if( level == 'debug'):
            self.logEngine.debug( msg )
        if( level == 'info'):
            self.logEngine.info( msg )
        if( level == 'warn'):
            self.logEngine.warn( msg )
        if( level == 'error'):
            self.logEngine.error( msg )                                    
        pass 
 
    #----------------------------------------------------------------------
    def loadBar(self, dbName, collectionName, startDate):
        """直接返回初始化数据列表中的Bar"""
        return self.initData
    
    #----------------------------------------------------------------------
    def loadTick(self, dbName, collectionName, startDate):
        """直接返回初始化数据列表中的Tick"""
        return self.initData
    
    #----------------------------------------------------------------------
    def writeLog(self, content):
        """记录日志"""
        log = str(self.dt) + ' ' + content 
        self.logList.append(log)
   
  
    #----------------------------------------------------------------------
    def saveSyncData(self, strategy):
        """保存同步数据（无效）"""
        pass
    
    #----------------------------------------------------------------------
    def getPriceTick(self, strategy):
        """获取最小价格变动"""
        return self.priceTick                    
 
 
    #----------------------------------------------------------------------
    def sendSignal(self, signal ):   # VtSignal = type(signal) 
        pass

    #----------------------------------------------------------------------
    def updateDailyClose(self,  datetime,  lastPrice):
        pass        

    #----------------------------------------------------------------------
    def buy(self, algo, vtSymbol, price, volume, priceType=None, offset=None):
        """买入"""
        return '' ''

    #----------------------------------------------------------------------
    def sell(self, algo, vtSymbol, price, volume, priceType=None, offset=None):
        """卖出"""
        return '' 

    #----------------------------------------------------------------------
    def cancelOrder(self, algo, vtOrderID):
        """撤单"""
        pass
    