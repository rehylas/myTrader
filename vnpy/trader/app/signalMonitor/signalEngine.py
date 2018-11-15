# encoding: UTF-8

'''
信号监控引擎
'''

from __future__ import division
import os
import importlib

from vnpy.event import Event
from vnpy.rpc import RpcServer
from vnpy.trader.vtEvent import EVENT_TIMER, EVENT_TICK, EVENT_ORDER, EVENT_TRADE
from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT, 
                                    PRICETYPE_LIMITPRICE, PRICETYPE_MARKETPRICE,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    OFFSET_CLOSETODAY, OFFSET_CLOSEYESTERDAY)
from vnpy.trader.vtObject import VtSubscribeReq, VtOrderReq, VtCancelOrderReq, VtLogData

from .signal import SIGNAL_DICT


EVENT_SIGNAL_LOG = 'eSignalLog'         # 算法日志事件
EVENT_SIGNAL_PARAM = 'eSignalParam'     # 算法参数事件
EVENT_SIGNAL_VAR = 'eSignalVar'         # 算法变量事件
EVENT_SIGNAL_SETTING = 'eSignalSetting' # 算法配置事件

SIGNALTRADING_DB_NAME = 'MyTrader_SignalTrading_Db'     # SignalMonitor 数据库名

SETTING_COLLECTION_NAME = 'SignalSetting'             # 信号配置集合名
HISTORY_COLLECTION_NAME = 'SignalHistory'             # 信号历史集合名
SIGNAL_COLLECTION_NAME  = 'SignalRecord'              # 信号数据集合名


