import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime
import requests
import json
import os

class MusicDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('音乐下载器 @微信公众号: 昔尘科技')
        self.setGeometry(100, 100, 800, 600)

        # 创建控件
        self.search_input = QLineEdit(self)
        self.search_button = QPushButton('搜索', self)
        self.result_table = QTableWidget(self)
        self.result_table.setColumnCount(5)  # ID, Title, Author, Cover, Download

        # 设置表头
        header_labels = ["ID", "歌曲标题", "歌手", "封面", "下载"]
        self.result_table.setHorizontalHeaderLabels(header_labels)

        # 设置布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel('请输入歌曲名称:'))
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.result_table)

        # 连接按钮点击事件
        self.search_button.clicked.connect(self.search_music)

    def search_music(self):
        keyword = self.search_input.text()
        if keyword:
            self.worker = Worker(keyword)
            self.worker.result_received.connect(self.show_search_results)
            self.worker.start()

    def show_search_results(self, result):
        self.result_table.setRowCount(0)  # 清空表格内容

        if result and 'data' in result and len(result['data']) > 0:
            for song in result['data']:
                row_position = self.result_table.rowCount()
                self.result_table.insertRow(row_position)

                # 显示歌曲信息
                self.result_table.setItem(row_position, 0, QTableWidgetItem(str(song['songid'])))
                self.result_table.setItem(row_position, 1, QTableWidgetItem(song['title']))
                self.result_table.setItem(row_position, 2, QTableWidgetItem(song['author']))

                # 显示封面
                pixmap = self.get_cover_image(song['pic'])
                label_cover = QLabel(self)
                label_cover.setPixmap(pixmap)
                label_cover.setAlignment(Qt.AlignCenter)
                self.result_table.setCellWidget(row_position, 3, label_cover)

                # 下载按钮
                download_button = QPushButton('下载', self)
                download_button.clicked.connect(lambda _, s=song: self.download_music(s['url'], f"{s['title']}-{s['author']}-{self.get_timestamp()}"))
                self.result_table.setCellWidget(row_position, 4, download_button)

    def download_music(self, url, filename):
        if url:
            self.download_worker = DownloadWorker(url, filename)
            self.download_worker.start()

    def get_cover_image(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            pixmap = self.scale_image(pixmap, 150, 150)  # 调整图片大小
            return pixmap
        else:
            return QPixmap()  # 返回空的 QPixmap，表示没有图像

    def scale_image(self, pixmap, width, height):
        if not pixmap.isNull():
            return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            return QPixmap()

    def get_timestamp(self):
        return QDateTime.currentDateTime().toString('yyyyMMddHHmmss')

class Worker(QThread):
    result_received = pyqtSignal(dict)

    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword

    def run(self):
        result = make_request(self.keyword)
        self.result_received.emit(result)

class DownloadWorker(QThread):
    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        if self.url:
            response = requests.get(self.url)
            if response.status_code == 200:
                if not os.path.exists('PastKing'):
                    os.makedirs('PastKing')
                with open(f'PastKing/{self.filename}.mp3', 'wb') as file:
                    file.write(response.content)

def make_request(keyword):
    url = "https://music.haom.ren/"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    form_data = {"input": keyword, "filter": "name", "type": "netease", "page": "1"}

    try:
        response = requests.post(url, headers=headers, data=form_data)
        response.raise_for_status()
        decoded_json = json.loads(response.text)
        return decoded_json
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    music_downloader = MusicDownloaderApp()
    music_downloader.show()
    sys.exit(app.exec_())
