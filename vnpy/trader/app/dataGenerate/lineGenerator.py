# encoding: UTF-8

'''
本文件包含了 line数据类。 尚未完全测试验证
'''
import copy
import sys

sys.path.append('..')
sys.path.append('../..')

from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE, 
                                    EMPTY_FLOAT, EMPTY_INT)

from vnpy.trader.app.dataGenerate.generateDataTemp import DataGenerator

LINE_TYPE_UP   =  1
LINE_TYPE_DOWN = -1

TICK_TYPE_B      =  1
TICK_TYPE_BANK   =  0
TICK_TYPE_S      = -1

########################################################################
class VtLineData(object):
   
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtLineData, self).__init__(  )
        self.datetime = EMPTY_STRING
        self.time = EMPTY_STRING
        self.open = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        self.dim = EMPTY_FLOAT
        self.type = EMPTY_INT
        self.vol = EMPTY_INT

########################################################################
class LineGenerator(DataGenerator):
    """
    数据生成器基类
    """

    #----------------------------------------------------------------------
    def __init__(self, onDataGen, setting  ):
        """Constructor"""
        super(LineGenerator, self).__init__( onDataGen )

        self.oneData = VtLineData()            #  数据对象
        self.onDataGen = onDataGen             #  数据生成回调函数
        self.dataSet =[]                       #  所有数据
        self.LineSize = setting["linesize"]
 
        self.lastTick = None        # 上一TICK缓存对象

    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """TICK更新"""
        """
        根据tick 生成 Line:
        3个以上连续买入
        """
      
        if self.lastTick:
            tick.lastVolume = tick.volume - self.lastTick.volume   # 当前ticK 内的成交量

        if( tick.lastVolume == 0 ):
            return     
        ticktype = TICK_TYPE_BANK
        tick.lastPrice = round( tick.lastPrice,3 )
        if(  tick.lastPrice  <=  tick.bidPrice1     ) :   
            ticktype = TICK_TYPE_S        
        if( tick.lastPrice >= tick.askPrice1    ) :   
            ticktype = TICK_TYPE_B

        #print tick.time, tick.bidPrice1,  tick.lastPrice , tick.askPrice1,ticktype,tick.lastVolume
        # if( ticktype == 0 ):
        #     print tick.__dict__

        #print tick.lastPrice
        if( self.lastTick == None ):
            self.lastTick  = tick
            self.oneData.type  = ticktype
            self.oneData.open  = tick.lastPrice
            return 

 
        # 缓存Tick
        self.lastTick  = tick

        # 延续
        if(ticktype == TICK_TYPE_BANK or ticktype == self.oneData.type ):
            self.oneData.close = tick.lastPrice
            self.oneData.dim = self.oneData.close - self.oneData.open
            self.oneData.vol += tick.lastVolume   
            #return          
            pass

        #print tick.time, self.oneData.dim ,self.LineSize

        if( self.oneData.dim >=  self.LineSize):
            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.close = tick.lastPrice
 
            self.oneData.type = LINE_TYPE_UP
            self.dataSet.append( self.oneData )
            self.generate( )     
            self.oneData = VtLineData()     
            self.oneData.type  = ticktype
            self.oneData.open  = tick.lastPrice  
            return              
            pass


        if( self.oneData.dim <=  -self.LineSize):
            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.close = tick.lastPrice

            self.oneData.type = LINE_TYPE_DOWN    
            self.dataSet.append( self.oneData )
            self.generate( )     
            self.oneData = VtLineData()     
            self.oneData.type  = ticktype
            self.oneData.open  = tick.lastPrice  
            return                     
            pass 

              

        # 断续
        if(ticktype != TICK_TYPE_BANK or ticktype != self.oneData.type ):
            self.oneData.datetime = EMPTY_STRING
            self.oneData.time = EMPTY_STRING
            self.oneData.open = EMPTY_FLOAT
            self.oneData.close = EMPTY_FLOAT
            self.oneData.dim = EMPTY_FLOAT
            self.oneData.type = EMPTY_INT
            self.oneData.vol = EMPTY_INT

            self.oneData.type  = ticktype
            self.oneData.open  = tick.lastPrice

       
            pass


    #----------------------------------------------------------------------
    # def updateBar(self, bar):
    #     pass
 
    #----------------------------------------------------------------------
    def generate(self):
        """"""
        self.onDataGen(self.oneData)




