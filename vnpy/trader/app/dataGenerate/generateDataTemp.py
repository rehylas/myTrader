
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

