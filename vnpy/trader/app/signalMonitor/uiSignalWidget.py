# encoding: UTF-8

from six import text_type

from vnpy.trader.uiQt import QtWidgets


########################################################################
class SignalWidgetTemp(QtWidgets.QFrame): 
    """信号启动组件"""
    
    #----------------------------------------------------------------------
    def __init__(self, signalEngine, parent=None):
        """Constructor"""
        super(SignalWidgetTemp, self).__init__(parent)
        
        self.templateName = ''
        self.signalEngine = signalEngine
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setFrameShape(self.Box)
        print 'initSignalLayout():',self.initSignalLayout
        signalLayout = self.initSignalLayout()
        
        buttonStart = QtWidgets.QPushButton(u'启动监控')
        buttonStart.clicked.connect(self.addSignal)
        buttonStart.setMinimumHeight(100)
        
        buttonSave = QtWidgets.QPushButton(u'保存配置')
        buttonSave.clicked.connect(self.saveSignalSetting)
        buttonSave.setMinimumHeight(100)
        
        self.lineSettingName = QtWidgets.QLineEdit()
        self.lineSettingName.setPlaceholderText(u'监控配置名称')
        
        

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(signalLayout)
        vbox.addWidget(buttonStart)
        vbox.addWidget(QtWidgets.QLabel(''))
        vbox.addWidget(QtWidgets.QLabel(''))
        vbox.addWidget(self.lineSettingName)
        vbox.addWidget(buttonSave)
        
        self.setLayout(vbox)
    
    #----------------------------------------------------------------------
    def addSignal(self):
        """启动信号"""
        setting = self.getSignalSetting()
        self.signalEngine.addSignal(setting)
    
    #----------------------------------------------------------------------
    def saveSignalSetting(self):
        """保存信号配置"""
        setting = self.getSignalSetting()
        setting['templateName'] = self.templateName
        setting['settingName'] = text_type(self.lineSettingName.text())
        self.signalEngine.saveSignalSetting(setting)
        print 'setting:',setting
        '''
        setting: OrderedDict([('templateName', u'Tk \u9694\u591c\u8df3\u7a7a'), ('vtSymbol', 'rb1901'), ('direction', u'\u591a'), ('stopPrice', 0.0), ('totalVolume', 0.0), ('offset', u''), ('priceAdd', 0.0), ('settingName', u'rbtk')])
        '''
        
        self.lineSettingName.setText('')
    
    #----------------------------------------------------------------------
    def initSignalLayout(self):
        """初始化信号相关的组件部分"""
        pass
        
    #----------------------------------------------------------------------
    def getSignalSetting(self):
        """获取信号配置"""
        pass
