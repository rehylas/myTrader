# encoding: UTF-8

from __future__ import division
from datetime import datetime

from vnpy.trader.vtConstant import STATUS_NOTTRADED, STATUS_PARTTRADED, STATUS_UNKNOWN
from vnpy.trader.vtObject import VtSignal

# 活动委托状态
STATUS_ACTIVE = [STATUS_NOTTRADED, STATUS_PARTTRADED, STATUS_UNKNOWN]


########################################################################
class SignalTemplate(object):
    """算法模板"""
    templateName = 'SignalTemplate'
    
    timestamp = ''
    count = 0
    
    @classmethod
    #----------------------------------------------------------------------
    def new(cls, engine, setting):
        """创建新对象"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        if timestamp != cls.timestamp:
            cls.timestamp = timestamp
            cls.count = 0
        else:
            cls.count += 1
            
        signalName = '_'.join([cls.templateName, cls.timestamp, str(cls.count)])
        signal = cls(engine, setting, signalName)
        return signal

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, signalName):
        """Constructor"""
        self.engine = engine
        self.active = True
        self.signalName = signalName
        self.activeOrderDict = {}  # vtOrderID:order

        self.signal  = VtSignal() 
        self.signal.signalName = signalName
    
    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """"""
        if not self.active:
            return
        
        self.onTick(tick)
    
    #----------------------------------------------------------------------
    def updateTrade(self, trade):
        """"""
        if not self.active:
            return
        
        self.onTrade(trade)
    
    #----------------------------------------------------------------------
    def updateOrder(self, order):
        """"""
        if not self.active:
            return
        
        # 活动委托需要缓存
        if order.status in STATUS_ACTIVE:
            self.activeOrderDict[order.vtOrderID] = order
        # 结束委托需要移除
        elif order.vtOrderID in self.activeOrderDict:
            del self.activeOrderDict[order.vtOrderID]
        
        self.onOrder(order)
    
    #----------------------------------------------------------------------
    def updateTimer(self):
        """"""
        if not self.active:
            return
        
        self.onTimer()
        
    #----------------------------------------------------------------------
    def stop(self):
        """"""
        self.active = False
        self.cancelAll()
        
        self.onStop()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onTimer(self):
        """"""
        pass

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeLog(u'%s策略启动' %self.name)
         
        #self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeLog(u'%s策略停止' %self.name)
        #self.putEvent()

    #----------------------------------------------------------------------
    def subscribe(self, vtSymbol):
        """"""
        self.engine.subscribe(self, vtSymbol)
    
    #----------------------------------------------------------------------
    def buy(self, vtSymbol, price, volume, priceType=None, offset=None):
        """"""
        return self.engine.buy(self, vtSymbol, price, volume, priceType, offset)
    
    #----------------------------------------------------------------------
    def sell(self, vtSymbol, price, volume, priceType=None, offset=None):
        """"""
        return self.engine.sell(self, vtSymbol, price, volume, priceType, offset)
    
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """"""
        self.engine.cancelOrder(self, vtOrderID)
    
    #----------------------------------------------------------------------
    def cancelAll(self):
        """"""
        if not self.activeOrderDict:
            return False
        
        for order in self.activeOrderDict.values():
            self.cancelOrder(order.vtOrderID)
        return True
    
    #----------------------------------------------------------------------
    def getTick(self, vtSymbol):
        """"""
        return self.engine.getTick(self, vtSymbol) 
   
    #----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        """"""
        return self.engine.getContract(self, vtSymbol)    
        
    #----------------------------------------------------------------------
    def roundValue(self, value, change):
        """标准化价格或者数量"""
        if not change:
            return value
        
        n = value / change
        v = round(n, 0) * change
        return v  
    
    #----------------------------------------------------------------------
    def putVarEvent(self, d):
        """更新变量"""
        d['active'] = self.active
        self.engine.putVarEvent(self, d)
        
    #----------------------------------------------------------------------
    def putParamEvent(self, d):
        """更新参数"""
        self.engine.putParamEvent(self, d)
    
    #----------------------------------------------------------------------
    def writeLog(self, content):
        """输出日志"""
        self.engine.writeLog(content  )
        
    #----------------------------------------------------------------------    
    def sendSignalMsg(self, signalMsg):
        if( self.engine.mainEngine ):
            sub = u'交易信号:%s '%( self.templateName  )
            self.engine.mainEngine.sendMsg( sub , signalMsg ) 

    #----------------------------------------------------------------------
    def save2db( self ):
        """保存到数据库"""
        #save self.signal   to db
        if( self.engine.mainEngine ):
            self.engine.save2db( self.signal )
            pass
            # sub = u'交易信号:%s '%( self.templateName  )
            # self.engine.mainEngine.sendMsg( sub , signalMsg )         
        pass        