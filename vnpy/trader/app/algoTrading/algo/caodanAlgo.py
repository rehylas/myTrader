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
from vnpy.trader.app.dataGenerate.potGenerator import PotGenerator, POT_TYPE_UP, POT_TYPE_DOWN
 


STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])

OS_0 = 0
OS_1 = 1
OS_2 = 2
OS_3 = 3
OS_4 = 4
OS_5 = 5

########################################################################
class CaodanAlgo(AlgoTemplate):
    """炒蛋交易算法 SR"""
    """
    """
    
    templateName = u'炒蛋算法'
    className = 'CaodanAlgo'
 
    #----------------------------------------------------------------------
    def __init__(self, engine, setting, algoName):
        """Constructor"""
        super(CaodanAlgo, self).__init__(engine, setting, algoName)
        
        self.engine = engine
        potSetting ={ "potsize": setting["potsize"] } 
        self.potGenor = PotGenerator( self.onPotDataGen, potSetting )
        
        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])              # 合约代码
        self.potsize =  int(setting['potsize'])       
  
        self.totalVolume = int(setting['totalVolume'])    # 数量
        self.direction = text_type(setting['direction'])    # 买卖

        
 
 
        self.vtOrderID = ''     # 委托号
        self.tradedVolume = 0   # 成交数量
        self.orderStatus = ''   # 委托状态

        self.goodlook = False
        self.fail = 0.0
        self.win = 0.0
        self.type = 0
        self.state = 0
        self.potPrice = 0.0
        self.tickcount = 0
        self.bsCount = 0
        self.totalIncome = 0

        self.lastTick = None
        
        self.subscribe(self.vtSymbol)

        #debug
        # self.vtOrderID = self.buy(self.vtSymbol, 5090 , 1, offset= OFFSET_OPEN ) 
        # strLog = u'sendorder：%s %.1f'%(self.type, 5090)
        # self.writeLog( strLog  ) 
        # print  strLog

        self.paramEvent()
        self.varEvent()

    
    #----------------------------------------------------------------------
    def onPotDataGen(self, newPotData):
        dl = self.potGenor.dataSet
        n = len(dl)
        if( n  >=2 ):
            Pot = dl[n-2]
            msg = u'%s 新点:  %f, %f, %f, %d' %(Pot.time,  Pot.open, Pot.close, Pot.dim,  Pot.type )
            self.writeLog(msg)
            print msg   
 
        if( self.state !=  OS_0):
            return              

        checked = self.checkIn( newPotData.type ) 
        if( checked == False ):
            
            return  
            pass
          

        #print 'true ******************'            
        #委托入场
        self.tickcount == 0
        if(newPotData.type == POT_TYPE_DOWN):
            self.type = POT_TYPE_UP
            func = self.buy
            self.inPrice    = newPotData.close  
            msg = u'%s Caodan入场，代码：%s， 方向:  %d 点价:%.1f 现价:%.1f' %(newPotData.time, self.vtSymbol,  self.type ,newPotData.close, self.lastTick.lastPrice  )        
            print msg
            pass
        else:
            self.type = POT_TYPE_DOWN
            func = self.sell
            self.inPrice    = newPotData.close   
            msg = u'%s Caodan入场，代码：%s， 方向:  %d 点价:%.1f 现价:%.1f' %(newPotData.time, self.vtSymbol,  self.type ,newPotData.close, self.lastTick.lastPrice  )       
            print msg
            pass
        pass
        self.writeLog(msg)  

        self.vtOrderID = func(self.vtSymbol, self.inPrice , self.totalVolume, offset= OFFSET_OPEN ) 
        strLog = u'sendorder：%s %.1f'%(self.type, self.inPrice)
        self.writeLog( strLog  )               
 
        self.state = OS_1       
        self.sendAlgoMsg( strLog )        
 
        self.state ==  OS_1
        self.tickcount = 0
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        if( self.lastTick != None ):
            if( tick.lastVolume == 0  ):
                tick.lastVolume = tick.volume - self.lastTick.volume            

        self.potGenor.updateTick( tick )
 
        if( self.state == OS_4 ):
            strLog = 'onTick state:', self.state 
            self.writeLog( strLog )            
            self.state == OS_5
            return 

        if( self.state == OS_5 ):
            strLog = 'onTick state:', self.state 
            self.writeLog( strLog )            
            self.state == OS_0
            return             

        if( self.state ==  OS_2 ):
            self.tickcount = self.tickcount +1

        income = (tick.lastPrice - self.potPrice) * self.type
        if( self.tickcount == 120 and self.state ==  OS_2 ):
            msg = u'%s Caodan 时间出场，代码：%s， 方向:  %d %.1f/%.1f 点价:%.1f 现价:%.1f' %(tick.time, self.vtSymbol,  self.type , income, self.totalIncome, self.potPrice, tick.lastPrice  )
            self.writeLog(msg) 
            print msg

            if (self.type == POT_TYPE_UP ):
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

            self.tickcount = 0
            self.goodlook = False
            self.totalIncome =  self.totalIncome +  income
            return                

        

        if( income >= 3 and self.state ==  OS_2 and self.tickcount>=90 ):
            msg = u'%s Caodan 盈利出场，代码：%s， 方向:  %d %.1f/%.1f 点价:%.1f 现价:%.1f' %(tick.time, self.vtSymbol,  self.type , income, self.totalIncome, self.potPrice, tick.lastPrice  )
            self.writeLog(msg) 
            print msg

            if (self.type == POT_TYPE_UP ):
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

            self.tickcount = 0
            self.goodlook = False
            self.totalIncome =  self.totalIncome +  income
            return   
 
        
        self.bsCount = self.bsCount + 1

        self.lastTick =  tick
        # 更新变量
        self.varEvent()         
        return 
 
    #----------------------------------------------------------------------
    def processTik(self, tick):
        # self.goodlook = True
        # self.fail = 0.0
        # self.win = 0.0
        # self.potPrice = newPotData.close
        # self.type = POT_TYPE_UP
 
          
        # if( self.goodlook == False ):
        #     return False
        # win_temp =  (tick.lastPrice -  self.potPrice)*self.type
        # # msg =u'监控价差 %.1f %.1f %.1f' %(win_temp, tick.lastPrice , self.potPrice)

        # if( win_temp >= self.goodval ):  #goodpot
        #     self.goodlook = False
        #     return True

        # if( win_temp < -self.failval ):  #not goodpot
        #     self.goodlook = False
        #     return False

        # return False
        pass 

    #----------------------------------------------------------------------
    def checkIn( self, newPotType ) :
        dl = self.potGenor.dataSet
        n = len(dl)

        #debug
        # if(n>=3):
        #     return True
        #print n
        if( n  <=5 ):
            return False
        newPotData = dl[n-1]
        if( newPotData.type == POT_TYPE_DOWN and self.direction != DIRECTION_LONG ):
            return false   
                     
        if( newPotData.type == POT_TYPE_UP and   self.direction != DIRECTION_SHORT  ):
            return false   

        if(newPotType == POT_TYPE_DOWN):
            if( dl[-1].close >= dl[-3].close  and dl[-3].close >= dl[-5].close and dl[-2].close >= dl[-4].close  ):
                #print '%d True'%(newPotType)
                return True
        else:
            if( dl[-1].close <= dl[-3].close  and dl[-3].close <= dl[-5].close and dl[-2].close <= dl[-4].close  ):
                #print '%d True'%(newPotType)
                return True             
         
        return False
        
        
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onOrder(self, order):

        msg = 'onOrder %s'%(order.status)
        self.writeLog( msg  )
 
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
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeLog(u'算法启动' )
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
class CaodanWidget(AlgoWidget):
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, algoEngine, parent=None):
        """Constructor"""
        super(CaodanWidget, self).__init__(algoEngine, parent)
        
        self.templateName = CaodanAlgo.templateName
        
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
        self.spinVolume.setValue(1)
        
        self.comboOffset = QtWidgets.QComboBox()
        self.comboOffset.addItems(['', OFFSET_OPEN, OFFSET_CLOSE])
        self.comboOffset.setCurrentIndex(0)
        
        self.spinPotsize = QtWidgets.QDoubleSpinBox()
        self.spinPotsize.setMinimum(0)
        self.spinPotsize.setValue(4)
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
        buttonStart.clicked.connect(self.addAlgo)
        buttonStart.setMinimumHeight(100)
        
        Label = QtWidgets.QLabel
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(u'代码'), 0, 0)
        grid.addWidget(self.lineSymbol, 0, 1)

        grid.addWidget(Label(u'点大小'), 1, 0)
        grid.addWidget(self.spinPotsize, 1, 1)  

        grid.addWidget(Label(u'方向'), 2, 0)
        grid.addWidget(self.comboDirection, 2, 1)
 
        grid.addWidget(Label(u'数量'), 3, 0)
        grid.addWidget(self.spinVolume, 3, 1)
 

        return grid
    
    #----------------------------------------------------------------------
    def getAlgoSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = CaodanAlgo.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        setting['potsize'] =  (self.spinPotsize.value())

        setting['totalVolume'] =  int(self.spinVolume.value())   
        setting['direction'] = text_type(self.comboDirection.currentText())   
 
        return setting
    
