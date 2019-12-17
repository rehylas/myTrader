# encoding: UTF-8
"""
回测信号扫描，用于 debug 和 信号调优。
"""

from __future__ import division

import sys
sys.path.append('..')
sys.path.append('../..')
from vnpy.trader.app.signalMonitor.signalScaning import SignalScaningEngine 

TICK_DB_NAME = 'MyTrader_Tick_Db'

if __name__ == '__main__':
    
    from vnpy.trader.app.signalMonitor.signal.bigTradeSignal  import BigTradeSignal
    from vnpy.trader.app.signalMonitor.signal.goodPotSignal  import GoodPotSignal
    
    # 创建回测引擎
    engine = SignalScaningEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.TICK_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20181113')
    engine.setEndDate('20181113')
    
    # 设置产品相关参数
    engine.setSize(10)         # 股指合约大小 
    engine.setPriceTick(5)     # 股指最小价格变动
    
    # 设置使用的历史数据库
    engine.setDatabase(TICK_DB_NAME, 'ru1901')
    
    # 在引擎中创建策略对象
    d_goodpot = { 'vtSymbol':'ru1901', "potsize": 25.0, "failval":5.0, "goodval":15.0,  }
    engine.initStrategy(GoodPotSignal, d_goodpot)

    # d_bigtrade = { 'vtSymbol':'ru1901', "totalVolume": 500   }
    # engine.initStrategy(BigTradeSignal, d_bigtrade)
    
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    #engine.showBacktestingResult()