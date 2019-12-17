# encoding: UTF-8
from __future__ import division
from collections import OrderedDict

from six import text_type

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED)
from vnpy.trader.uiQt import QtWidgets
#from vnpy.trader.app.signalMonitor.generateDataTemp import PotGenerator, POT_TYPE_UP, POT_TYPE_DOWN

from vnpy.trader.app.dataGenerate.potGenerator import PotGenerator, POT_TYPE_UP, POT_TYPE_DOWN
from vnpy.trader.app.signalMonitor.signalTemplate import SignalTemplate

from vnpy.trader.app.signalMonitor.uiSignalWidget import SignalWidgetTemp, QtWidgets
from vnpy.trader.vtConstant import EMPTY_UNICODE, EMPTY_STRING, EMPTY_FLOAT, EMPTY_INT



STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])

########################################################################
class GoodPotSignal(SignalTemplate):
    """好点信号"""
    """
    1. 根据设置，发现大单显示在界面上
    """
    className = 'GoodPotSignal'
    templateName = u'好点监控'
    vtSymbol = EMPTY_STRING
    totalVolume = 100
    

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, signalName): 
        """Constructor"""
        super(GoodPotSignal, self).__init__(engine, setting, signalName)

        self.engine = engine
        potSetting ={ "potsize": setting["potsize"] } 
        self.potGenor = PotGenerator( self.onPotDataGen, potSetting )
        
        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])              # 合约代码
        self.potsize =  int(setting['potsize'])       
        self.failval =  int(setting['failval'])       
        self.goodval =  int(setting['goodval'])       
 
 
        self.vtOrderID = ''     # 委托号
        self.tradedVolume = 0   # 成交数量
        self.orderStatus = ''   # 委托状态

        self.goodlook = False
        self.fail = 0.0
        self.win = 0.0
        self.type = 0
        self.potPrice = 0.0

        self.lastTick = None
        
        self.subscribe(self.vtSymbol)
        self.paramEvent()
        self.varEvent()

    #----------------------------------------------------------------------
    def onPotDataGen(self, newPotData):
        dl = self.potGenor.dataSet
        n = len(dl)
        if( n  >=2 ):
            Pot = dl[n-2]
            msg = u'%s 新点:  %f, %f, %f, %f, %d' %(Pot.time,  Pot.open, Pot.close, (Pot.close-Pot.open), Pot.dim,  Pot.type )
            self.writeLog(msg)
            print msg   
            msgObject = { 'msg': msg }
            self.engine.putSignalEvent( self , msgObject )
            

        checked = self.checkLook( newPotData.type ) 
        if( checked == False ):
            return  
            pass

        if(newPotData.type == POT_TYPE_DOWN):
            self.goodlook = True
            self.fail = 0.0
            self.win = 0.0
            self.potPrice = newPotData.close
            self.type = POT_TYPE_UP
        else:
            self.goodlook = True
            self.fail = 0.0
            self.win = 0.0
            self.potPrice = newPotData.close
            self.type = POT_TYPE_DOWN                
        pass

    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        if( self.lastTick != None ):
            if( tick.lastVolume == 0  ):
                tick.lastVolume = tick.volume - self.lastTick.volume            

        self.potGenor.updateTick( tick )
        

        if( self.processTik( tick ) ):
            msg = u'%s 发现GoodPot，代码：%s， 方向:  %d 点价:%.1f 现价:%.1f' %(tick.time, self.vtSymbol,  self.type ,self.potPrice, tick.lastPrice  )
            self.writeLog(msg)
            self.sendSignalMsg( msg )
            d ={ "vtSymbol":self.vtSymbol,"datetime":tick.datetime, "type":self.type, "price":tick.lastPrice  }
            self.engine.putSignalEvent(self,  d)

            # 生成信号数据
            self.signal.datetime = tick.datetime
            self.signal.date = tick.date
            self.signal.time = tick.time
            self.signal.lastPrice = tick.lastPrice
            self.signal.level = 1
            self.signal.msg = msg
            self.signal.vtSymbol = self.vtSymbol
            self.signal.type = self.type
            self.signal.code ='goodpot'

            self.onSignal()
 

        self.lastTick =  tick
        # 更新变量
        self.varEvent()         
        return 
 
    #----------------------------------------------------------------------
    def processTik(self, tick):
        if( self.goodlook == False ):
            return False
        win_temp =  (tick.lastPrice -  self.potPrice)*self.type
        # msg =u'监控价差 %.1f %.1f %.1f' %(win_temp, tick.lastPrice , self.potPrice)

        if( win_temp >= self.goodval ):  #goodpot
            self.goodlook = False
            return True

        if( win_temp < -self.failval ):  #not goodpot
            self.goodlook = False
            return False

        return False
        pass 

    #----------------------------------------------------------------------
    def checkLook( self, newPotType ) :
        dl = self.potGenor.dataSet
        n = len(dl)
        if( n  <=5 ):
            return False
                     
        if(newPotType == POT_TYPE_DOWN):
            if( dl[-1].close > dl[-3].close  and dl[-3].close > dl[-5].close and dl[-2].close > dl[-4].close  ):
                return True
        else:
            if( dl[-1].close < dl[-3].close  and dl[-3].close < dl[-5].close and dl[-2].close < dl[-4].close  ):
                return True             
         
        return False
        
        
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """"""

        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTimer(self):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onStop(self):
        """"""
        self.writeLog(u'停止算法')
        self.varEvent()
        
    #----------------------------------------------------------------------
    def varEvent(self):
        """更新变量"""
        d = OrderedDict()
        d[u'算法状态'] = self.active
        d[u'委托号'] = self.vtOrderID
        d[u'成交数量'] = self.tradedVolume
        d[u'委托状态'] = self.orderStatus
        d['active'] = self.active
        self.putVarEvent(d)
    
    #----------------------------------------------------------------------
    def paramEvent(self):
        """更新参数"""
        d = OrderedDict()
        d[u'代码'] = self.vtSymbol
        # d[u'方向'] = self.direction
        # d[u'触发价格'] = self.stopPrice
        d[u'数量'] = self.totalVolume
        # d[u'开平'] = self.offset
        self.putParamEvent(d)


