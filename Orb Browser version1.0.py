import os
import sys
import re
import asyncio
import aiohttp
import threading
import xml.etree.ElementTree as ET
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtCore import QTimer
import yt_dlp

class AdblockX:
    def __init__(self, page, adBlocker):
        self.page = page
        self.block_lists = []
        self.tracker_lists = []
        self.adBlocker = adBlocker
        self.session = aiohttp.ClientSession()

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

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

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.language = "日本語"
        self.tabs = QTabWidget()
        self.memory_saver = MemorySaver(self.tabs)
        self.dark_mode = DarkMode(self.tabs)
        self.load_settings()
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.memory_saver = MemorySaver(self.tabs)
        self.dark_mode = DarkMode(self.tabs)
        self.add_tab_button = QPushButton("")
        self.add_tab_button.setStyleSheet("background-color: black; color: black;")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.vertical_bar = QToolBar("Vertical Bar")
        self.vertical_bar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.vertical_bar)
        self.tabs.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        navtb = QToolBar("Navigation")
        self.addToolBar(navtb)
        self.load_shortcuts()
        back_btn = QAction("↩︎", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)
        next_btn = QAction("↪︎", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)
        reload_btn = QAction("○", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)
        home_btn = QAction("🏠", self)
        home_btn.setStatusTip("Go home")
        self.toolbar = QToolBar("Actions")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.star_button = QAction("⭐️", self)
        self.star_button.setStatusTip("Add shortcut to vertical bar")
        self.star_button.triggered.connect(self.add_shortcut)
        self.toolbar.addAction(self.star_button)
        self.youtube_id_bar = QLineEdit()
        self.youtube_id_bar.setPlaceholderText("YouTube Video ID")
        navtb.addWidget(self.youtube_id_bar)
        self.youtube_id_bar.returnPressed.connect(self.play_youtube_video)
        self.youtube_download_bar = QLineEdit()
        self.youtube_download_bar.setPlaceholderText("youtube download")
        navtb.addWidget(self.youtube_download_bar)
        self.youtube_download_bar.returnPressed.connect(self.download_youtube_video)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)
        navtb.addSeparator()
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)
        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.on_downloadRequested)
        stop_btn = QAction("❌", self)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        navtb.addAction(stop_btn)
        self.add_new_tab(QUrl('https://takerin-123.github.io/qqqqq.github.io/'), 'Homepage')
        self.vertical_bar = QToolBar("Vertical Bar")
        self.vertical_bar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.vertical_bar)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.show()
        self.setWindowTitle("")
        self.setStyleSheet("background-color: black; color: white;")  # 背景色を黒に変更
        self.tabs.setStyleSheet("QTabBar::tab { background-color: white; color: black; }")
        settings_btn = QAction("⚙️", self)
        settings_btn.setStatusTip("設定")
        settings_btn.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_btn)
        self.update_language()
        ai_btn = QAction("AI", self)
        ai_btn.setStatusTip("Use Orb AI")
        ai_btn.triggered.connect(self.open_ai_tool)
        navtb.addAction(ai_btn)
    def open_ai_tool(self):
        ai_url = QUrl("https://supertakerin2-comcomgptfree.hf.space/")
        self.add_new_tab(ai_url, "AI Tool")

    def add_new_tab(self, qurl=None, label="ブランク"):
        if qurl is None:
            qurl = QUrl('https://takerin-123.github.io/qqqqq.github.io/')
        elif isinstance(qurl, str):
            qurl = QUrl(qurl)
        elif not isinstance(qurl, QUrl):
            raise TypeError("qurl must be a QUrl or a string")
        
        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))
        browser.iconChanged.connect(lambda _, i=i, browser=browser: self.tabs.setTabIcon(i, browser.icon()))

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    def current_tab_changed(self, i):
        qurl = self.tabs.currentWidget().url()
        self.update_urlbar(qurl, self.tabs.currentWidget())
        self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)
        QWidget.deleteLater()
    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            return
        title = self.tabs.currentWidget().page().title()
        formatted_title = title[:7] if len(title) > 7 else title.ljust(7)
        self.setWindowTitle("%s OrbBrowser" % formatted_title)
        self.tabs.setTabText(self.tabs.currentIndex(), formatted_title)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl("https://takerin-123.github.io/qqqqq.github.io/"))

    def navigate_to_url(self):
        url = self.urlbar.text()
        if "google.com/search?q=" in url:
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            google_search_url = "https://www.google.com/search?q=" + url
            self.tabs.currentWidget().setUrl(QUrl(google_search_url))

    def update_urlbar(self, q, browser=None):
        if browser != self.tabs.currentWidget():
            return
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def extract_video_id(self, youtube_url):
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
            pass

    def on_downloadRequested(self, download):
        home_dir = os.path.expanduser("~")
        download_dir = os.path.join(home_dir, "Downloads")
        download_filename = download.suggestedFileName()
        QWebEngineProfile.defaultProfile().setDownloadDirectory(download_dir)
        download.setDownloadFileName(download_filename)
        download.accept()
        self.show_download_progress(download)

    def show_download_progress(self, download):
        progress_bar = QProgressBar(self.status)
        self.status.addPermanentWidget(progress_bar)
        download.downloadProgress.connect(lambda bytesReceived, bytesTotal, progress_bar=progress_bar: progress_bar.setValue(int((bytesReceived / bytesTotal) * 100) if bytesTotal > 0 else 0))
        download.finished.connect(lambda progress_bar=progress_bar: progress_bar.deleteLater())

    def update_progress_bar(self, progress_bar, bytesReceived, bytesTotal):
        if bytesTotal > 0:
            progress = (bytesReceived / bytesTotal) * 100
            progress_bar.setValue(int(progress))

    def remove_progress_bar(self, progress_bar):
        self.status.removeWidget(progress_bar)
        progress_bar.deleteLater()

    def download_youtube_video(self):
        youtube_url = self.youtube_download_bar.text()
        video_id = self.extract_video_id(youtube_url)
        if video_id:
            threading.Thread(target=self.download_video, args=(video_id,)).start()
        else:
            pass

    def download_video(self, video_id):
        ydl_opts = {'format': 'mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'http://www.youtube.com/watch?v={video_id}'])

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
            self.save_shortcut_to_xml(title, url)

    def save_shortcut_to_xml(self, title, url):
        if not os.path.exists('shortcuts.xml'):
            root = ET.Element("shortcuts")
            tree = ET.ElementTree(root)
            tree.write('shortcuts.xml')
        tree = ET.parse('shortcuts.xml')
        root = tree.getroot()
        for shortcut in root.findall('shortcut'):
            if shortcut.find('url').text == url:
                print("Bookmark already exists.")
                return
        shortcut = ET.SubElement(root, 'shortcut')
        ET.SubElement(shortcut, 'title').text = title
        ET.SubElement(shortcut, 'url').text = url
        tree.write('shortcuts.xml')

    def load_shortcuts(self):
        if not os.path.exists('shortcuts.xml'):
            return
        tree = ET.parse('shortcuts.xml')
        root = tree.getroot()
        added_urls = set()
        for shortcut in root.findall('shortcut'):
            title = shortcut.find('title').text
            url = shortcut.find('url').text
            if url not in added_urls:
                self.add_website_shortcut(url, title)
                added_urls.add(url)

    def add_website_shortcut(self, url, name):
        name = name[:23] + '...' if len(name) > 23 else name
        shortcut_button = QAction(name, self)
        shortcut_button.url = url
        view = QWebEngineView()
        view.load(QUrl(url))
        view.iconChanged.connect(lambda icon, button=shortcut_button: button.setIcon(icon))
        shortcut_button.triggered.connect(lambda: self.tabs.currentWidget().setUrl(QUrl(url)))
        self.vertical_bar.addAction(shortcut_button)
        self.save_shortcut_to_xml(name, url)

    def create_database(self):
        if not os.path.exists('shortcuts.xml'):
            root = ET.Element("shortcuts")
            tree = ET.ElementTree(root)
            tree.write('shortcuts.xml')

    def show_settings(self):
        settings_dialog = SettingsDialog(self, self.memory_saver, self.dark_mode, self.language)
        settings_dialog.exec()
        self.language = settings_dialog.language
        self.save_settings()
        self.update_language()

    def save_settings(self):
        root = ET.Element("settings")
        tree = ET.ElementTree(root)
        language_element = ET.SubElement(root, "language")
        language_element.text = self.language
        memory_saver_element = ET.SubElement(root, "memory_saver")
        memory_saver_element.text = str(self.memory_saver.memory_saver_enabled)
        dark_mode_element = ET.SubElement(root, "dark_mode")
        dark_mode_element.text = str(self.dark_mode.dark_mode_enabled)
        tree.write("settings.xml")

    def load_settings(self):
        if not os.path.exists("settings.xml"):
            return
        tree = ET.parse("settings.xml")
        root = tree.getroot()
        language_element = root.find("language")
        if language_element is not None:
            self.language = language_element.text
        memory_saver_element = root.find("memory_saver")
        if memory_saver_element is not None:
            self.memory_saver.memory_saver_enabled = bool(memory_saver_element.text)
        dark_mode_element = root.find("dark_mode")
        if dark_mode_element is not None:
            self.dark_mode.dark_mode_enabled = bool(dark_mode_element.text)
        self.update_language()

    def update_language(self):
        if self.language == "日本語":
            self.setWindowTitle("Orb Browser")
        elif self.language == "English":
            self.setWindowTitle("About Orb Browser")
        elif self.language == "中文":
            self.setWindowTitle("关于 Orb Browser")

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
        tree = ET.parse('shortcuts.xml')
        root = tree.getroot()
        for shortcut in root.findall('shortcut'):
            if shortcut.find('url').text == self.url:
                root.remove(shortcut)
                tree.write('shortcuts.xml')
                break
        self.parent().removeAction(self)

class MemorySaver(QObject):
    def __init__(self, tabs):
        super().__init__()
        self.tabs = tabs
        self.tabs.currentChanged.connect(self.save_memory)
        self.memory_saver_enabled = False
        self.last_access_times = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_inactive_tabs)
        self.timer.start(60000)  # 1分ごとにチェック


    def save_memory(self, index):
        if self.memory_saver_enabled:
            current_time = QDateTime.currentDateTime()
            for i in range(self.tabs.count()):
                if i != index:
                    if i not in self.last_access_times:
                        self.last_access_times[i] = current_time
                    self.tabs.widget(i).setVisible(False)
                else:
                    self.last_access_times[i] = current_time
                    self.tabs.widget(i).setVisible(True)
        else:
            for i in range(self.tabs.count()):
                self.tabs.widget(i).setVisible(True)

    def toggle_memory_saver(self, enabled):
        self.memory_saver_enabled = enabled
        self.save_memory(self.tabs.currentIndex())

    def check_inactive_tabs(self):
        if not self.memory_saver_enabled:
            return

        current_time = QDateTime.currentDateTime()
        for i in range(self.tabs.count()):
            if i != self.tabs.currentIndex():
                last_access_time = self.last_access_times.get(i, current_time)
                if last_access_time.secsTo(current_time) > 600:  # 10分以上経過
                    self.tabs.widget(i).setVisible(False)
                else:
                    self.tabs.widget(i).setVisible(True)


    

