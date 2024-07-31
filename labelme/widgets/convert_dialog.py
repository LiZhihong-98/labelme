from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QFileDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
)
from PyQt5.QtGui import QIntValidator
from labelme.utils.rs import Batch_Convert_tif_to_png


class ConvertDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(ConvertDialog, self).__init__(*args, **kwargs)
        self.image_path = ""
        self.output_path = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Convert TIF to PNG")

        # 创建用于显示选取的图像路径和输出路径的标签
        self.TIF_path_label = QLabel("TIF路径:")
        self.output_path_label = QLabel("PNG路径:")

        # 创建自定义按钮
        button1 = QPushButton("选取TIF")
        button1.clicked.connect(self.select_TIF_path)

        button2 = QPushButton("选取输出PNG路径")
        button2.clicked.connect(self.select_output_path)

        button3 = QPushButton("转换")
        button3.clicked.connect(self.convert_image)

        # 创建布局并将标签和按钮添加到布局中
        layout = QVBoxLayout()
        layout.addWidget(self.TIF_path_label)
        layout.addWidget(self.output_path_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)
        button_layout.addWidget(button3)

        layout.addLayout(button_layout)

        # 设置对话框的布局
        self.setLayout(layout)

    def select_TIF_path(self):
        file_dialog = QFileDialog()
        TIF_path = file_dialog.getExistingDirectory(self, "选择TIF路径")

        if TIF_path:
            self.TIF_path = TIF_path
            self.TIF_path_label.setText(f"输出路径: {TIF_path}")
            print(f"选择的输出路径: {TIF_path}")

    def select_output_path(self):
        file_dialog = QFileDialog()
        output_path = file_dialog.getExistingDirectory(self, "选择PNG输出路径")

        if output_path:
            self.output_path = output_path
            self.output_path_label.setText(f"输出路径: {output_path}")
            print(f"选择的输出路径: {output_path}")

    def convert_image(self):
        if not self.TIF_path or not self.output_path:
            print("请先选择TIF路径和PNG输出路径")
            return

        Batch_Convert_tif_to_png(self.TIF_path, self.output_path)
        self.accept()
