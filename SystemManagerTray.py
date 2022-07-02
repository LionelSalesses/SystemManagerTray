import sys
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QWidgetAction, QMenu, QMessageBox, QAction, QSystemTrayIcon
import PyQt5.QtCore
from Controllers import GfxController, PowerProfileController, CmdExecError
from Theme import iconTheme
from Views import PowerProfileView, GfxModeView


class SystemManagerTray(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        # Check system tray and tray notification are supported
        self.checkSupport()
        
        self.app = app
        
        # Init controllers
        self.initControllers()
        
        # Show tray menu when clicking on tray icon
        self.activated.connect(self.showMenuOnTrigger)
        
        # Set tray icon
        self.icon = QIcon(iconTheme['Tray'])
        self.setIcon(self.icon)
        self.setVisible(True)
        
        # Create menu and add to the tray
        self.menu = self.createMenu(parent=parent)
        self.setContextMenu(self.menu)
        
        self.refresh()
    
    def showMenuOnTrigger(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.contextMenu().popup(QCursor.pos())
    
    def checkSupport(self):
        if not self.isSystemTrayAvailable() or not self.supportsMessages():
            self.notifyError(
                'CRITICAL',
                "System tray is not supported on your system"
            )
    
    def initControllers(self):
        try:
            self.gfxController = GfxController()
            self.powerProfileController = PowerProfileController()
        except CmdExecError as e:
            self.notifyError(
                'CRITICAL',
                "Failed to initialize controllers...<br>"
                "Details: "+e.getMessage()
            )
        print("Controllers initialized")
    
    def notifyError(self, severity, message):
        assert severity in ['ERROR', 'CRITICAL']
        if severity == 'CRITICAL':
            QMessageBox.critical(self.parent(), "System Manager Tray", message)
            sys.exit(1)
        elif severity == 'ERROR':
            QMessageBox.warning(self.parent(), "System Manager Tray", message)
            
    def refresh(self):
        self.powerProfileView.refresh()
        self.gfxModeView.refresh()
        # Send resize event to handle views geometry changing
        resizeEvent = PyQt5.QtGui.QResizeEvent(PyQt5.QtCore.QSize(), self.menu.size())
        self.app.sendEvent(self.menu, resizeEvent)
    
    def redrawMenu(self):
        self.menu.hide()
        self.menu.popup(self.menu.pos())
    
    def createMenuAction(self, menu, actionText, method):
        action = QAction(actionText, menu)
        action.triggered.connect(method)
        menu.addAction(action)
        return action
    
    def widgetToAction(self, parent, widget):
        # Create widget action to insert into the menu
        wAction = QWidgetAction(parent)
        wAction.setDefaultWidget(widget)
        return wAction
    
    def createViews(self, menu):
        # Power profile view
        self.powerProfileView = PowerProfileView(
            self.powerProfileController,
            self.notifyError,
            parent=menu
        )
        menu.addAction(self.widgetToAction(menu, self.powerProfileView))
        
        # Separator
        menu.addSeparator()
        
        # Graphics mode
        self.gfxModeView = GfxModeView(
            self.gfxController,
            self.redrawMenu,
            self.notifyError,
            parent=menu
        )
        menu.addAction(self.widgetToAction(menu, self.gfxModeView))
    
    def createMenu(self, parent=None):
        menu = QMenu(parent)
        menu.setWindowFlags(menu.windowFlags() | PyQt5.QtCore.Qt.FramelessWindowHint)
        menu.setAttribute(PyQt5.QtCore.Qt.WA_TranslucentBackground)
        
        # Power and gfx mode selector views
        self.createViews(menu)
        
        menu.addSeparator()
        
        # Quit action
        self.createMenuAction(menu, "&Quit", self.app.quit)
        
        menu.aboutToShow.connect(self.refresh)
        return menu


