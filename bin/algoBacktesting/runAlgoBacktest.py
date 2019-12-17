# encoding: UTF-8
"""
回测信号扫描，用于 debug 和 信号调优。
"""

from __future__ import division

import sys
sys.path.append('..')
sys.path.append('../..')
from vnpy.trader.app.algoTrading.algoBackTest import AlgoBackEngine 
 

TICK_DB_NAME = 'MyTrader_Tick_Db'

if __name__ == '__main__':
    
 
    from vnpy.trader.app.algoTrading.algo.caodanAlgo  import CaodanAlgo
    
    # 创建回测引擎
    engine = AlgoBackEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.TICK_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20181106')
    engine.setEndDate('20181106')
    
    # 设置产品相关参数
    engine.setSize(10)         # 股指合约大小 
    engine.setPriceTick(1)     # 股指最小价格变动
    
    # 设置使用的历史数据库
    engine.setDatabase(TICK_DB_NAME, 'SR901')
    
    # 在引擎中创建策略对象
    d = { 'vtSymbol':'SR901', "potsize": 4.0, "failtotalVolumeval":1.0, "goodval":1.0,  }
    d_caodan = { 'vtSymbol':'SR901', "potsize": 4.0, "totalVolume":1.0, "direction":u'多',  }
    engine.initStrategy(CaodanAlgo, d_caodan )
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    #engine.showBacktestingResult()