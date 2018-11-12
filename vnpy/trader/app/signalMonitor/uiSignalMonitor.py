# encoding: UTF-8

import csv
import traceback
from collections import OrderedDict

from six import text_type

from vnpy.event import Event
from vnpy.trader.uiQt import QtCore, QtWidgets

from .signalEngine import (EVENT_SIGNAL_LOG, EVENT_SIGNAL_PARAM, 
                         EVENT_SIGNAL_VAR, EVENT_SIGNAL_SETTING)
from .signal import WIDGET_DICT



########################################################################
class StopButton(QtWidgets.QPushButton):
    """停止信号用按钮"""

    #----------------------------------------------------------------------
    def __init__(self, signalEngine, signalName=''):
        """Constructor"""
        super(StopButton, self).__init__()
        
        self.signalEngine = signalEngine
        self.signalName = signalName
        
        self.setStyleSheet("color:black;background-color:yellow")
        
        if signalName:
            self.setText(u'停止')
            self.clicked.connect(self.stopSignal)
        else:
            self.setText(u'停止全部信号')
            self.clicked.connect(self.stopAll)
    
    #----------------------------------------------------------------------
    def stopSignal(self):
        """停止某一信号"""
        self.signalEngine.stopSignal(self.signalName)
        self.disable()
    
    #----------------------------------------------------------------------
    def stopAll(self):
        """停止全部信号"""
        self.signalEngine.stopAll()
    
    #----------------------------------------------------------------------
    def disable(self):
        """禁用按钮"""
        self.setEnabled(False)
        self.setStyleSheet("color:black;background-color:grey")


SignalCell = QtWidgets.QTableWidgetItem


########################################################################
class SignalStatusMonitor(QtWidgets.QTableWidget):
    """信号状态监控"""
    signalParam = QtCore.Signal(type(Event()))
    signalVar = QtCore.Signal(type(Event()))
    
    MODE_WORKING = 'working'
    MODE_HISTORY = 'history'

    #----------------------------------------------------------------------
    def __init__(self, signalEngine, mode):
        """Constructor"""
        super(SignalStatusMonitor, self).__init__()
        
        self.signalEngine = signalEngine
        self.eventEngine = signalEngine.eventEngine
        self.mode = mode
        
        self.cellDict = {}
        
        self.initUi()
        self.registerEvent()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        labels = [u'',
                  u'名称',
                  u'参数',
                  u'变量']
        
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        self.setAlternatingRowColors(True)
        
        if self.mode == self.MODE_HISTORY:
            self.hideColumn(0)

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signalParam.connect(self.processParamEvent)
        self.signalVar.connect(self.processVarEvent)
        
        self.eventEngine.register(EVENT_SIGNAL_PARAM, self.signalParam.emit)
        self.eventEngine.register(EVENT_SIGNAL_VAR, self.signalVar.emit)
    
    #----------------------------------------------------------------------
    def addSignal(self, signalName):
        """新增信号"""
        self.insertRow(0)
        
        buttonStop = StopButton(self.signalEngine, signalName)
        cellName = SignalCell(signalName)
        cellParam = SignalCell()
        cellVar = SignalCell()
        
        self.setCellWidget(0, 0, buttonStop)
        self.setItem(0, 1, cellName)
        self.setItem(0, 2, cellParam)
        self.setItem(0, 3, cellVar)
        
        self.cellDict[signalName] = {
            'param': cellParam,
            'var': cellVar,
            'button': buttonStop
        }
        
        if self.mode == self.MODE_HISTORY:
            self.hideRow(0)
        
    #----------------------------------------------------------------------
    def processParamEvent(self, event):
        """处理参数事件"""
        d = event.dict_['data']
        
        signalName = d['signalName']
        if signalName not in self.cellDict:
            self.addSignal(signalName)
        
        text = self.generateText(d)
        cell = self.cellDict[signalName]['param']
        cell.setText(text)

        self.resizeColumnsToContents()
        
    #----------------------------------------------------------------------
    def processVarEvent(self, event):
        """处理变量事件"""
        d = event.dict_['data']
        
        signalName = d['signalName']
        if signalName not in self.cellDict:
            self.addSignal(signalName)
            
        if 'active' in d:
            active = d['active']
            
            # 若信号已经结束
            if not active:
                # 禁用按钮
                cells = self.cellDict[signalName]
                button = cells['button']
                button.disable()
                
                # 根据模式决定显示或者隐藏该行
                cell = cells['var']
                row = self.row(cell)
                if self.mode == self.MODE_WORKING:
                    self.hideRow(row)
                else:
                    self.showRow(row)
        
        text = self.generateText(d)
        cell = self.cellDict[signalName]['var']
        cell.setText(text)
        
        self.resizeColumnsToContents()
    
    #----------------------------------------------------------------------
    def generateText(self, d):
        """从字典生成字符串"""
        l = []
        for k, v in d.items():
            if k not in ['signalName']:
                msg = u'%s:%s' %(k, v)
                l.append(msg)
        text = ','.join(l)        
        return text


