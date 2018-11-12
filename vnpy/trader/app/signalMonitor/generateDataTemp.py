
# encoding: UTF-8

'''
本文件包含了特殊数据生成的基类，Pot数据类。
'''
import copy

from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE, 
                                    EMPTY_FLOAT, EMPTY_INT)


########################################################################
class DataGenerator(object):
    """
    数据生成器基类
    """

    #----------------------------------------------------------------------
    def __init__(self, onDataCen ):
        """Constructor"""
        self.oneData = None                    #  数据对象
        self.onDataCen = onDataCen             #  数据生成回调函数
        self.dataSet =[]                       #  所有数据
 
        self.lastTick = None        # 上一TICK缓存对象
        
    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """TICK更新"""
        
        if self.lastTick:
            volumeChange = tick.volume - self.lastTick.volume   # 当前K线内的成交量
            self.bar.volume += max(volumeChange, 0)             # 避免夜盘开盘lastTick.volume为昨日收盘数据，导致成交量变化为负的情况
            
        # 缓存Tick
        self.lastTick = tick

    #----------------------------------------------------------------------
    # def updateBar(self, bar):
    #     pass
 
    #----------------------------------------------------------------------
    def generate(self):
        """手动强制立即完成K线合成"""
        self.onDataCen(self.oneData)
        self.bar = None


POT_TYPE_UP   =  1
POT_TYPE_DOWN = -1

########################################################################
class VtPotData(object):
   
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtPotData, self).__init__(  )
        self.datetime = EMPTY_STRING
        self.time = EMPTY_STRING
        self.endtime = EMPTY_STRING
        self.open = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        self.volume = EMPTY_FLOAT
        self.dim = EMPTY_FLOAT
        self.tickcount = EMPTY_INT



########################################################################
class PotGenerator(DataGenerator):
    """
    数据生成器基类
    """

    #----------------------------------------------------------------------
    def __init__(self, onDataGen, setting  ):
        """Constructor"""
        super(PotGenerator, self).__init__( onDataGen )

        self.oneData = VtPotData()             #  数据对象
        self.onDataGen = onDataGen             #  数据生成回调函数
        self.dataSet =[]                       #  所有数据

        self.PotSize = setting["potsize"]
 
        self.lastTick = None        # 上一TICK缓存对象


    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """TICK更新"""
        """
        1. 根据tick 生成 Pot
        """
        #print tick.lastPrice

        
        if self.lastTick:
            tick.lastVolume = tick.volume - self.lastTick.volume   # 当前ticK 内的成交量

        
        if( self.oneData.tickcount ==  EMPTY_INT ): 
            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.endtime = tick.datetime
            self.oneData.open = tick.lastPrice
            self.oneData.close = tick.lastPrice
            self.oneData.volume = tick.lastVolume
            self.oneData.type = POT_TYPE_UP
            self.oneData.dim = 0
            self.oneData.tickcount = 1  
            self.lastTick = tick
            self.dataSet.append( self.oneData )
            self.generate( )
            return           
            pass    
        
        backDim_temp = ( self.oneData.close - tick.lastPrice ) * self.oneData.type
        dim_temp = ( tick.lastPrice - self.oneData.open ) * self.oneData.type
        if( backDim_temp >=  self.PotSize ):   #形成新的点
            # newPot = copy.deepcopy( self.oneData )
            # self.dataSet.append( newPot )
            lastType = self.oneData.type
            lastclose = self.oneData.close
            self.oneData = VtPotData()

            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.endtime = tick.datetime
            self.oneData.open = lastclose
            self.oneData.close = tick.lastPrice 
            self.oneData.volume = tick.lastVolume
            self.oneData.type = lastType*(-1)
            self.oneData.dim = 0
            self.oneData.tickcount = 1  
            self.lastTick = tick
            self.dataSet.append( self.oneData )
            self.generate( )
            
                       
            pass 
        else:    #更新当前的点
            self.oneData.endtime = tick.datetime
            if( dim_temp > self.oneData.dim ):
                self.oneData.close = tick.lastPrice
                self.oneData.dim = dim_temp            
            self.oneData.volume = self.oneData.volume + tick.lastVolume
            self.oneData.tickcount = self.oneData.tickcount + 1  
            self.lastTick = tick            
            pass


        # 缓存Tick
        self.lastTick = tick

    #----------------------------------------------------------------------
    # def updateBar(self, bar):
    #     pass
 
    #----------------------------------------------------------------------
    def generate(self):
        """手动强制立即完成K线合成"""
        self.onDataGen(self.oneData)



