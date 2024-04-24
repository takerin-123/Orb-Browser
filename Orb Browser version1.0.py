from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtPrintSupport import *
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtCore import Qt, QUrl

import os
import sys
import re
import asyncio
import aiohttp
import sqlite3

class AdblockX:
    def __init__(self, page, adBlocker):
        self.page = page
        self.block_lists = []
        self.tracker_lists = []
        self.adBlocker = adBlocker
        self.session = aiohttp.ClientSession()

    async def fetch_lists(self, url):
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch lists: {response.status}")
                return (await response.text()).split('\n')
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    async def update_lists(self):
        block_lists, tracker_lists = await asyncio.gather(
            self.fetch_lists("https://easylist.to/easylist/easylist.txt"),
            self.fetch_lists("https://easylist.to/easylist/easyprivacy.txt")
        )
        if block_lists and block_lists != self.block_lists:
            self.block_lists = block_lists
            await self.blockAds()
        if tracker_lists and tracker_lists != self.tracker_lists:
            self.tracker_lists = tracker_lists
            await self.blockTrackers()

    async def blockAds(self):
        await self.adBlocker.setUrlFilterRules(self.block_lists)

    async def blockTrackers(self):
        await self.adBlocker.setUrlFilterRules(self.tracker_lists)

    async def main(self):
        await self.update_lists()

    async def updateBlockedContent(self, event):
        await self.update_lists()         