########################################################################
class SignalLogMonitor(QtWidgets.QTextEdit):
    """"""
    signal = QtCore.Signal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, signalEngine):
        """Constructor"""
        super(SignalLogMonitor, self).__init__()
        
        self.eventEngine = signalEngine.eventEngine
        
        self.registerEvent()
        
    #----------------------------------------------------------------------
    def registerEvent(self):
        """"""
        self.signal.connect(self.processEvent)
        
        self.eventEngine.register(EVENT_SIGNAL_LOG, self.signal.emit)
        
    #----------------------------------------------------------------------
    def processEvent(self, event):
        """"""
        log = event.dict_['data']
        if not log.gatewayName:
            log.gatewayName = u'信号引擎'
        msg = u'%s\t%s：%s' %(log.logTime, log.gatewayName, log.logContent)
        self.append(msg)


########################################################################
class StartButton(QtWidgets.QPushButton):
    """基于配置启动信号用按钮"""

    #----------------------------------------------------------------------
    def __init__(self, signalEngine, setting):
        """Constructor"""
        super(StartButton, self).__init__()
        
        self.signalEngine = signalEngine
        self.setting = setting
        
        self.setStyleSheet("color:black;background-color:green")
        self.setText(u'启动')
        
        self.clicked.connect(self.startSignal)
        
    #----------------------------------------------------------------------
    def startSignal(self):
        """启动信号"""
        self.signalEngine.addSignal(self.setting)
    
    #----------------------------------------------------------------------
    def updateSetting(self, setting):
        """更新配置"""
        self.setting = setting
    

########################################################################
class DeleteButton(QtWidgets.QPushButton):
    """删除信号用按钮"""

    #----------------------------------------------------------------------
    def __init__(self, signalEngine, setting):
        """Constructor"""
        super(DeleteButton, self).__init__()
        
        self.signalEngine = signalEngine
        self.setting = setting
        
        self.setStyleSheet("color:black;background-color:red")
        self.setText(u'删除')
        
        self.clicked.connect(self.deleteSignalSetting)
        
    #----------------------------------------------------------------------
    def deleteSignalSetting(self):
        """删除信号配置"""
        self.signalEngine.deleteSignalSetting(self.setting)
    
    #----------------------------------------------------------------------
    def updateSetting(self, setting):
        """更新配置"""
        self.setting = setting
    