########################################################################
class GoodPotWidget(SignalWidgetTemp): 
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, signalEngine, parent=None):
        """Constructor"""
        print "BigTradeWidget __init__"
        super(GoodPotWidget, self).__init__(signalEngine, parent)        
        self.templateName = GoodPotSignal.templateName
        
        
    #----------------------------------------------------------------------
    def initSignalLayout(self):
        """"""
 
        self.lineSymbol = QtWidgets.QLineEdit()
        
        self.comboDirection = QtWidgets.QComboBox()
        self.comboDirection.addItem(DIRECTION_LONG)
        self.comboDirection.addItem(DIRECTION_SHORT)
        self.comboDirection.setCurrentIndex(0)
        
 
        self.spinPotsize = QtWidgets.QDoubleSpinBox()
        self.spinPotsize.setMinimum(0)
        self.spinPotsize.setMaximum(1000)
        self.spinPotsize.setDecimals(0)
       

        self.spinFailval = QtWidgets.QDoubleSpinBox()
        self.spinFailval.setMinimum(0)
        self.spinFailval.setMaximum(1000)
        self.spinFailval.setDecimals(0)

        self.spinGoodval = QtWidgets.QDoubleSpinBox()
        self.spinGoodval.setMinimum(0)
        self.spinGoodval.setMaximum(1000)
        self.spinGoodval.setDecimals(0)
 
        buttonStart = QtWidgets.QPushButton(u'启动')
        buttonStart.clicked.connect(self.addSignal)
        buttonStart.setMinimumHeight(100)
        
        Label = QtWidgets.QLabel
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(u'代码'), 0, 0)
        grid.addWidget(self.lineSymbol, 0, 1)

        grid.addWidget(Label(u'点大小'), 1, 0)
        grid.addWidget(self.spinPotsize, 1, 1)
        grid.addWidget(Label(u'亏点'), 2, 0)
        grid.addWidget(self.spinFailval, 2, 1)
        grid.addWidget(Label(u'盈点'), 3, 0)
        grid.addWidget(self.spinGoodval, 3, 1)
 
        return grid
    
    #----------------------------------------------------------------------
    def getSignalSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = GoodPotSignal.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        setting['potsize'] =  (self.spinPotsize.value())
        setting['failval'] =  (self.spinFailval.value())
        setting['goodval'] =  (self.spinGoodval.value())

        # setting['direction'] = text_type(self.comboDirection.currentText())
        # setting['stopPrice'] = float(self.spinPrice.value())
        # setting['offset'] = text_type(self.comboOffset.currentText())
        # setting['priceAdd'] = float(self.spinPriceAdd.value())
                 
        return setting
        
    
    
