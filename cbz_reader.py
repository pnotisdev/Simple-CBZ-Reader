import os
import zipfile
from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout,
    QProgressBar, QFileDialog, QWidget, QPushButton, QApplication,
    QListWidget, QListWidgetItem, QHBoxLayout, QShortcut,
    QSizePolicy, QAction, QMenu
)
from PyQt5.QtGui import QPixmap, QImage, QKeySequence, QIcon
from PyQt5.QtCore import Qt
from PIL import Image
from io import BytesIO

class CBZReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cbz_files = []
        self.current_index = 0
        self.menu_visible = True

    def initUI(self):
        self.setWindowTitle('Pontus jävla CBZ-läsare')
        self.setGeometry(100, 100, 1200, 800)

        self.file_list = QListWidget()
        self.file_list.setMaximumWidth(300)
        self.file_list.itemClicked.connect(self.openCBZFromList)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self.showContextMenu)

        self.progressBar = QProgressBar(self)
        self.progressBar.setFormat('%p% - Page %v/%m')
        self.progressBar.setInvertedAppearance(True)

        self.openButton = QPushButton('Open Folder', self)
        self.openButton.clicked.connect(self.openFolder)

        self.fullScreenButton = QPushButton('Full Screen', self)
        self.fullScreenButton.clicked.connect(self.toggleFullScreen)

        layout = QHBoxLayout()
        layout.addWidget(self.openButton)
        layout.addWidget(self.fullScreenButton)

        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        vbox.addWidget(self.file_list)

        img_layout = QVBoxLayout()
        img_layout.addWidget(self.label)
        img_layout.addWidget(self.progressBar)

        main_layout = QHBoxLayout()
        main_layout.addLayout(vbox)
        main_layout.addLayout(img_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        QShortcut(QKeySequence('Right'), self, self.prevPage)
        QShortcut(QKeySequence('Left'), self, self.nextPage)
        QShortcut(QKeySequence('Esc'), self, self.toggleFullScreen)
        QShortcut(QKeySequence('Ctrl+H'), self, self.toggleMenuVisibility)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #333;
                color: white;
            }
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #888;
            }
            QProgressBar {
                background-color: #555;
                color: white;
                border: 1px solid #777;
                padding: 1px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QLabel {
                background-color: black;
            }
        """)

        self.saveAction = QAction(QIcon(), 'Save As...', self)
        self.saveAction.triggered.connect(self.saveImage)

        self.copyAction = QAction(QIcon(), 'Copy', self)
        self.copyAction.triggered.connect(self.copyImage)

        self.contextMenu = QMenu(self)
        self.contextMenu.addAction(self.saveAction)
        self.contextMenu.addAction(self.copyAction)

    def openFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if folder_path:
            self.loadFolder(folder_path)

    def loadFolder(self, folder_path):
        self.file_list.clear()
        for file in os.listdir(folder_path):
            if file.lower().endswith('.cbz'):
                item = QListWidgetItem(file)
                item.setData(Qt.UserRole, os.path.join(folder_path, file))
                self.file_list.addItem(item)

    def openCBZFromList(self, item):
        file_path = item.data(Qt.UserRole)
        self.loadCBZ(file_path)

    def loadCBZ(self, file_path):
        with zipfile.ZipFile(file_path, 'r') as cbz:
            self.cbz_files = sorted(
                [file for file in cbz.namelist() if file.lower().endswith(('.png', '.jpg', '.jpeg'))],
                reverse=True
            )
            self.current_index = len(self.cbz_files) - 1
            self.showPage()

    def showPage(self):
        if self.cbz_files:
            file = self.cbz_files[self.current_index]
            with zipfile.ZipFile(self.file_list.currentItem().data(Qt.UserRole), 'r') as cbz:
                data = cbz.read(file)
                image = Image.open(BytesIO(data))
                self.displayImage(image)
            self.updateProgressBar()

    def displayImage(self, image):
        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        q_image = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(q_image)
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def updateProgressBar(self):
        total_pages = len(self.cbz_files)
        current_page = total_pages - self.current_index
        self.progressBar.setMaximum(total_pages)
        self.progressBar.setValue(current_page)

    def nextPage(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.showPage()

    def prevPage(self):
        if self.current_index < len(self.cbz_files) - 1:
            self.current_index += 1
            self.showPage()

    def toggleFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullScreenButton.setText('Full Screen')
        else:
            self.showFullScreen()
            self.fullScreenButton.setText('Exit Full Screen')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.prevPage()
        elif event.key() == Qt.Key_Left:
            self.nextPage()

    def showContextMenu(self, pos):
        self.contextMenu.exec_(self.label.mapToGlobal(pos))

    def saveImage(self):
        if self.label.pixmap():
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
            if file_path:
                pixmap = self.label.pixmap()
                pixmap.save(file_path)

    def copyImage(self):
        if self.label.pixmap():
            clipboard = QApplication.clipboard()
            pixmap = self.label.pixmap()
            clipboard.setPixmap(pixmap)

    def toggleMenuVisibility(self):
        self.menu_visible = not self.menu_visible
        self.file_list.setVisible(self.menu_visible)
        self.openButton.setVisible(self.menu_visible)
        self.fullScreenButton.setVisible(self.menu_visible)