class DarkMode(QObject):
    def __init__(self, tabs):
        super().__init__()
        self.tabs = tabs
        self.dark_mode_enabled = False

    def toggle_dark_mode(self, enabled):
        self.dark_mode_enabled = enabled
        for i in range(self.tabs.count()):
            web_view = self.tabs.widget(i)
            if enabled:
                web_view.page().setBackgroundColor(Qt.black)
                self.apply_dark_mode_js(web_view)
            
            else:
                web_view.page().setBackgroundColor(Qt.white)
                self.remove_dark_mode_js(web_view)

    def apply_dark_mode_js(self, web_view):
        js_code = """
        document.body.style.backgroundColor = 'black';
        document.body.style.color = 'white';
        """
        web_view.page().runJavaScript(js_code)

    def remove_dark_mode_js(self, web_view):
        js_code = """
        document.body.style.backgroundColor = 'white';
        document.body.style.color = 'black';
        """
        web_view.page().runJavaScript(js_code)


class SettingsDialog(QDialog):
    def __init__(self, parent, memory_saver, dark_mode, language):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.language = language
        self.memory_saver = memory_saver
        self.dark_mode = dark_mode
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        # ダークモードのトグルボタン
        dark_mode_layout = QHBoxLayout()
        dark_mode_toggle = QLabel("ダークモード")
        self.dark_mode_toggle = QCheckBox()
        self.dark_mode_toggle.setChecked(self.dark_mode.dark_mode_enabled)
        self.dark_mode_toggle.toggled.connect(self.dark_mode.toggle_dark_mode)
        dark_mode_layout.addWidget(self.dark_mode_toggle)
        dark_mode_layout.addWidget(self.dark_mode_toggle)
        layout.addLayout(dark_mode_layout)
        self.dark_mode_toggle.setChecked(self.dark_mode.dark_mode_enabled)

        # メモリーセイバーのトグルボタン
        memory_saver_layout = QHBoxLayout()
        memory_saver_toggle = QLabel("メモリーセイバー")
        self.memory_saver_toggle = QCheckBox()
        self.memory_saver_toggle.setChecked(self.memory_saver.memory_saver_enabled)
        self.memory_saver_toggle.toggled.connect(self.memory_saver.toggle_memory_saver)
        memory_saver_layout.addWidget(memory_saver_toggle)
        memory_saver_layout.addWidget(self.memory_saver_toggle)
        layout.addLayout(memory_saver_layout)
        self.memory_saver_toggle.setChecked(self.memory_saver.memory_saver_enabled)

        language_layout = QHBoxLayout()
        language_label = QLabel("言語設定")
        self.language_toggle = QComboBox()
        self.language_toggle.addItems(["日本語", "English", "中文"])
        self.language_toggle.setCurrentText(self.language)
        self.language_toggle.currentTextChanged.connect(self.update_language)
        language_layout.addWidget(self.language_toggle)
        language_layout.addWidget(self.language_toggle)
        layout.addLayout(language_layout)

        # Orb Browserについて
        self.about_layout = QHBoxLayout()
        self.about_label = QLabel("Orb Browserについて")
        self.about_text = QLabel("Orb Browserは、Python と Qt を使って作られた軽量なブラウザです。")
        self.about_layout.addWidget(self.about_label)
        self.about_layout.addWidget(self.about_text)
        layout.addLayout(self.about_layout)

        self.setLayout(layout)

    def update_language(self, language):
        self.language = language
        if language == "日本語":
            self.about_label.setText("Orb Browserについて")
            self.about_text.setText("Orb Browserは、Python と Qt を使って作られた軽量なブラウザです")
            self.setWindowTitle("設定")
            self.dark_mode_toggle.setText("ダークモード")
            self.memory_saver_toggle.setText("メモリーセイバー")
        elif language == "English":
            self.about_label.setText("About Orb Browser")
            self.about_text.setText("Orb Browser is a lightweight and fast web browser developed using Python and QT.")
            self.setWindowTitle("Settings")
            self.dark_mode_toggle.setText("Dark Mode")
            self.memory_saver_toggle.setText("Memory Saver")
        elif language == "中文":
            self.about_label.setText("关于 Orb 浏览器")
            self.about_text.setText("Orb Browser 是一款使用 Python")
            self.setWindowTitle("设置")
            self.dark_mode_toggle.setText("暗模式")
            self.memory_saver_toggle.setText("内存保护器")

app = QApplication(sys.argv)
app.setApplicationName("OrbBrowser")
window = MainWindow()
window.create_database()
window.show()
app.exec()
