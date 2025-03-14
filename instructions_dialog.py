# -*- coding: utf-8 -*-
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea

class InstructionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Doodle Instructions / Doodle 使用说明")
        self.resize(650, 600)  # 增加高度以适应更多行
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建标题标签
        title_label = QLabel("Doodle Plugin Instructions / Doodle 插件使用说明")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 添加使用说明内容 - 英汉双语（上下分行）
        instructions = [
            ("<b>Basic Operations / 基本操作</b>", None),
            ("Enable/Disable Doodle / 启用/禁用 Doodle", 
             ("Press Ctrl+R or select Enable Doodle from the menu to enable or disable the Doodle plugin.", 
              "按下 Ctrl+R 或从菜单中选择 Enable Doodle 选项可以启用或禁用 Doodle 插件。")),
            ("Drawing Mode / 绘图模式", 
             ("Draw on cards using mouse or stylus.", 
              "在卡片上用鼠标或触控笔进行绘图。")),
            ("<b>Tool Buttons / 工具按钮</b>", None),
            ("Free Drawing Tool / 自由绘画工具", 
             ("Default drawing tool, allows drawing free lines.", 
              "默认的绘图工具，可以自由绘制线条。")),
            ("Line Tool / 直线工具", 
             ("Draw straight lines, first click the starting point, then drag to the endpoint and release.", 
              "绘制直线，首先点击起点，然后拖动到终点并释放。")),
            ("Rectangle Tool / 矩形工具", 
             ("Draw rectangles, first click one corner, then drag to the opposite corner and release.", 
              "绘制矩形，首先点击一个角，然后拖动到对角并释放。")),
            ("Highlight Tool / 高亮工具", 
             ("Highlight areas with semi-transparent color.", 
              "使用半透明颜色高亮显示区域。")),
            ("Color Picker / 颜色选择器", 
             ("Select drawing color from preset colors.", 
              "从预设颜色中选择绘图颜色。")),
            ("Eraser / 橡皮擦", 
             ("Erase drawn content.", 
              "擦除已经绘制的内容。")),
            ("Fullscreen Mode / 全屏模式", 
             ("Toggle fullscreen mode to expand drawing area.", 
              "切换全屏模式，扩大绘图区域。")),
            ("Clear Canvas / 清除画布", 
             ("Clear all drawn content.", 
              "清除所有绘制的内容。")),
            ("<b>Settings / 设置选项</b>", None),
            ("Pen Color Settings / 笔颜色设置", 
             ("Select 'Set pen color' from the menu to change drawing color.", 
              "从菜单中选择 Set pen color 可以更改绘图颜色。")),
            ("Pen Width Settings / 笔宽度设置", 
             ("Select 'Set pen width' from the menu to adjust line width.", 
              "从菜单中选择 Set pen width 可以调整线条宽度。")),
            ("Pen Opacity Settings / 笔透明度设置", 
             ("Select 'Set pen opacity' from the menu to adjust line transparency.", 
              "从菜单中选择 Set pen opacity 可以调整线条透明度。")),
            ("Toolbar and Canvas Location Settings / 工具栏和画布位置设置", 
             ("Select 'Toolbar and canvas location settings' from the menu to adjust toolbar position and canvas size.", 
              "从菜单中选择 Toolbar and canvas location settings 可以调整工具栏位置和画布大小。")),
            ("Auto Hide Toolbar / 自动隐藏工具栏", 
             ("Automatically hide toolbar when drawing, can be enabled or disabled in the menu.", 
              "绘图时自动隐藏工具栏，可以在菜单中启用或禁用。")),
            ("Auto Hide Pointer / 自动隐藏指针", 
             ("Automatically hide pointer when drawing, can be enabled or disabled in the menu.", 
              "绘图时自动隐藏指针，可以在菜单中启用或禁用。")),
            ("Follow When Scrolling / 滚动时跟随", 
             ("Canvas follows scrolling of the card, suitable for large cards, can be enabled or disabled in the menu.", 
              "滚动卡片时画布跟随滚动，适合大型卡片，可以在菜单中启用或禁用。")),
            ("Small Canvas by Default / 默认小画布", 
             ("Use a smaller canvas as default setting, can be enabled or disabled in the menu.", 
              "使用较小的画布作为默认设置，可以在菜单中启用或禁用。")),
            ("Zen Mode / 禅模式", 
             ("Hide toolbar until this option is disabled, can be enabled or disabled in the menu.", 
              "隐藏工具栏直到禁用此选项，可以在菜单中启用或禁用。")),
            ("<b>Toolbar Button Display Control / 工具栏按钮显示控制</b>", None),
            ("Toggle Arrows Button / 显示/隐藏箭头按钮", 
             ("Show or hide the arrow tool button.", 
              "显示或隐藏箭头工具按钮。")),
            ("Toggle Line Button / 显示/隐藏直线按钮", 
             ("Show or hide the line tool button.", 
              "显示或隐藏直线工具按钮。")),
            ("Toggle Rectangle Button / 显示/隐藏矩形按钮", 
             ("Show or hide the rectangle tool button.", 
              "显示或隐藏矩形工具按钮。")),
            ("Toggle Highlight Button / 显示/隐藏高亮按钮", 
             ("Show or hide the highlight tool button.", 
              "显示或隐藏高亮工具按钮。")),
            ("Toggle Color Picker Button / 显示/隐藏颜色选择器按钮", 
             ("Show or hide the color picker tool button.", 
              "显示或隐藏颜色选择器工具按钮。")),
            ("Toggle Eraser Button / 显示/隐藏橡皮擦按钮", 
             ("Show or hide the eraser tool button.", 
              "显示或隐藏橡皮擦工具按钮。")),
            ("Toggle Fullscreen Button / 显示/隐藏全屏按钮", 
             ("Show or hide the fullscreen mode button.", 
              "显示或隐藏全屏模式按钮。")),
            ("Toggle Clean Canvas Button / 显示/隐藏清除画布按钮", 
             ("Show or hide the clean canvas button.", 
              "显示或隐藏清除画布按钮。")),
        ]
        
        # 将说明内容添加到布局 - 修改为上下分行显示
        for title, description in instructions:
            # 添加标题
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold;")
            title_label.setWordWrap(True)
            scroll_layout.addWidget(title_label)
            
            # 如果有描述内容，添加英文和中文各占一行
            if description:
                english_text, chinese_text = description
                
                # 英文说明（上面一行）
                english_label = QLabel(english_text)
                english_label.setWordWrap(True)
                english_label.setStyleSheet("margin-left: 20px;")
                scroll_layout.addWidget(english_label)
                
                # 中文说明（下面一行）
                chinese_label = QLabel(chinese_text)
                chinese_label.setWordWrap(True)
                chinese_label.setStyleSheet("margin-left: 20px;")
                scroll_layout.addWidget(chinese_label)
                
                # 添加一点空间，分隔不同项目
                spacer = QWidget()
                spacer.setFixedHeight(10)
                scroll_layout.addWidget(spacer)
        
        # 添加一些空间
        scroll_layout.addStretch()
        
        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # 添加关闭按钮 - 英汉双语
        close_button = QPushButton("Close / 关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

def show_instructions():
    """
    显示Doodle插件的使用说明对话框
    Display instructions dialog for Doodle plugin
    """
    dialog = InstructionsDialog(mw)
    dialog.exec() 