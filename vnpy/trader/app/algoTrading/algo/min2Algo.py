# encoding: UTF-8

from __future__ import division
from collections import OrderedDict

from six import text_type

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE, OFFSET_CLOSETODAY,
                                    STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED)
from vnpy.trader.uiQt import QtWidgets
from vnpy.trader.app.algoTrading.algoTemplate import AlgoTemplate
from vnpy.trader.app.algoTrading.uiAlgoWidget import AlgoWidget, QtWidgets



STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])

OS_0 = 0
OS_1 = 1
OS_2 = 2
OS_3 = 3
OS_4 = 4
OS_5 = 5

########################################################################
class Min2Algo(AlgoTemplate):
    """2分钟交易算法"""
    """
    1.即手工开仓，自动出场
    2.选择做多或做空
    3.设置绝对止损 m
    4.如果2分钟内不出现预定的收益 n,则平仓
    5.如果有预期的收益n,则不允许亏损
    6.m x5  或 n x5  止盈
    7.14:58 自动平仓
    """
    
    templateName = u'Min2 时间止损'

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, algoName):
        """Constructor"""
        super(Min2Algo, self).__init__(engine, setting, algoName)
        
        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])            # 合约代码
        self.direction = text_type(setting['direction'])    # 买卖
        # self.stopPrice = float(setting['stopPrice'])        # 触发价格
        self.totalVolume = int(setting['totalVolume'])    # 数量
        # self.offset = text_type(setting['offset'])          # 开平
        # self.priceAdd = float(setting['priceAdd'])          # 下单时的超价
        self.maxFail = float(setting['maxFail'])              # 最大亏损
        self.expectWin = float(setting['expectWin'])          # 短期预期盈利  

        
        self.vtOrderID = ''     # 委托号
        self.tradedVolume = 0   # 成交数量
        self.orderStatus = ''   # 委托状态

        self.winRate = 5
        self.volume = 1
        self.inPrice = 0.0
        self.outPrice = 0.0
        self.state = 0

        self.tempTikCount = 0
        self.tempMaxWin = 0
        self.tempMaxFail = 0
        
        self.subscribe(self.vtSymbol)
        self.paramEvent()
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """
        1.即手工开仓，自动出场
        2.选择做多或做空
        3.设置绝对止损 m
        4.如果2分钟内不出现预定的收益 n,则平仓
        5.如果有预期的收益n,则不允许亏损
        6.m x5  或 n x5  止盈
        7.14:58 自动平仓
        """  
        contract = self.engine.getContract( Min2Algo, self.vtSymbol ) #,'SHFE' 
        # print('contract :' ) 
        # print('contract:', contract )   #contract.priceTick
        # strLog = 'onTick state:', self.state 
        # self.writeLog( strLog )
        

        if( self.state == OS_4 ):
            strLog = 'onTick state:', self.state 
            self.writeLog( strLog )            
            self.stop()
            self.state == OS_5
            return 

        if( self.state == OS_0 ):  #下单
            strLog = 'onTick state:', self.state 
            self.writeLog( strLog )          
            if (self.direction == DIRECTION_LONG ):
                func = self.buy
                self.inPrice    = tick.lastPrice  -1*contract.priceTick
            else:
                func = self.sell  
                self.inPrice    = tick.lastPrice  +1*contract.priceTick
               
            self.vtOrderID = func(self.vtSymbol, self.inPrice , self.totalVolume, offset= OFFSET_OPEN ) 
            strLog = u'sendorder：%s %.1f'%(self.direction, self.inPrice)
            self.writeLog( strLog  )               
            str = 'send order ret :', self.vtOrderID
            self.writeLog( str  )
            self.state = OS_1       
            self.sendAlgoMsg( strLog )
            return 

        if( self.state == OS_1 ):  #

            pass
            return 

        if( self.state == OS_2 ):  # 统计最大亏损，最大盈利，持仓时间
            strLog = 'onTick state: %d %d/%d '%(  self.state , 120-self.tempTikCount, 120) 
      
            self.writeLog( strLog )            
            self.tempTikCount = self.tempTikCount +1
            income = tick.lastPrice - self.inPrice 
            if( self.direction == DIRECTION_SHORT  ):
                income = - income
            if( income > self.tempMaxWin)  :
                self.tempMaxWin = income  
            if( income < self.tempMaxFail)  :
                self.tempMaxFail = income  
            nCheckOut = self.outCheck( income )                   
            if( nCheckOut >= 1 ):
                if (self.direction == DIRECTION_LONG ):
                    func = self.sell
                else:
                    func = self.buy                 
                self.outPrice    = tick.lastPrice    
                if( contract.exchange == 'SHFE' ):   #self.totalVolume
                    func(self.vtSymbol, self.outPrice, self.totalVolume , offset= OFFSET_CLOSETODAY )   
                else:
                    func(self.vtSymbol, self.outPrice, self.totalVolume, offset= OFFSET_CLOSE )       
                self.state = OS_3
                strLog = u'sendorder：%d %s %.1f'%(nCheckOut, OFFSET_CLOSE, self.outPrice)
                self.writeLog( strLog  ) 
                self.sendAlgoMsg( strLog )                 
            return          

        if( self.state == OS_3 ):  # 已经委出
            strLog = 'onTick state:', self.state 
            self.writeLog( strLog )            
            pass
            return             
        return 
      
    #----------------------------------------------------------------------
    def outCheck(self ,income ):
        if( income <=0 and  self.tempMaxWin >= self.expectWin):
            #out now
            strLog = u'出场：盈利归零'
            self.writeLog( strLog  )
            return 1
            pass

        if( self.tempMaxFail <= self.maxFail ):
            #out now
            strLog = u'出场：止损'
            self.writeLog( strLog  )            
            return 2
            pass

        if( self.tempTikCount >= 2*60 ):
            #out now
            strLog = u'出场：时间'
            self.writeLog( strLog  )            
            return 3
            pass

        if( income >= self.winRate*self.expectWin or  income >= self.winRate*(-self.maxFail) ):
            #out now
            strLog = u'出场：盈利'
            self.writeLog( strLog  )                
            return 4
            pass
        return 0

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        self.writeLog( 'onTrade' )
        self.writeLog( trade.orderID )        
        pass
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """"""

        self.writeLog( 'onOrder' )
        self.writeLog( order.status )

        self.tradedVolume = order.tradedVolume
        self.orderStatus = order.status
        
        if( self.state == OS_1 and  STATUS_ALLTRADED == self.orderStatus ):
            self.state = OS_2

        if( self.state == OS_3 and  STATUS_ALLTRADED == self.orderStatus ):
            self.state = OS_4

        if( STATUS_REJECTED == self.orderStatus and self.state == OS_1 ):
            self.stop()
            
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
        d[u'最大亏损'] = self.maxFail
        d[u'预期盈利'] = self.expectWin

 

