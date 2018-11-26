# encoding: UTF-8

from __future__ import division
from collections import OrderedDict

from six import text_type

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED)
from vnpy.trader.uiQt import QtWidgets

from vnpy.trader.app.dataGenerate.jumpGenerator import JumpGenerator
from vnpy.trader.app.dataGenerate.lineGenerator import LineGenerator
from vnpy.trader.app.dataGenerate.potGenerator import PotGenerator


from vnpy.trader.app.signalMonitor.signalTemplate import SignalTemplate
from vnpy.trader.app.signalMonitor.uiSignalWidget import SignalWidgetTemp, QtWidgets
from vnpy.trader.vtConstant import EMPTY_UNICODE, EMPTY_STRING, EMPTY_FLOAT, EMPTY_INT



STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])

########################################################################
class BigTradeSignal(SignalTemplate):
    """大单交易信号"""
    """
    1. 根据设置，发现大单显示在界面上
    """
    className = 'BigTradeSignal'
    templateName = u'大单监控'
    vtSymbol = EMPTY_STRING
    totalVolume = 100
    jumps = None
    lines = None

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, signalName): 
        """Constructor"""
        super(BigTradeSignal, self).__init__(engine, setting, signalName)
        
        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])              # 合约代码
        # self.direction = text_type(setting['direction'])    # 买卖
        # self.stopPrice = float(setting['stopPrice'])        # 触发价格
        self.totalVolume =  int(setting['totalVolume'])       # 数量
        # self.offset = text_type(setting['offset'])          # 开平
        # self.priceAdd = float(setting['priceAdd'])          # 下单时的超价

        
        self.vtOrderID = ''     # 委托号
        self.tradedVolume = 0   # 成交数量
        self.orderStatus = ''   # 委托状态

        self.opened = False
        self.closed = False
        self.price = 0.0

        self.lastTick = None

        potSetting ={ 'potsize':10 }
        jumpSetting ={ 'jumpsize':10 }
        lineSetting ={ 'linesize':10 }
        self.pots =   PotGenerator(self.onJumpData, jumpSetting)
        self.jumps =  JumpGenerator(self.onJumpData, jumpSetting)
        self.lines =  LineGenerator(self.onLineData, lineSetting)
        
        self.subscribe(self.vtSymbol)
        self.paramEvent()
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        if( self.lastTick != None ):
            if( tick.lastVolume == 0  ):
                tick.lastVolume = tick.volume - self.lastTick.volume   

        self.jumps.updateTick( tick )  
        self.lines.updateTick( tick )                

        if( tick.lastVolume >= self.totalVolume ):
            msg = u'%s 发现大单，代码：%s， 单量:  %d' %(tick.time, self.vtSymbol,  tick.lastVolume  )
            self.writeLog(msg)
            print msg

            # 生成信号数据
            self.signal.datetime = tick.datetime
            self.signal.date = tick.date
            self.signal.time = tick.time
            self.signal.lastPrice = tick.lastPrice
            self.signal.level = 1
            self.signal.msg = msg
            self.signal.vtSymbol = self.vtSymbol

            self.onSignal()
                        
        self.lastTick =  tick
        # 更新变量
        self.varEvent()         
        return 
 
    #----------------------------------------------------------------------
    def onJumpData(self, jump):
        """"""
        print '%s onJumpData %.1f %d %.1f'%( jump.time, jump.close,jump.type,jump.close-jump.open)
        pass      

    #----------------------------------------------------------------------
    def onLineData(self, line):
        """"""
        print '%s onLineData %.1f %d %.1f'%( line.time, line.close,line.type,line.close-line.open)
        pass     

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
class BigTradeWidget(SignalWidgetTemp): 
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, signalEngine, parent=None):
        """Constructor"""
        print "BigTradeWidget __init__"
        super(BigTradeWidget, self).__init__(signalEngine, parent)        
        self.templateName = BigTradeSignal.templateName
        
        
    #----------------------------------------------------------------------
    def initSignalLayout(self):
        """"""
 
        self.lineSymbol = QtWidgets.QLineEdit()
        
        self.comboDirection = QtWidgets.QComboBox()
        self.comboDirection.addItem(DIRECTION_LONG)
        self.comboDirection.addItem(DIRECTION_SHORT)
        self.comboDirection.setCurrentIndex(0)
        
        self.spinPrice = QtWidgets.QDoubleSpinBox()
        self.spinPrice.setMinimum(0)
        self.spinPrice.setMaximum(1000000000)
        self.spinPrice.setDecimals(8)
        
        self.spinVolume = QtWidgets.QDoubleSpinBox()
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(1000000000)
        self.spinVolume.setDecimals(0)
        
        self.comboOffset = QtWidgets.QComboBox()
        self.comboOffset.addItems(['', OFFSET_OPEN, OFFSET_CLOSE])
        self.comboOffset.setCurrentIndex(0)
        
        self.spinPriceAdd = QtWidgets.QDoubleSpinBox()
        self.spinPriceAdd.setMinimum(0)
        self.spinPriceAdd.setMaximum(1000000000)
        self.spinPriceAdd.setDecimals(8)        
        
        buttonStart = QtWidgets.QPushButton(u'启动')
        buttonStart.clicked.connect(self.addSignal)
        buttonStart.setMinimumHeight(100)
        
        Label = QtWidgets.QLabel
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(u'代码'), 0, 0)
        grid.addWidget(self.lineSymbol, 0, 1)
        # grid.addWidget(Label(u'方向'), 1, 0)
        # grid.addWidget(self.comboDirection, 1, 1)

        # grid.addWidget(Label(u'价格'), 2, 0)
        # grid.addWidget(self.spinPrice, 2, 1)
        grid.addWidget(Label(u'数量'), 3, 0)
        grid.addWidget(self.spinVolume, 3, 1)
        # grid.addWidget(Label(u'开平'), 4, 0)
        # grid.addWidget(self.comboOffset, 4, 1)
        # grid.addWidget(Label(u'超价'), 5, 0)
        # grid.addWidget(self.spinPriceAdd, 5, 1)        
        
        print 'bt. initSignalLayout():',grid
        return grid
    
    #----------------------------------------------------------------------
    def getSignalSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = BigTradeSignal.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        # setting['direction'] = text_type(self.comboDirection.currentText())
        # setting['stopPrice'] = float(self.spinPrice.value())
        setting['totalVolume'] =  (self.spinVolume.value())
        # setting['offset'] = text_type(self.comboOffset.currentText())
        # setting['priceAdd'] = float(self.spinPriceAdd.value())
        
        return setting
    
    