########################################################################
class SignalSettingMonitor(QtWidgets.QTableWidget):
    """"""
    signal = QtCore.Signal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, signalEngine):
        """Constructor"""
        super(SignalSettingMonitor, self).__init__()
        
        self.signalEngine = signalEngine
        self.eventEngine = signalEngine.eventEngine
        
        self.cellDict = {}
        
        self.initUi()
        self.registerEvent()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        labels = ['',
                  '',
                  u'名称',
                  u'信号',
                  u'参数']
        
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)   

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.processEvent)
        
        self.eventEngine.register(EVENT_SIGNAL_SETTING, self.signal.emit)
    
    #----------------------------------------------------------------------
    def processEvent(self, event):
        """处理事件"""
        setting = event.dict_['data']
        settingName = setting['settingName']
        
        # 删除配置行
        if len(setting) == 1:
            d = self.cellDict.pop(settingName)
            cell = d['text']
            row = self.row(cell)
            self.removeRow(row)
        # 新增配置行
        elif settingName not in self.cellDict:
            self.insertRow(0)
        
            buttonStart = StartButton(self.signalEngine, setting)
            buttonDelete = DeleteButton(self.signalEngine, setting)
            cellSettingName = SignalCell(settingName)
            cellTemplateName = SignalCell(setting['templateName'])
            cellSettingText = SignalCell(self.generateText(setting))
            
            self.setCellWidget(0, 0, buttonStart)
            self.setCellWidget(0, 1, buttonDelete)
            self.setItem(0, 2, cellSettingName)
            self.setItem(0, 3, cellTemplateName)
            self.setItem(0, 4, cellSettingText)
            
            self.cellDict[settingName] = {
                'start': buttonStart,
                'template': cellTemplateName,
                'text': cellSettingText,
                'delete': buttonDelete
            }
        # 更新已有配置行
        else:
            d = self.cellDict[settingName]
            d['start'].updateSetting(setting)
            d['template'].setText(setting['templateName'])
            d['text'].setText(self.generateText(setting))
            d['delete'].updateSetting(setting)
        
        self.resizeColumnsToContents()
    
    #----------------------------------------------------------------------
    def generateText(self, d):
        """从字典生成字符串"""
        l = []
        for k, v in d.items():
            if k not in ['settingName', 'templateName', '_id']:
                msg = u'%s:%s' %(k, v)
                l.append(msg)
        text = ','.join(l)
        return text


