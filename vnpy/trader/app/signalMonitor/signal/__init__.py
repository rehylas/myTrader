# encoding: UTF-8

'''
动态载入所有的监控类
'''
from __future__ import print_function

import os
import importlib
import traceback


# 用来保存算法类和控件类的字典
SIGNAL_DICT = {}
WIDGET_DICT = {}


#----------------------------------------------------------------------
def loadSignalModule(path, prefix):
    """使用importlib动态载入算法"""
    for root, subdirs, files in os.walk(path):
        for name in files:
            # 只有文件名以Signal.py结尾的才是监控类文件
            if len(name)>9 and name[-9:] == 'Signal.py':
                try:
                    # 模块名称需要模块路径前缀
                    moduleName = prefix + name.replace('.py', '')
                    module = importlib.import_module(moduleName)
                    
                    # 获取算法类和控件类
                    signal = None
                    widget = None
 
                    for k in dir(module):
 
                        # 以Signal结尾的类，是算法
                        if k[-6:] == 'Signal':
                            signal = module.__getattribute__(k)
                        
                        # 以Widget结尾的类，是控件
                        if k[-6:] == 'Widget':
                            widget = module.__getattribute__(k)
                    #debug 
                    # print ('loadSignalModule:')
                    # print (signal.templateName)
                    # print (signal,widget)

                    # 保存到字典中
                    if signal and widget:
                        SIGNAL_DICT[signal.templateName] = signal
                        WIDGET_DICT[signal.templateName] = widget
                except:
                    print ('-' * 20)
                    print ('Failed to import strategy file %s:' %moduleName)
                    traceback.print_exc()                       


# 遍历signal目录下的文件
path1 = os.path.abspath(os.path.dirname(__file__))
loadSignalModule(path1, 'vnpy.trader.app.signalMonitor.signal.')

# 遍历工作目录下的文件
path2 = os.getcwd()
loadSignalModule(path2, '')
