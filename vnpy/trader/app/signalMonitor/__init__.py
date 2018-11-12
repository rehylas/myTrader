# encoding: UTF-8

from .signalEngine import SignalEngine
from .uiSignalMonitor import SignalMonitorWidget

appName = 'SignalMonitor'
appDisplayName = u'信号监控'
appEngine = SignalEngine
appWidget = SignalMonitorWidget
appIco = 'cta.ico'