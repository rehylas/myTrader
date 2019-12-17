# encoding: UTF-8

import sys
# vn.trader模块
sys.path.append('..')
sys.path.append('../..')
from vnpy.event import EventEngine

from vnpy.trader.vtObject import *

class CData(object):
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""       
        self.rawData = None                     # 原始数据
        self.val ='dd'

#----------------------------------------------------------------------
def main():
    tik = VtTickData()
    print tik
    print tik.rawData

    dd = CData()
    data = tik.__dict__
    print( data )
    #CData
    pass


if __name__ == '__main__':
    main()