########################################################################
class SignalMonitorWidget(QtWidgets.QWidget):
    """行情监控管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, signalEngine, eventEngine, parent=None):
        """Constructor"""
        super(SignalMonitorWidget, self).__init__(parent)
        
        self.signalEngine = signalEngine
        self.eventEngine = eventEngine
        
        self.widgetDict = {}
        
        self.initUi()
        self.changeWidget()
        self.signalEngine.loadSignalSetting()   # 界面初始化后，再加载信号配置
        
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(u'信号交易')
        
        #buttonWidth = 400
        #buttonHeight = 60        
        
        self.comboTemplate = QtWidgets.QComboBox()
        #self.comboTemplate.setMaximumWidth(buttonWidth)
        self.comboTemplate.currentIndexChanged.connect(self.changeWidget)
        
        vbox = QtWidgets.QVBoxLayout()
        for templateName, widgetClass in WIDGET_DICT.items():
            widget = widgetClass(self.signalEngine)
            #widget.setMaximumWidth(buttonWidth)
            widget.hide()
            vbox.addWidget(widget)
            
            self.widgetDict[templateName] = widget
            self.comboTemplate.addItem(templateName)
        
        self.buttonStop = StopButton(self.signalEngine)
        
        self.buttonAddSignal = QtWidgets.QPushButton(u'启动篮子信号')
        self.buttonAddSignal.setStyleSheet("color:white;background-color:green")
        self.buttonAddSignal.clicked.connect(self.addSignalFromCsv)
        
        self.buttonSaveSetting = QtWidgets.QPushButton(u'加载信号配置')
        self.buttonSaveSetting.setStyleSheet("color:white;background-color:blue")
        self.buttonSaveSetting.clicked.connect(self.saveSettingFromCsv)
        
        self.lineRepPort = QtWidgets.QLineEdit('8899')
        self.linePubPort = QtWidgets.QLineEdit('9988')
        
        self.buttonStartRpc = QtWidgets.QPushButton(u'启动RPC服务')
        self.buttonStartRpc.setStyleSheet("color:black;background-color:orange")
        self.buttonStartRpc.clicked.connect(self.startRpc)
        
        label = QtWidgets.QLabel(u'信号类型')
        label.setFixedWidth(100)
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.comboTemplate)
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel(u'REP端口'), 0, 0)
        grid.addWidget(self.lineRepPort, 0, 1)
        grid.addWidget(QtWidgets.QLabel(u'PUB端口'), 1, 0)
        grid.addWidget(self.linePubPort, 1, 1)
        
        vbox1 = QtWidgets.QVBoxLayout()
        vbox1.addLayout(hbox)
        vbox1.addLayout(vbox)
        vbox1.addStretch()
        vbox1.addWidget(self.buttonStop)
        vbox1.addWidget(self.buttonAddSignal)
        vbox1.addWidget(self.buttonSaveSetting)
        vbox1.addStretch()
        vbox1.addLayout(grid)
        vbox1.addWidget(self.buttonStartRpc)
        
        workingMonitor = SignalStatusMonitor(self.signalEngine, SignalStatusMonitor.MODE_WORKING)
        workingMonitor.setFixedWidth(1500)
        
        historyMonitor = SignalStatusMonitor(self.signalEngine, SignalStatusMonitor.MODE_HISTORY)
        logMonitor = SignalLogMonitor(self.signalEngine)        
        settingMonitor = SignalSettingMonitor(self.signalEngine)
        
        tab1 = QtWidgets.QTabWidget()
        tab1.addTab(workingMonitor, u'运行中')
        tab1.addTab(historyMonitor, u'已结束')
        
        tab2 = QtWidgets.QTabWidget()
        tab2.addTab(logMonitor, u'日志信息')
        
        tab3 = QtWidgets.QTabWidget()
        tab3.addTab(settingMonitor, u'信号配置')
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(tab2)
        hbox.addWidget(tab3)
        
        vbox2 = QtWidgets.QVBoxLayout()
        vbox2.addWidget(tab1)
        vbox2.addLayout(hbox)
        
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addLayout(vbox1)
        hbox2.addLayout(vbox2)
        
        self.setLayout(hbox2)
    
    #----------------------------------------------------------------------
    def changeWidget(self):
        """"""
        for widget in self.widgetDict.values():
            widget.hide()

        #debug 
        # print 'changeWidget:'
        # print    self.comboTemplate.currentText()

        templateName = text_type(self.comboTemplate.currentText())
        widget = self.widgetDict[templateName]
        widget.show()
    
    #----------------------------------------------------------------------
    def addSignalWidget(self, widgetClass):
        """添加信号控制组件 """
        w = widgetClass(self.signalEngine)
        self.tab.addTab(w, w.templateName)
    
    #----------------------------------------------------------------------
    def loadCsv(self, path):
        """读取CSV配置文件"""
        try:
            with open(text_type(path)) as f:
                buf = [line.encode('UTF-8') for line in f]
            
            reader = csv.DictReader(buf)
            l = []
            
            for d in reader:
                setting = OrderedDict()    
                for name in reader.fieldnames:
                    setting[str(name)] = d[name]
                l.append(setting)
            
            return l
        
        except:
            msg = traceback.format_exc()
            self.signalEngine.writeLog(u'读取CSV文件失败：\n' + msg)
            return []
    
    #----------------------------------------------------------------------
    def saveSettingFromCsv(self):
        """从CSV加载配置到数据库"""
        path, fileType = QtWidgets.QFileDialog.getOpenFileName(self, u'加载信号配置', '', 'CSV(*.csv)')
        l = self.loadCsv(path)
        for setting in l:
            self.signalEngine.saveSignalSetting(setting)
    
    #----------------------------------------------------------------------
    def addSignalFromCsv(self):
        """从CSV启动一篮子信号"""
        path, fileType = QtWidgets.QFileDialog.getOpenFileName(self, u'启动篮子信号', '', 'CSV(*.csv)        ')
        l = self.loadCsv(path)
        for setting in l:
            self.signalEngine.addSignal(setting)
    
    #----------------------------------------------------------------------
    def startRpc(self):
        """启动信号服务"""
        try:
            repPort = int(self.lineRepPort.text())
            pubPort = int(self.linePubPort.text())
        except:
            self.signalEngine.writeLog(u'请检查RPC端口，只能使用整数')
            return
        
        self.signalEngine.startRpc(repPort, pubPort)
    
    #----------------------------------------------------------------------
    def show(self):
        """"""
        self.showMaximized()
        
        