########################################################################
class SignalEngine(object):
    """监控引擎"""
    
    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.rpcServer = None
        
        self.signalDict = {}          # signalName:signal
        self.orderSignalDict = {}     # vtOrderID:signal
        self.symbolSignalDict = {}    # vtSymbol:signal set
        self.settingDict = {}       # settingName:setting
        self.historyDict = {}       # signalName:dict
        
        self.registerEvent()

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.processTickEvent)
        self.eventEngine.register(EVENT_TIMER, self.processTimerEvent)
        self.eventEngine.register(EVENT_ORDER, self.processOrderEvent)
        self.eventEngine.register(EVENT_TRADE, self.processTradeEvent)
    
    #----------------------------------------------------------------------
    def stop(self):
        """停止"""
        if self.rpcServer:
            self.rpcServer.stop()
    
    #----------------------------------------------------------------------
    def processTickEvent(self, event):
        """行情事件"""
        tick = event.dict_['data']
        
        l = self.symbolSignalDict.get(tick.vtSymbol, None)
        if l:    
            for signal in l:
                signal.updateTick(tick)
        
    #----------------------------------------------------------------------
    def processOrderEvent(self, event):
        """委托事件"""
        order = event.dict_['data']
        
        signal = self.orderSignalDict.get(order.vtOrderID, None)
        if signal:
            signal.updateOrder(order)

    #----------------------------------------------------------------------
    def processTradeEvent(self, event):
        """成交事件"""
        trade = event.dict_['data']
        
        signal = self.orderSignalDict.get(trade.vtOrderID, None)
        if signal:
            signal.updateTrade(trade)
    
    #----------------------------------------------------------------------
    def processTimerEvent(self, event):
        """定时事件"""
        for signal in self.signalDict.values():
            signal.updateTimer()
    
    #----------------------------------------------------------------------
    def addSignal(self, signalSetting):
        """新增监控"""
        templateName = signalSetting['templateName']
        signalClass = SIGNAL_DICT[templateName]
        print 'debug'
        print templateName
        print signalClass
        signal = signalClass.new(self, signalSetting)
        
        self.signalDict[signal.signalName] = signal
        
        return signal.signalName
    
    #----------------------------------------------------------------------
    def stopSignal(self, signalName):
        """停止监控"""
        if signalName in self.signalDict:
            self.signalDict[signalName].stop()
            del self.signalDict[signalName]
    
    #----------------------------------------------------------------------
    def stopAll(self):
        """全部停止"""
        l = self.signalDict.keys()
        for signalName in l:
            self.stopSignal(signalName)
    
    #----------------------------------------------------------------------
    def subscribe(self, signal, vtSymbol):
        """"""
        contract = self.mainEngine.getContract(vtSymbol)
        if not contract:
            self.writeLog(u'%s订阅行情失败，找不到合约%s' %(signal.signalName, vtSymbol))
            return        

        # 如果vtSymbol已存在于字典，说明已经订阅过
        if vtSymbol in self.symbolSignalDict:
            s = self.symbolSignalDict[vtSymbol]
            s.add(signal)
            return
        # 否则需要添加到字典中并执行订阅
        else:
            s = set()
            self.symbolSignalDict[vtSymbol] = s
            s.add(signal)
            
            req = VtSubscribeReq()
            req.symbol = contract.symbol
            req.exchange = contract.exchange
            self.mainEngine.subscribe(req, contract.gatewayName)

    #----------------------------------------------------------------------
    def sendOrder(self, signal, vtSymbol, direction, price, volume, 
                  priceType=None, offset=None):
        """发单"""
        contract = self.mainEngine.getContract(vtSymbol)
        if not contract:
            self.writeLog(u'%s委托下单失败，找不到合约：%s' %(signal.signalName, vtSymbol))

        vtSymbol = '.'.join([contract.symbol, contract.exchange])
        req = VtOrderReq()
        req.vtSymbol = vtSymbol
        req.symbol = contract.symbol
        req.exchange = contract.exchange
        req.direction = direction        
        req.offset = OFFSET_CLOSETODAY
        req.price = price
        req.volume = volume
        
        if priceType:
            req.priceType = priceType
        else:
            req.priceType = PRICETYPE_LIMITPRICE
        
        if offset:
            req.offset = offset
        else:
            req.offset = OFFSET_OPEN
        
        strData = 'symbol %s exchange %s price %.2f volume %d direction %s offset %s vtSymbol %s gatewayName %s'\
        %(req.symbol,req.exchange,req.price,req.volume,req.direction,req.offset,req.vtSymbol,contract.gatewayName)

        print 'currency productClass ',req.currency, req.productClass
        # print 'sendOrder req:'  
        # print strData
        vtOrderID = self.mainEngine.sendOrder(req, contract.gatewayName)
        self.orderSignalDict[vtOrderID] = signal
        
        return vtOrderID

    #----------------------------------------------------------------------
    def buy(self, signal, vtSymbol, price, volume, priceType=None, offset=None):
        """买入"""
        return self.sendOrder(signal, vtSymbol, DIRECTION_LONG, price, volume, priceType, offset)

    #----------------------------------------------------------------------
    def sell(self, signal, vtSymbol, price, volume, priceType=None, offset=None):
        """卖出"""
        return self.sendOrder(signal, vtSymbol, DIRECTION_SHORT, price, volume, priceType, offset)

    #----------------------------------------------------------------------
    def cancelOrder(self, signal, vtOrderID):
        """撤单"""
        order = self.mainEngine.getOrder(vtOrderID)
        if not order:
            self.writeLog(u'%s委托撤单失败，找不到委托：%s' %(signal.signalName, vtOrderID))
            return

        req = VtCancelOrderReq()
        req.symbol = order.symbol
        req.exchange = order.exchange
        req.orderID = order.orderID
        req.frontID = order.frontID
        req.sessionID = order.sessionID
        self.mainEngine.cancelOrder(req, order.gatewayName)
        
    #----------------------------------------------------------------------
    def writeLog(self, content, signal=None):
        """输出日志"""
        log = VtLogData()
        log.logContent = content
        
        if signal:
            log.gatewayName = signal.signalName

        event = Event(EVENT_SIGNAL_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)
    
    #----------------------------------------------------------------------
    def putVarEvent(self, signal, d):
        """更新变量"""
        signalName = signal.signalName
        
        d['signalName'] = signalName
        event = Event(EVENT_SIGNAL_VAR)
        event.dict_['data'] = d
        self.eventEngine.put(event)
        
        # RPC推送
        if self.rpcServer:
            self.rpcServer.publish('SignalTrading', event)
        
        # 保存数据到数据库
        history = self.historyDict.setdefault(signalName, {})
        history['signalName'] = signalName
        history['var'] = d
        
        self.mainEngine.dbUpdate(SIGNALTRADING_DB_NAME,
                                 HISTORY_COLLECTION_NAME,
                                 history,
                                 {'signalName': signalName},
                                 True)
        
        
    #----------------------------------------------------------------------
    def putParamEvent(self, signal, d):
        """更新参数"""
        signalName = signal.signalName
        
        d['signalName'] = signalName
        event = Event(EVENT_SIGNAL_PARAM)
        event.dict_['data'] = d
        self.eventEngine.put(event)    
        
        # RPC推送
        if self.rpcServer:
            self.rpcServer.publish('SignalTrading', event)        
        
        # 保存数据到数据库
        history = self.historyDict.setdefault(signalName, {})
        history['signalName'] = signalName
        history['param'] = d
        
        self.mainEngine.dbUpdate(SIGNALTRADING_DB_NAME,
                                 HISTORY_COLLECTION_NAME,
                                 history,
                                 {'signalName': signalName},
                                 True)        
    

    #----------------------------------------------------------------------
    def putSignalEvent(self, signal, d):
        """更新参数"""
        signalName = signal.signalName
        
        d['signalName'] = signalName
        event = Event(EVENT_SIGNAL_PARAM)
        event.dict_['data'] = d
        self.eventEngine.put( event )  
        self.mainEngine.dbInsert(  SIGNALTRADING_DB_NAME, SIGNAL_COLLECTION_NAME, d)  

 
    #----------------------------------------------------------------------
    def getTick(self, signal, vtSymbol):
        """查询行情"""
        tick = self.mainEngine.getTick(vtSymbol)
        if not tick:
            self.writeLog(u'%s查询行情失败，找不到报价：%s' %(signal.signalName, vtSymbol))
            return            
            
        return tick
    
    #----------------------------------------------------------------------
    def getContract(self, signal, vtSymbol):
        """查询合约"""
        contract = self.mainEngine.getContract(vtSymbol)
        if not contract:
            self.writeLog(u'%s查询合约失败，找不到报价：%s' %(signal.signalName, vtSymbol))
            return            
        
        return contract
    
    #----------------------------------------------------------------------
    def saveSignalSetting(self, signalSetting):
        """保存算法配置"""
        settingName = signalSetting['settingName']
        self.settingDict[settingName] = signalSetting
        
        self.mainEngine.dbUpdate(SIGNALTRADING_DB_NAME, 
                                 SETTING_COLLECTION_NAME,
                                 signalSetting,
                                 {'settingName': settingName},
                                 True)
        
        self.putSettingEvent(settingName, signalSetting)
    
    #----------------------------------------------------------------------
    def loadSignalSetting(self):
        """加载算法配置"""
        l = self.mainEngine.dbQuery(SIGNALTRADING_DB_NAME,
                                    SETTING_COLLECTION_NAME,
                                    {},
                                    'templateName')
        for signalSetting in l:
            settingName = signalSetting['settingName']
            self.settingDict[settingName] = signalSetting
            self.putSettingEvent(settingName, signalSetting)
    
    #----------------------------------------------------------------------
    def deleteSignalSetting(self, signalSetting):
        """删除算法配置"""
        settingName = signalSetting['settingName']
        
        del self.settingDict[settingName]
        self.mainEngine.dbDelete(SIGNALTRADING_DB_NAME,
                                 SETTING_COLLECTION_NAME,
                                 {'settingName': settingName})
        
        self.putSettingEvent(settingName, {})
        
    #----------------------------------------------------------------------
    def putSettingEvent(self, settingName, signalSetting):
        """发出算法配置更新事件"""
        signalSetting['settingName'] = settingName
        
        event = Event(EVENT_SIGNAL_SETTING)
        event.dict_['data'] = signalSetting
        self.eventEngine.put(event)
    
    #----------------------------------------------------------------------
    def startRpc(self, repPort, pubPort):
        """启动RPC服务"""
        if self.rpcServer:
            return
        
        self.rpcServer = SignalRpcServer(self, repPort, pubPort)
        self.rpcServer.start()
        self.writeLog(u'算法交易RPC服务启动成功，REP端口:%s，PUB端口:%s' %(repPort, pubPort))

    #----------------------------------------------------------------------
    def save2db(self,  signal):
        """保存到数据库"""        
        data = signal.__dict__.copy() 
        self.mainEngine.dbInsert(  SIGNALTRADING_DB_NAME, signal.vtSymbol, data )  
        pass
   

########################################################################
class SignalRpcServer(RpcServer):
    """算法交易RPC服务器"""
    
    #----------------------------------------------------------------------
    def __init__(self, engine, repPort, pubPort):
        """Constructor"""
        self.engine = engine
        repAddress = 'tcp://*:%s' %repPort
        pubAddress = 'tcp://*:%s' %pubPort
        
        super(SignalRpcServer, self).__init__(repAddress, pubAddress)
        
        self.register(self.engine.addSignal)
        self.register(self.engine.stopSignal)
        self.register(self.engine.stopAll)
    