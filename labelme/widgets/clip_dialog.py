from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QFileDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QProgressBar,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator
from osgeo import gdal
import os


class ClipThread(QThread):
    progress_signal = pyqtSignal(int, int)  # 定义进度信号，传递当前进度和总进度

    def __init__(
        self, input_file, output_prefix, block_width, block_height, overlap_percentage
    ):
        super(ClipThread, self).__init__()
        self.input_file = input_file
        self.output_prefix = output_prefix
        self.block_width = block_width
        self.block_height = block_height
        self.overlap_percentage = overlap_percentage

    def run(self):
        # 执行裁切操作
        self.clip_image(
            self.input_file,
            self.output_prefix,
            self.block_width,
            self.block_height,
            self.overlap_percentage,
        )

    def clip_image(
        self, input_file, output_prefix, block_width, block_height, overlap_percentage
    ):
        if not os.path.exists(output_prefix):
            os.makedirs(output_prefix)
        in_ds = gdal.Open(input_file)
        width = in_ds.RasterXSize
        height = in_ds.RasterYSize
        num = 0

        overlap_width = int(block_width * overlap_percentage / 100)
        overlap_height = int(block_height * overlap_percentage / 100)

        num_cols = width // (block_width - overlap_width)
        num_rows = height // (block_height - overlap_height)
        total_tiles = num_cols * num_rows  # 总裁切块数

        for i in range(num_cols):
            for j in range(num_rows):
                offset_x = i * (block_width - overlap_width)
                offset_y = j * (block_height - overlap_height)

                out_filename = output_prefix + f"./{num:04d}.tiff"

                gdal.Translate(
                    out_filename,
                    in_ds,
                    srcWin=[offset_x, offset_y, block_width, block_height],
                )
                num += 1

                # 发射进度信号
                self.progress_signal.emit(num, total_tiles)

        in_ds = None


class ClipDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(ClipDialog, self).__init__(*args, **kwargs)
        self.image_path = ""
        self.output_path = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("遥感影像分割")

        # 创建用于显示选取的图像路径和输出路径的标签
        self.image_path_label = QLabel("图像路径:")
        self.output_path_label = QLabel("输出路径:")

        # 创建输入框并设置验证器
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Width")
        self.width_input.setValidator(QIntValidator(1, 10000))

        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Height")
        self.height_input.setValidator(QIntValidator(1, 10000))

        self.overlap_input = QLineEdit()
        self.overlap_input.setPlaceholderText("Overlap")
        self.overlap_input.setValidator(QIntValidator(0, 1000))

        # 创建自定义按钮
        button1 = QPushButton("选取影像")
        button1.clicked.connect(self.select_image_path)

        button2 = QPushButton("选取输出路径")
        button2.clicked.connect(self.select_output_path)

        button3 = QPushButton("裁切")
        button3.clicked.connect(self.cut_image)

        # 创建进度条并初始隐藏
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)  # 设置进度条范围 0到100
        self.progress_bar.setValue(0)  # 初始化为0%
        self.progress_bar.setVisible(False)  # 初始时隐藏进度条

        # 创建布局并将标签和按钮添加到布局中
        layout = QVBoxLayout()
        layout.addWidget(self.image_path_label)
        layout.addWidget(self.output_path_label)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.width_input)
        input_layout.addWidget(self.height_input)
        input_layout.addWidget(self.overlap_input)

        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)
        button_layout.addWidget(button3)

        layout.addLayout(button_layout)

        # 添加进度条到布局
        layout.addWidget(self.progress_bar)

        # 设置对话框的布局
        self.setLayout(layout)

    def select_image_path(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self, "选择图像路径", "", "Images (*.tif *.tiff *.png *.jpg *.jpeg)"
        )
        if image_path:
            self.image_path = image_path
            self.image_path_label.setText(f"图像路径: {image_path}")
            print(f"选择的图像路径: {image_path}")

    def select_output_path(self):
        file_dialog = QFileDialog()
        output_path = file_dialog.getExistingDirectory(self, "选择输出路径")

        if output_path:
            self.output_path = output_path
            self.output_path_label.setText(f"输出路径: {output_path}")
            print(f"选择的输出路径: {output_path}")

    def cut_image(self):
        if not self.image_path or not self.output_path:
            print("请先选择图像路径和输出路径")
            return

        tile_width = int(self.width_input.text()) if self.width_input.text() else 0
        tile_height = int(self.height_input.text()) if self.height_input.text() else 0
        overlap = int(self.overlap_input.text()) if self.overlap_input.text() else 0

        if tile_width <= 0 or tile_height <= 0:
            print("请输入有效的宽度和高度")
            return

        print(
            f"裁切参数: 图像路径={self.image_path}, 输出路径={self.output_path}, "
            f"宽度={tile_width}, 高度={tile_height}, 重叠={overlap}"
        )

        # 显示进度条
        self.progress_bar.setVisible(True)

        # 创建并启动裁切线程
        self.clip_thread = ClipThread(
            self.image_path, self.output_path, tile_width, tile_height, overlap
        )
        self.clip_thread.progress_signal.connect(self.update_progress)
        self.clip_thread.start()

    def update_progress(self, current, total):
        # 更新进度条
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        print(f"进度: {progress}%")
