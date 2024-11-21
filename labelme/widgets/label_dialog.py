import re

from qtpy import QT_VERSION
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets


import labelme.utils

# from labelme.ai.qwen25 import generate_response
from labelme.logger import logger

QT5 = QT_VERSION[0] == "5"


# TODO(未知):
# - 计算优化的位置以保证不超出屏幕区域。


class LabelQLineEdit(QtWidgets.QLineEdit):
    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)


class LabelDialog(QtWidgets.QDialog):
    def __init__(
        self,
        text="Enter object label",
        parent=None,
        labels=None,
        sort_labels=True,
        show_text_field=True,
        completion="startswith",
        fit_to_content=None,
        flags=None,
    ):
        if fit_to_content is None:
            fit_to_content = {"row": False, "column": True}
        self._fit_to_content = fit_to_content

        super(LabelDialog, self).__init__(parent)
        self.edit = LabelQLineEdit()
        self.edit.setFont(QtGui.QFont("Arial", 14))
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        if flags:
            self.edit.textChanged.connect(self.updateFlags)
        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setFont(QtGui.QFont("Arial", 14))
        self.edit_group_id.setPlaceholderText("Group ID")
        self.edit_group_id.setValidator(
            QtGui.QRegExpValidator(QtCore.QRegExp(r"\d*"), None)
        )
        layout = QtWidgets.QVBoxLayout()
        if show_text_field:
            layout_edit = QtWidgets.QHBoxLayout()
            layout_edit.addWidget(self.edit, 6)
            layout_edit.addWidget(self.edit_group_id, 2)
            layout.addLayout(layout_edit)

        # 添加预定义的标签按钮
        self.buttonLayout = QtWidgets.QHBoxLayout()
        predefined_labels = [
            ("防尘网", "Green Plastic Cover"),
            ("地膜", "Plastic Mulch"),
            ("大棚", "Greenhouse"),
            ("彩钢房", "Color Steel Shed"),
        ]
        for label, english_label in predefined_labels:
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(
                lambda checked, text=english_label: self.setLabel(text)
            )
            self.buttonLayout.addWidget(button)
        layout.addLayout(self.buttonLayout)

        # 标签列表
        self.labelList = QtWidgets.QListWidget()
        self.labelList.setFont(QtGui.QFont("Arial", 14))
        if self._fit_to_content["row"]:
            self.labelList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if self._fit_to_content["column"]:
            self.labelList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._sort_labels = sort_labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.labelList.itemDoubleClicked.connect(self.labelDoubleClicked)
        self.labelList.setFixedHeight(150)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)

        # 添加状态按钮（如“破损”、“完好”）
        self.statusButtonLayout = QtWidgets.QHBoxLayout()
        status_labels = [
            ("严重破损", "severe damage"),
            ("中度破损", "moderate damage"),
            ("轻微破损", "minor damage"),
            ("局部破损", "partial damage"),
            ("完好", "Intact"),
        ]
        for status_label, status_text in status_labels:
            status_button = QtWidgets.QPushButton(status_label)
            status_button.setFont(QtGui.QFont("Arial", 14))
            status_button.clicked.connect(
                lambda checked, desc=status_text: self.setDescription(desc)
            )
            self.statusButtonLayout.addWidget(status_button)
        layout.addLayout(self.statusButtonLayout)

        # self.ai_buttonLayout = QtWidgets.QHBoxLayout()
        # ai_button = QtWidgets.QPushButton("AI填充")
        # ai_button.setFont(QtGui.QFont("Arial", 14))
        # ai_button.clicked.connect(self.setAIFill)
        # self.ai_buttonLayout.addWidget(ai_button)
        # layout.addLayout(self.ai_buttonLayout)

        # 添加标签编辑框
        self.editLayout = QtWidgets.QHBoxLayout()
        self.editLayout.addWidget(self.edit)
        layout.addLayout(self.editLayout)

        # 标签标记
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        layout.addItem(self.flagsLayout)
        self.edit.textChanged.connect(self.updateFlags)
        # 文本编辑
        self.editDescription = QtWidgets.QTextEdit()
        self.editDescription.setFont(QtGui.QFont("Arial", 14))
        self.editDescription.setPlaceholderText("Label description")
        self.editDescription.setFixedHeight(50)
        layout.addWidget(self.editDescription)
        self.setLayout(layout)

        # 按钮
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon("done"))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon("undo"))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        # 自动补全
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != "startswith":
            logger.warn(
                "completion other than 'startswith' is only "
                "supported with Qt5. Using 'startswith'"
            )
            completion = "startswith"
        if completion == "startswith":
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # 默认设置
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == "contains":
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError("Unsupported completion: {}".format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def setLabel(self, text):
        self.edit.setText(text)

    def setDescription(self, description):
        current_description = self.editDescription.toPlainText()
        if current_description:
            self.editDescription.setPlainText(f"{current_description}, {description}")
        else:
            self.editDescription.setPlainText(description)

    # def setAIFill(self):
    #     current_description = self.editDescription.toPlainText()
    #     current_label = self.edit.text()
    #     text = generate_response(
    #         f"影像中的{current_label} is { current_description } ，请用30个字详细描述破损情况。"
    #     )
    #     print(text)
    #     self.editDescription.setPlainText(text)

    def setLabelText(self, text):
        self.edit.setText(text)

    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        self.edit.setText(item.text())

    def validate(self):
        text = self.edit.text()
        if hasattr(text, "strip"):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def labelDoubleClicked(self, item):
        self.validate()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, "strip"):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def updateFlags(self, label_new):
        # 保持共享标记的状态
        flags_old = self.getFlags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(None)

    def resetFlags(self, label=""):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            flags[item.text()] = item.isChecked()
        return flags

    def getGroupId(self):
        group_id = self.edit_group_id.text()
        if group_id:
            return int(group_id)
        return None

    def popUp(self, text=None, move=True, flags=None, group_id=None, description=None):
        if self._fit_to_content["row"]:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content["column"]:
            self.labelList.setMinimumWidth(self.labelList.sizeHintForColumn(0) + 2)
        # 如果 text 为 None，则保留在 self.edit 中的上一个标签
        if text is None:
            text = self.edit.text()
        # 描述始终为空文本，引用自于 self.edit.text
        if description is None:
            description = ""
        self.editDescription.setPlainText(description)
        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        if group_id is None:
            self.edit_group_id.clear()
        else:
            self.edit_group_id.setText(str(group_id))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        if items:
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)
        if move:
            self.move(QtGui.QCursor.pos())
        if self.exec_():
            return (
                self.edit.text(),
                self.getFlags(),
                self.getGroupId(),
                self.editDescription.toPlainText(),
            )
        else:
            return None, None, None, None
