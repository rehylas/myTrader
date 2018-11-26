# encoding: UTF-8

'''
本文件包含了POT数据生成的基类，Pot数据类。
'''
import copy
import sys

sys.path.append('..')
sys.path.append('../..')

from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE, 
                                    EMPTY_FLOAT, EMPTY_INT)

from vnpy.trader.app.dataGenerate.generateDataTemp import DataGenerator

POT_TYPE_UP   =  1
POT_TYPE_DOWN = -1

########################################################################
class VtPotData(object):
   
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtPotData, self).__init__(  )
        self.vtSymbol = EMPTY_STRING
        self.datetime = EMPTY_STRING
        self.date = EMPTY_STRING                # 日期 20151009
        self.time = EMPTY_STRING
        self.endtime = EMPTY_STRING
        self.open = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        self.volume = EMPTY_FLOAT
        self.dim = EMPTY_FLOAT
        self.tickcount = EMPTY_INT
        self.datatype = 'pot'



########################################################################
class PotGenerator(DataGenerator):
    """
    数据生成器基类
    需要 setting["potsize"]
    """

    #----------------------------------------------------------------------
    def __init__(self, onDataGen, setting  ):
        """Constructor"""   
        super(PotGenerator, self).__init__( onDataGen )

        self.oneData = VtPotData()             #  数据对象
        self.onDataGen = onDataGen             #  数据生成回调函数
        self.dataSet =[]                       #  所有数据

        self.PotSize = setting["potsize"]
        #debug
        # print '----------------------------------------------'
        # print 'potsize:', self.PotSize
        # print '----------------------------------------------'
 
        self.lastTick = None        # 上一TICK缓存对象

    #----------------------------------------------------------------------
    def clearTmepData(self):
        self.oneData = VtPotData() 
        self.dataSet =[] 
        self.lastTick = None
        pass

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
            self.oneData.vtSymbol = tick.vtSymbol 
            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.endtime = tick.time
            self.oneData.open = tick.lastPrice
            self.oneData.close = tick.lastPrice
            self.oneData.volume = tick.lastVolume
            self.oneData.type = POT_TYPE_UP
            self.oneData.dim = 0
            self.oneData.tickcount = 1  
            self.datatype = 'pot'
            self.lastTick = tick
            self.oneData.date  = tick.date
            self.dataSet.append( self.oneData )
            #self.generate( )
            return           
            pass    
        
        backDim_temp = ( self.oneData.close - tick.lastPrice ) * self.oneData.type
        dim_temp =     ( tick.lastPrice - self.oneData.open  ) * self.oneData.type
        if( backDim_temp >=  self.PotSize ):   #形成新的点

            #debug
            # print '----------------------------------------------'
            # print 'potsize:', self.PotSize
            # print 'type,close,newpirce,dim, backdim ', self.oneData.type,self.oneData.close,tick.lastPrice, self.oneData.dim, backDim_temp
            # print '----------------------------------------------'

            # newPot = copy.deepcopy( self.oneData )
            # self.dataSet.append( newPot )
            lastType = self.oneData.type
            lastclose = self.oneData.close
            self.oneData = VtPotData()
            self.oneData.vtSymbol = tick.vtSymbol 
            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.endtime = tick.time
            self.oneData.open = lastclose
            self.oneData.close = tick.lastPrice 
            self.oneData.volume = tick.lastVolume
            self.oneData.type = lastType*(-1)
            self.oneData.dim = self.oneData.close - self.oneData.open
            self.oneData.tickcount = 1  
            self.datatype = 'pot'
            self.lastTick = tick
            self.oneData.date  = tick.date
            self.dataSet.append( self.oneData )
            self.generate( )
            
                       
            pass 
        else:    #更新当前的点
            # #debug
            # print '----------------------------------------------'
            # print 'type,close,newpirce,dim, backdim ', self.oneData.type,self.oneData.close,tick.lastPrice, self.oneData.dim, backDim_temp
            # print '----------------------------------------------'

            self.oneData.endtime = tick.time
            if( tick.lastPrice > self.oneData.close and self.oneData.type == POT_TYPE_UP ):
                self.oneData.close = tick.lastPrice
                self.oneData.dim = dim_temp       
            if( tick.lastPrice < self.oneData.close and self.oneData.type == POT_TYPE_DOWN ):
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
    def generate(self, lastData = False):
        """手动强制立即完成K线合成"""
        if( lastData == True ):
            self.onDataGen( self.oneData )  
        else:
            if( len(self.dataSet) >=2 ):
                self.onDataGen( self.dataSet[-2] )   #self.oneData
                overPot = self.dataSet[-2]
                #debug
                # print '----------------------------------------------'
                # print 'potsize:', self.PotSize
                # print 'type,close, ,dim  ', overPot.type, overPot.open, overPot.close , overPot.dim 
                # print '----------------------------------------------'
            pass

        