########################################################################
class TkWidget(AlgoWidget):
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, algoEngine, parent=None):
        """Constructor"""
        super(TkWidget, self).__init__(algoEngine, parent)
        
        self.templateName = Min2Algo.templateName
        
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
        self.spinVolume.setDecimals(1)
        
        self.comboOffset = QtWidgets.QComboBox()
        self.comboOffset.addItems(['', OFFSET_OPEN, OFFSET_CLOSE])
        self.comboOffset.setCurrentIndex(0)
        
        self.spinPriceAdd = QtWidgets.QDoubleSpinBox()
        self.spinPriceAdd.setMinimum(0)
        self.spinPriceAdd.setMaximum(1000000000)
        self.spinPriceAdd.setDecimals(8) 

        self.spinMaxfail = QtWidgets.QDoubleSpinBox()
        self.spinMaxfail.setMinimum(-10000)
        self.spinMaxfail.setMaximum(0)
        self.spinMaxfail.setDecimals(2)     

        self.spinExpectWin = QtWidgets.QDoubleSpinBox()
        self.spinExpectWin.setMinimum(0)
        self.spinExpectWin.setMaximum(10000)
        self.spinExpectWin.setDecimals(2)                    
        
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

        grid.addWidget(Label(u'最大亏损'), 4, 0)
        grid.addWidget(self.spinMaxfail, 4, 1) 

        grid.addWidget(Label(u'预期盈利'), 5, 0)
        grid.addWidget(self.spinExpectWin, 5, 1)         

      
        
        return grid
    
    #----------------------------------------------------------------------
    def getAlgoSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = Min2Algo.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        setting['direction'] = text_type(self.comboDirection.currentText())
        # setting['stopPrice'] = float(self.spinPrice.value())
        setting['totalVolume'] = float(self.spinVolume.value())
        # setting['offset'] = text_type(self.comboOffset.currentText())
        # setting['priceAdd'] = float(self.spinPriceAdd.value())
        setting['maxFail'] = float(self.spinMaxfail.value())
        setting['expectWin'] = float(self.spinExpectWin.value())

        
        return setting
    
    
