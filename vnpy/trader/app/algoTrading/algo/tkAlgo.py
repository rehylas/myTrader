# encoding: UTF-8

from __future__ import division
from collections import OrderedDict

from six import text_type

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED)
from vnpy.trader.uiQt import QtWidgets
from vnpy.trader.app.algoTrading.algoTemplate import AlgoTemplate
from vnpy.trader.app.algoTrading.uiAlgoWidget import AlgoWidget, QtWidgets



STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])


########################################################################
class TkAlgo(AlgoTemplate):
    """交易隔夜单算法"""
    """
    1. 根据设置，隔夜做多，做空
    2.14：59分，发送开仓
    3.20:58,发送平仓 无夜盘品种，8:58发平仓
    4.5分钟内无平仓价，则预警
    
    """
    
    templateName = u'Tk 隔夜跳空'

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, algoName):
        """Constructor"""
        super(TkAlgo, self).__init__(engine, setting, algoName)
        
        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])            # 合约代码
        self.direction = text_type(setting['direction'])    # 买卖
        # self.stopPrice = float(setting['stopPrice'])        # 触发价格
        self.totalVolume =  int(setting['totalVolume'])    # 数量
        # self.offset = text_type(setting['offset'])          # 开平
        # self.priceAdd = float(setting['priceAdd'])          # 下单时的超价

        
        self.vtOrderID = ''     # 委托号
        self.tradedVolume = 0   # 成交数量
        self.orderStatus = ''   # 委托状态

        self.opened = False
        self.closed = False
        self.price = 0.0
        
        self.subscribe(self.vtSymbol)
        self.paramEvent()
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """
        1.查时间，如果不是14：59， 和 20：58 , opened = False, closed = False
        2.如果是14：59 and opend=False; 则委托，根据 tkDirection vol , opened = True
        3.如果是20：58 and opend=False; 则委托，根据 tkDirection vol , closed = True
        """

        # initTime = '14:34' 
        # inTime = '14:35' 
        # outTime1 = '14:36' 
        # outTime2 = '14:59' 

        initTime = '14:55' 
        inTime = '14:59' 
        outTime1 = '20:58' 
        outTime2 = '14:59'         

        strTime = tick.time[:5]  #'14:59'     #print strTime
        if( strTime == initTime ):    
            self.opened = False    
            self.closed = False
            return 

        if( strTime == inTime and self.opened == False ):
            if (self.direction == DIRECTION_LONG ):
                func = self.buy
            else:
                func = self.sell  
            self.price    = tick.lastPrice     
            func(self.vtSymbol, self.price,   self.totalVolume , offset= OFFSET_OPEN )     

            self.opened = True
            msg = u'已触发开仓，代码：%s，方向：%s, 价格：%s，数量：%s，开平：%s' %(self.vtSymbol,
                                                                                    self.direction,
                                                                                    tick.lastPrice,
                                                                                    self.totalVolume,
                                                                                    OFFSET_OPEN)
            self.writeLog(msg)
            self.sendAlgoMsg( msg ) 

            # 更新变量
            self.varEvent()              
            return 
            pass
            
 
        if( strTime == outTime1 and self.closed == False ):  
            if (self.direction == DIRECTION_LONG ):
                func = self.sell 
            else:
                func = self.buy   
            
            func(self.vtSymbol, self.price, self.totalVolume, offset= OFFSET_CLOSE )     
 
            self.closed = True
            msg = u'已触发平仓，代码：%s，方向：%s, 价格：%s，数量：%s，开平：%s' %(self.vtSymbol,
                                                                                    self.direction,
                                                                                    tick.lastPrice,
                                                                                    self.totalVolume,
                                                                                    OFFSET_CLOSE)
            self.writeLog(msg)
            self.sendAlgoMsg( msg ) 
            
            # 更新变量
            self.varEvent()        
                    
            return 
            pass

        return 
      
        
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """"""
        self.tradedVolume = order.tradedVolume
        self.orderStatus = order.status
        
        # if self.orderStatus in STATUS_FINISHED:
        #     self.stop()
        
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
        d[u'方向'] = self.direction
        # d[u'触发价格'] = self.stopPrice
        d[u'数量'] = self.totalVolume
        # d[u'开平'] = self.offset
        self.putParamEvent(d)


########################################################################
class TkWidget(AlgoWidget):
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, algoEngine, parent=None):
        """Constructor"""
        super(TkWidget, self).__init__(algoEngine, parent)
        
        self.templateName = TkAlgo.templateName
        
    #----------------------------------------------------------------------
    def initAlgoLayout(self):
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
        buttonStart.clicked.connect(self.addAlgo)
        buttonStart.setMinimumHeight(100)
        
        Label = QtWidgets.QLabel
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(u'代码'), 0, 0)
        grid.addWidget(self.lineSymbol, 0, 1)
        grid.addWidget(Label(u'方向'), 1, 0)
        grid.addWidget(self.comboDirection, 1, 1)

        # grid.addWidget(Label(u'价格'), 2, 0)
        # grid.addWidget(self.spinPrice, 2, 1)
        grid.addWidget(Label(u'数量'), 3, 0)
        grid.addWidget(self.spinVolume, 3, 1)
        # grid.addWidget(Label(u'开平'), 4, 0)
        # grid.addWidget(self.comboOffset, 4, 1)
        # grid.addWidget(Label(u'超价'), 5, 0)
        # grid.addWidget(self.spinPriceAdd, 5, 1)        
        
        return grid
    
    #----------------------------------------------------------------------
    def getAlgoSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = TkAlgo.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        setting['direction'] = text_type(self.comboDirection.currentText())
        # setting['stopPrice'] = float(self.spinPrice.value())
        setting['totalVolume'] =  (self.spinVolume.value())
        # setting['offset'] = text_type(self.comboOffset.currentText())
        # setting['priceAdd'] = float(self.spinPriceAdd.value())
        
        return setting
    
    