# main window
class MainWindow(QMainWindow):
    # constructor
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # creating a vertical bar
        self.vertical_bar = QToolBar("Vertical Bar")
        self.vertical_bar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.vertical_bar)

        # creating a tab widget
        self.tabs = QTabWidget()

        # making document mode true
        self.tabs.setDocumentMode(True)

        # adding action when double clicked
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)

        # adding action when tab is changed
        self.tabs.currentChanged.connect(self.current_tab_changed)

        # making tabs closeable
        self.tabs.setTabsClosable(True)

        # ＋ボタンを追加
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tabs.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # adding action when tab close is requested
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        # making tabs as central widget
        self.setCentralWidget(self.tabs)

        # creating a status bar
        self.status = QStatusBar()

        # setting status bar to the main window
        self.setStatusBar(self.status)

        # creating a tool bar for navigation
        navtb = QToolBar("Navigation")

        # adding tool bar tot he main window
        self.addToolBar(navtb)

        # read "shortcut.db"
        self.load_shortcuts()

        # creating back action
        back_btn = QAction("<", self)

        # setting status tip
        back_btn.setStatusTip("Back to previous page")

        # adding action to back button
        # making current tab to go back
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())

        # adding this to the navigation tool bar
        navtb.addAction(back_btn)

        # similarly adding next button
        next_btn = QAction(">", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        # similarly adding reload button
        reload_btn = QAction("○", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        # creating home action
        home_btn = QAction("ホーム", self)
        home_btn.setStatusTip("Go home")

        # creating a tool bar for actions
        self.toolbar = QToolBar("Actions")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # creating a star button
        self.star_button = QAction("☆", self)
        self.star_button.setStatusTip("Add shortcut to vertical bar")
        self.star_button.triggered.connect(self.add_shortcut)
        self.toolbar.addAction(self.star_button)

        self.youtube_id_bar = QLineEdit()
        self.youtube_id_bar.setPlaceholderText("YouTube Video URL")
        navtb.addWidget(self.youtube_id_bar)
        self.youtube_id_bar.returnPressed.connect(self.play_youtube_video)

        # adding action to home button
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        # adding a separator
        navtb.addSeparator()

        # creating a line edit widget for URL
        self.urlbar = QLineEdit()

        # adding action to line edit when return key is pressed
        self.urlbar.returnPressed.connect(self.navigate_to_url)

        # adding line edit to tool bar
        navtb.addWidget(self.urlbar)

        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.on_downloadRequested)

        # similarly adding stop action
        stop_btn = QAction("X", self)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        navtb.addAction(stop_btn)

        # creating first tab
        self.add_new_tab(QUrl('https://takerin-123.github.io/qqqqq.github.io/'), 'Homepage')

        self.vertical_bar = QToolBar("Vertical Bar")
        self.vertical_bar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.vertical_bar)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # showing all the components
        self.show()

        # setting window title
        self.setWindowTitle("")

    # method for adding new tab
    def add_new_tab(self, qurl = None, label ="ブランク"):
        # if url is blank
        if qurl is None:
            # creating a google url
            qurl = QUrl('https://takerin-123.github.io/qqqqq.github.io/')

        # creating a QWebEngineView object
        browser = QWebEngineView()

        # setting url to browser
        browser.setUrl(qurl)

        # setting tab index
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        # adding action to the browser when url is changed
        # update the url
        browser.urlChanged.connect(lambda qurl, browser = browser: self.update_urlbar(qurl, browser))

        # adding action to the browser when loading is finished
        # set the tab title
        browser.loadFinished.connect(lambda _, i = i, browser = browser: self.tabs.setTabText(i, browser.page().title()))

        # adding action to the browser when icon is changed
        # set the tab icon
        browser.iconChanged.connect(lambda _, i=i, browser=browser: self.tabs.setTabIcon(i, browser.icon()))

    # when double clicked is pressed on tabs
    def tab_open_doubleclick(self, i):
        # checking index i.e
        # No tab under the click
        if i == -1:
            # creating a new tab
            self.add_new_tab()

    # when tab is changed
    def current_tab_changed(self, i):
        # get the curl
        qurl = self.tabs.currentWidget().url()

        # update the url
        self.update_urlbar(qurl, self.tabs.currentWidget())

        # update the title
        self.update_title(self.tabs.currentWidget())

    # when tab is closed
    def close_current_tab(self, i):
        # if there is only one tab
        if self.tabs.count() < 2:
            # do nothing
            return

        # else remove the tab
        self.tabs.removeTab(i)

    # method for updating the title
    def update_title(self, browser):
        # if signal is not from the current tab
        if browser != self.tabs.currentWidget():
            # do nothing
            return

        # get the page title
        title = self.tabs.currentWidget().page().title()

        formatted_title = title[:7] if len(title) > 7 else title.ljust(7)
        self.setWindowTitle("%s OrbBrowser" % formatted_title)
        self.tabs.setTabText(self.tabs.currentIndex(), formatted_title)

        # set the window title
        self.setWindowTitle("% s  OrbBrowser" % title)

    # action to go to home
    def navigate_home(self):
        # go to google
        self.tabs.currentWidget().setUrl(QUrl("https://takerin-123.github.io/qqqqq.github.io/"))

    # method for navigate to url
    def navigate_to_url(self):
        url = self.urlbar.text()
        if "google.com/search?q=" in url:
            # set the url
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            google_search_url = "https://www.google.com/search?q=" + url
            self.tabs.currentWidgets().setUrl(QUrl(google_search_url))

    # method to update the url
    def update_urlbar(self, q, browser = None):
        # If this signal is not from the current tab, ignore
        if browser != self.tabs.currentWidget():
            return

        # set text to the url bar
        self.urlbar.setText(q.toString())

        # set cursor position
        self.urlbar.setCursorPosition(0)

    # YouTubeのURLからビデオIDを抽出する関数 
    def extract_video_id(self,youtube_url):
      # YouTubeのURLパターン
      video_id_pattern = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&?/\s]+)')
      match = video_id_pattern.search(youtube_url)
      if match:
         return match.group(1)
      return None

    def play_youtube_video(self):
        youtube_url = self.youtube_id_bar.text()
        video_id = self.extract_video_id(youtube_url)
        if video_id:
            embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
            self.add_new_tab(QUrl(embed_url), 'YouTube Video')
        else:
            # URLからビデオIDが見つからない場合の処理
            # 例えばエラーメッセージを表示するなど
            pass

    def on_downloadRequested(self, download):
         download_dir = "C:\\Users\\ユーザー名\\Downloads" 
         download_filename = download.suggestedFileName()
         QWebEngineProfile.defaultProfile().setDownloadDirectory(download_dir)
         download.setDownloadFileName(download_filename)
         download.accept()
         self.show_download_progress(download)
 
    def show_download_progress(self, download):
         progress_bar = QProgressBar(self.status)
         self.status.addPermanentWidget(progress_bar)
         download.downloadProgress.connect(lambda bytesReceived, bytesTotal, progress_bar=progress_bar:progress_bar.setValue(int((bytesReceived/bytesTotal) *100) if bytesTotal > 0 else 0))
         download.finished.connect(lambda progress_bar=progress_bar:progress_bar.deleteLater())

    def update_progress_bar(self, progress_bar, bytesReceived, bytesTotal):
        if bytesTotal > 0:
            progress = (bytesReceived / bytesTotal) * 100
            progress_bar.setValue(int(progress))

    def remove_progress_bar(self, progress_bar):
        self.status.removeWidget(progress_bar)
        progress_bar.deleteLater()

    def add_shortcut(self):
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            url = current_tab.page().url().toString()
            title = current_tab.page().title()
            shortcut_button = QAction("", self)
            shortcut_button.setText(current_tab.page().title()) 
            shortcut_button.setToolTip(url)
            shortcut_button.triggered.connect(lambda: self.tabs.currentWidget().setUrl(QUrl(url)))
            self.vertical_bar.addAction(shortcut_button)
            self.tabs.currentWidget().setUrl(QUrl(url))
            #  connect "shortcut.db"
            conn = sqlite3.connect('shortcuts.db')
            c = conn.cursor()

            # Check if the URL already exists in the database
            c.execute("SELECT * FROM shortcuts WHERE url = ?", (url,))
            if c.fetchone() is None:
              # The URL does not exist, so we can add it to the database
              c.execute("INSERT INTO shortcuts VALUES (?, ?)", (title, url))
              conn.commit()
            else:
              # The URL already exists, so we should not add it again
              # Optionally, you can provide user feedback here
              print("Bookmark already exists.")

        # Close the database
        conn.close()
        # save date  using"shortcut.db"
        c.execute("INSERT INTO shortcuts VALUES (?, ?)", (title, url))
        conn.commit()
        # close datebase
        conn.close()

    # read bookmark from ”shortcut.db”
    def load_shortcuts(self):

      #  connect "shortcut.db"
      conn = sqlite3.connect('shortcuts.db')
      c = conn.cursor()

      #  get information from "shortcut.db"
      c.execute("SELECT title, url FROM shortcuts")
      shortcuts = c.fetchall()

      #  close“shortcut.db“
      conn.close()

      # add bookmark to sidebar
      for title, url in shortcuts:

        self.add_website_shortcut(url, title)

    # creating bookmarks for the specified websites
    def add_website_shortcut(self, url, name):
        name = name[:23] + '...'if len(name) > 23 else name
        shortcut_button = QAction(name, self)
        shortcut_button.url = url  # URLをBookmarkActionに保存
        view = QWebEngineView()
        view.load(QUrl(url))
        view.iconChanged.connect(lambda icon, button=shortcut_button: button.setIcon(icon))
        shortcut_button.triggered.connect(lambda: self.tabs.currentWidget().setUrl(QUrl(url)))
        self.vertical_bar.addAction(shortcut_button)
        #  connect“shortcut.db“
        conn = sqlite3.connect('shortcuts.db')
        c = conn.cursor()
        # save information to“shortcut.db“
        c.execute("INSERT INTO shortcuts VALUES (?, ?)", (name, url))
        conn.commit()
        # close“shortcut.db“
        conn.close()

    
    def create_database():
        #  connect“shortcut.db“
        conn = sqlite3.connect('shortcuts.db')

        # get cursor
        c = conn.cursor()

        #  make table
        c.execute('''
            CREATE TABLE IF NOT EXISTS shortcuts
            (title TEXT, url TEXT)
        ''')

        # commit chenging
        conn.commit()

        #  close＂shortcut.db＂
        conn.close()

    create_database()

class BookmarkAction(QAction):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.url = ""

    def showContextMenu(self, point):
        contextMenu = QMenu(self.parent())
        deleteAction = QAction("削除", self)
        deleteAction.triggered.connect(self.deleteBookmark)
        contextMenu.addAction(deleteAction)
        contextMenu.exec_(self.mapToGlobal(point))

    def deleteBookmark(self):
        conn = sqlite3.connect('shortcuts.db')
        c = conn.cursor()
        c.execute("DELETE FROM shortcuts WHERE url = ?", (self.url,))
        conn.commit()
        conn.close()
        self.parent().removeAction(self)  # UIからアクションを削除
    
        
                                                                                                                                                                                                                          
# creating a Pyside6 application
app = QApplication(sys.argv)

# setting name to the application
app.setApplicationName("OrbBrowser")

# creating MainWindow object
window = MainWindow()

# loop
app.exec()