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

JUMP_TYPE_UP   =  1
JUMP_TYPE_DOWN = -1

########################################################################
class VtJumpData(object):
   
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtJumpData, self).__init__(  )
        self.vtSymbol = EMPTY_STRING
        self.date = EMPTY_STRING                # 日期 20151009
        self.datetime = EMPTY_STRING
        self.time = EMPTY_STRING
        self.endtime = EMPTY_STRING
        self.open = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        self.type = EMPTY_INT
        self.datatype = 'jump'

########################################################################
class JumpGenerator(DataGenerator):
    """
    数据生成器基类
    setting["jumpsize"]
    """

    #----------------------------------------------------------------------
    def __init__(self, onDataGen, setting  ):
        """Constructor"""
        super(JumpGenerator, self).__init__( onDataGen )

        self.oneData = VtJumpData()            #  数据对象
        self.onDataGen = onDataGen             #  数据生成回调函数
        self.dataSet =[]                       #  所有数据
        self.JumpSize = float(setting["jumpsize"])
 
        self.lastTick = None        # 上一TICK缓存对象


    #----------------------------------------------------------------------
    def clearTmepData(self):
        self.oneData = VtJumpData() 
        self.dataSet =[] 
        self.lastTick = None
        pass

    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """TICK更新"""
        """
        根据tick 生成 Jump:
        与上一个比较， 如果价差 大于等于 JumpSize 或者小于等于-JumpSize, 均为一个 Jump
        """
         
        #print tick.lastPrice
        if( self.lastTick == None ):
            self.lastTick  = tick
            return 
        dim = tick.lastPrice - self.lastTick.lastPrice
        # 缓存Tick
        self.lastTick  = tick
       
        if( dim >=  self.JumpSize):
            self.oneData.datetime = tick.datetime
            self.oneData.date = tick.date
            self.oneData.time = tick.time
            self.oneData.close = tick.lastPrice
            self.oneData.open = tick.lastPrice - dim
            self.oneData.type = JUMP_TYPE_UP
            #print 'dim %.1f'%( dim )
            pass


        if( dim <=  -self.JumpSize):
            self.oneData.datetime = tick.datetime
            self.oneData.time = tick.time
            self.oneData.close = tick.lastPrice
            self.oneData.open = tick.lastPrice - dim
            self.oneData.type = JUMP_TYPE_DOWN 
            #print 'dim %.1f'%( dim )           
            pass 

        if( self.oneData.type != EMPTY_INT ):
                self.oneData.vtSymbol = tick.vtSymbol  
                self.oneData.date  = tick.date
                self.dataSet.append( self.oneData )
                self.generate( )     
                self.oneData = VtJumpData()  
                self.oneData.vtSymbol = tick.vtSymbol      

    #----------------------------------------------------------------------
    # def updateBar(self, bar):
    #     pass
 
    #----------------------------------------------------------------------
    def generate(self):
        
        """"""
        self.onDataGen(self.oneData)




