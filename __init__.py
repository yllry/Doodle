# -*- coding: utf-8 -*-
# Copyright: Michal Krassowski <krassowski.michal@gmail.com>
# Copyright: Rytis Petronis <petronisrytis@gmail.com>
# Copyright: Louis Liu <liury2015@outlook.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
This addon is modified based on the AnkiDraw plugin.
Modified by Louis <liury2015@outlook.com>

Initially based on the Anki-TouchScreen addon, updated ui and added pressure pen/stylus capabilities, perfect freehand(line smoothing) and calligrapher functionality.


    It Added
    Rectangle Tool
    Line Tool
    Eraser Tool
    Highlight Tool
    Color Picker Tool.
    Resizing Options

If you want to contribute visit GitHub page: https://github.com/Rytisgit/Anki-StylusDraw
Also, feel free to send me bug reports or feature requests.

Copyright: Michal Krassowski <krassowski.michal@gmail.com>
Copyright: Rytis Petronis <petronisrytis@gmail.com>
Copyright: Louis <liury2015@outlook.com>
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html,
Important parts of Javascript code inspired by http://creativejs.com/tutorials/painting-with-pixels/index.html
"""

__addon_name__ = "Doodle"
__version__ = "1.0"

from aqt import mw
from aqt.utils import showWarning
from aqt import gui_hooks

from anki.lang import _
from anki.hooks import addHook

from aqt.qt import QAction, QMenu, QColorDialog, QMessageBox, QInputDialog, QLabel,\
   QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QSpinBox, QCheckBox, QGridLayout, QToolButton, QWidget
from aqt.qt import QKeySequence,QColor
from aqt.qt import pyqtSlot as slot

# 导入instructions_dialog模块
try:
    from . import instructions_dialog
except ImportError:
    import instructions_dialog

# This declarations are there only to be sure that in case of troubles
# with "profileLoaded" hook everything will work.

ts_state_on = False
ts_profile_loaded = False
ts_auto_hide = True
ts_auto_hide_pointer = True
ts_default_small_canvas = False
ts_zen_mode = False
ts_follow = False
ts_ConvertDotStrokes = True

ts_color = "#272828"
ts_line_width = 4
ts_opacity = 0.7
ts_location = 1
ts_x_offset = 0
ts_y_offset = 0
ts_small_width = 500
ts_small_height = 500
ts_background_color = "#FFFFFF00"
ts_orient_vertical = True
ts_default_review_html = mw.reviewer.revHtml

# Define error message constant
TS_ERROR_NO_PROFILE = "Doodle: No profile loaded"

ts_default_VISIBILITY = "true"
ts_default_PerfFreehand = "false"
ts_default_Calligraphy = "false"

@slot()
def ts_change_color():
    """
    Open color picker and set chosen color to text (in content)
    """
    global ts_color
    qcolor_old = QColor(ts_color)
    qcolor = QColorDialog.getColor(qcolor_old)
    if qcolor.isValid():
        ts_color = qcolor.name()
        execute_js("color = '" + ts_color + "';")
        execute_js("if (typeof updateToolColor === 'function') { updateToolColor('" + ts_color + "'); }")
        execute_js("if (typeof reapplyErasedAreas === 'function') { reapplyErasedAreas(); }")


@slot()
def ts_change_width():
    global ts_line_width
    value, accepted = QInputDialog.getDouble(
        mw, 
        "Doodle", 
        "Enter the width (minimum 0.1):", 
        float(ts_line_width),  # 确保转换为float
        0.1,            
        100.0,          
        1               
    )
    
    if accepted:
        if value < 0.1:
            value = 0.1
            
        ts_line_width = value
        execute_js("line_width = " + str(ts_line_width) + ";")
        execute_js("if (typeof update_pen_settings === 'function') { update_pen_settings(); }")
        execute_js("if (typeof reapplyErasedAreas === 'function') { reapplyErasedAreas(); }")


@slot()
def ts_change_opacity():
    global ts_opacity
    value, accepted = QInputDialog.getDouble(mw, "Doodle", "Enter the opacity (0 = transparent, 100 = opaque):", 100 * ts_opacity, 0, 100, 2)
    if accepted:
        ts_opacity = value / 100
        execute_js("canvas.style.opacity = " + str(ts_opacity))


class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Doodle Toolbar And Canvas")

        self.combo_box = QComboBox()
        self.combo_box.addItem("Top-Left")
        self.combo_box.addItem("Top-Right")
        self.combo_box.addItem("Bottom-Left")
        self.combo_box.addItem("Bottom-Right")

        combo_label = QLabel("Location:")

        range_label = QLabel("Offset:")

        start_range_label = QLabel("X Offset:")
        self.start_spin_box = QSpinBox()
        self.start_spin_box.setRange(0, 1000)

        small_width_label = QLabel("Non-Fullscreen Canvas Width:")
        self.small_width_spin_box = QSpinBox()
        self.small_width_spin_box.setRange(0, 9999)

        small_height_label = QLabel("Non-Fullscreen Canvas Height:")
        self.small_height_spin_box = QSpinBox()
        self.small_height_spin_box.setRange(0, 9999)

        end_range_label = QLabel("Y Offset:")
        self.end_spin_box = QSpinBox()
        self.end_spin_box.setRange(0, 1000)

        range_layout = QVBoxLayout()

        small_height_layout = QHBoxLayout()
        small_height_layout.addWidget(small_height_label)
        small_height_layout.addWidget(self.small_height_spin_box)

        small_width_layout = QHBoxLayout()
        small_width_layout.addWidget(small_width_label)
        small_width_layout.addWidget(self.small_width_spin_box)

        color_layout = QHBoxLayout()
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.select_color)

        self.color_label = QLabel("Background color: #FFFFFF00")  # Initial color label

        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)
        

        

        start_layout = QHBoxLayout()
        start_layout.addWidget(start_range_label)
        start_layout.addWidget(self.start_spin_box)

        end_layout = QHBoxLayout()
        end_layout.addWidget(end_range_label)
        end_layout.addWidget(self.end_spin_box)
        range_layout.addLayout(start_layout)
        range_layout.addLayout(end_layout)
        range_layout.addLayout(small_width_layout)
        range_layout.addLayout(small_height_layout)
        

        checkbox_label2 = QLabel("Orient vertically:")
        self.checkbox2 = QCheckBox()

        checkbox_layout2 = QHBoxLayout()
        checkbox_layout2.addWidget(checkbox_label2)
        checkbox_layout2.addWidget(self.checkbox2)

        accept_button = QPushButton("Accept")
        cancel_button = QPushButton("Cancel")
        reset_button = QPushButton("Default")

        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_to_default)

        button_layout = QHBoxLayout()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(cancel_button)
        

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(combo_label)
        dialog_layout.addWidget(self.combo_box)
        dialog_layout.addWidget(range_label)
        dialog_layout.addLayout(range_layout)
        dialog_layout.addLayout(checkbox_layout2)
        dialog_layout.addLayout(color_layout)
        dialog_layout.addLayout(button_layout)
        
        self.setLayout(dialog_layout)

    def set_values(self, combo_index, start_value, end_value, checkbox_state2, width, height, background_color):
        self.combo_box.setCurrentIndex(combo_index)
        self.start_spin_box.setValue(start_value)
        self.small_height_spin_box.setValue(height)
        self.small_width_spin_box.setValue(width)
        self.end_spin_box.setValue(end_value)
        self.checkbox2.setChecked(checkbox_state2)
        self.color_label.setText(f"Background color: {background_color}")

    def reset_to_default(self):
        self.combo_box.setCurrentIndex(1)
        self.start_spin_box.setValue(0)
        self.end_spin_box.setValue(0)
        self.small_height_spin_box.setValue(500)
        self.small_width_spin_box.setValue(500)
        self.checkbox2.setChecked(True)
        self.color_label.setText("Background color: #FFFFFF00")  # Reset color label

    def select_color(self):
        color_dialog = QColorDialog()
        qcolor_old = QColor(self.color_label.text()[-9:-2])
        color = color_dialog.getColor(qcolor_old, options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.color_label.setText(f"Background color: {(color.name()+color.name(QColor.NameFormat.HexArgb)[1:3]).upper()}")  # Update color label

def get_css_for_toolbar_location(location, x_offset, y_offset, orient_column, canvas_width, canvas_height, background_color):
    orient = "column" if orient_column else "row"
    # 使用正偏移来将工具栏适当贴近边缘但不被遮挡
    x_offset_actual = 8 + x_offset  # 更新为8
    y_offset_actual = 8 + y_offset  # 更新为8，使工具栏不被遮挡
    
    # 为不同位置设置不同的transform-origin
    transform_origin = ""
    if location == 0:  # 左上角
        transform_origin = "transform-origin: 0 0;"
    elif location == 1:  # 右上角
        transform_origin = "transform-origin: 100% 0;"
    elif location == 2:  # 左下角
        transform_origin = "transform-origin: 0 100%;"
    elif location == 3:  # 右下角
        transform_origin = "transform-origin: 100% 100%;"
    else:
        transform_origin = "transform-origin: 0 0;"
    
    switch = {
        0: f"""
                        --button-bar-pt: {y_offset_actual}px;
                        --button-bar-pr: unset;
                        --button-bar-pb: unset;
                        --button-bar-pl: {x_offset_actual}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                        --transform-origin: 0 0;
                    """,
        1: f"""
                        --button-bar-pt: {y_offset_actual}px;
                        --button-bar-pr: {x_offset_actual}px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                        --transform-origin: 100% 0;
                    """,
        2: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: unset;
                        --button-bar-pb: {y_offset_actual}px;
                        --button-bar-pl: {x_offset_actual}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                        --transform-origin: 0 100%;
                    """,
        3: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: {x_offset_actual}px;
                        --button-bar-pb: {y_offset_actual}px;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                        --transform-origin: 100% 100%;
                    """,
    }
    return switch.get(location, """
                        --button-bar-pt: 8px;
                        --button-bar-pr: 8px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: column;
                        --small-canvas-height: 500;
                        --small-canvas-width: 500;
                        --background-color: #FFFFFF00;
                        --transform-origin: 0 0;
                    """) + transform_origin

def get_css_for_auto_hide(auto_hide, zen):
    return "none" if auto_hide or zen else "flex"

def get_css_for_zen_mode(hide):
    return "none" if hide else "flex"

def get_css_for_auto_hide_pointer(auto_hide):
    return "none" if auto_hide else "default"

@slot()
def ts_change_toolbar_settings():
    global ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color
    
    dialog = CustomDialog()
    dialog.set_values(ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color) 
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        ts_location = dialog.combo_box.currentIndex()
        ts_x_offset = dialog.start_spin_box.value()
        ts_y_offset = dialog.end_spin_box.value()
        ts_small_height = dialog.small_height_spin_box.value()
        ts_background_color = dialog.color_label.text()[-9:]
        ts_small_width = dialog.small_width_spin_box.value()
        ts_orient_vertical = dialog.checkbox2.isChecked()
        
        # 直接更新CSS变量以立即显示效果
        if ts_state_on:
            x_offset_actual = 8 + ts_x_offset
            y_offset_actual = 8 + ts_y_offset
            css_update = ""
            transform_origin = ""
            
            if ts_location == 0:  # 左上角
                css_update = f"""
                document.documentElement.style.setProperty('--button-bar-pt', '{y_offset_actual}px');
                document.documentElement.style.setProperty('--button-bar-pr', 'unset');
                document.documentElement.style.setProperty('--button-bar-pb', 'unset');
                document.documentElement.style.setProperty('--button-bar-pl', '{x_offset_actual}px');
                document.documentElement.style.setProperty('--transform-origin', '0 0');
                document.getElementById('pencil_button_bar').style.transformOrigin = '0 0';
                """
            elif ts_location == 1:  # 右上角
                css_update = f"""
                document.documentElement.style.setProperty('--button-bar-pt', '{y_offset_actual}px');
                document.documentElement.style.setProperty('--button-bar-pr', '{x_offset_actual}px');
                document.documentElement.style.setProperty('--button-bar-pb', 'unset');
                document.documentElement.style.setProperty('--button-bar-pl', 'unset');
                document.documentElement.style.setProperty('--transform-origin', '100% 0');
                document.getElementById('pencil_button_bar').style.transformOrigin = '100% 0';
                """
            elif ts_location == 2:  # 左下角
                css_update = f"""
                document.documentElement.style.setProperty('--button-bar-pt', 'unset');
                document.documentElement.style.setProperty('--button-bar-pr', 'unset');
                document.documentElement.style.setProperty('--button-bar-pb', '{y_offset_actual}px');
                document.documentElement.style.setProperty('--button-bar-pl', '{x_offset_actual}px');
                document.documentElement.style.setProperty('--transform-origin', '0 100%');
                document.getElementById('pencil_button_bar').style.transformOrigin = '0 100%';
                """
            elif ts_location == 3:  # 右下角
                css_update = f"""
                document.documentElement.style.setProperty('--button-bar-pt', 'unset');
                document.documentElement.style.setProperty('--button-bar-pr', '{x_offset_actual}px');
                document.documentElement.style.setProperty('--button-bar-pb', '{y_offset_actual}px');
                document.documentElement.style.setProperty('--button-bar-pl', 'unset');
                document.documentElement.style.setProperty('--transform-origin', '100% 100%');
                document.getElementById('pencil_button_bar').style.transformOrigin = '100% 100%';
                """
            
            execute_js(css_update)
        
        ts_switch()
        ts_switch()


def ts_save():
    """
    Save current state of profile.
    """
    mw.pm.profile['ts_state_on'] = ts_state_on
    mw.pm.profile['ts_default_ConvertDotStrokes'] = ts_ConvertDotStrokes
    mw.pm.profile['ts_auto_hide'] = ts_auto_hide
    mw.pm.profile['ts_auto_hide_pointer'] = ts_auto_hide_pointer
    mw.pm.profile['ts_follow'] = ts_follow
    mw.pm.profile['ts_default_small_canvas'] = ts_default_small_canvas
    mw.pm.profile['ts_zen_mode'] = ts_zen_mode
    mw.pm.profile['ts_color'] = ts_color
    mw.pm.profile['ts_line_width'] = ts_line_width
    mw.pm.profile['ts_opacity'] = ts_opacity
    mw.pm.profile['ts_hideLineButtons'] = ts_menu_toggle_line.isChecked()
    mw.pm.profile['ts_hideRectButton'] = ts_menu_toggle_rect.isChecked()
    mw.pm.profile['ts_hideHighlightButton'] = ts_menu_toggle_highlight.isChecked()
    mw.pm.profile['ts_hideColorPickerButton'] = ts_menu_toggle_color_picker.isChecked()
    mw.pm.profile['ts_hideEraserButton'] = ts_menu_toggle_eraser.isChecked()
    mw.pm.profile['ts_hideFullscreenButton'] = ts_menu_toggle_fullscreen.isChecked()
    mw.pm.profile['ts_hideCleanCanvasButton'] = ts_menu_toggle_clean_canvas.isChecked()
    
    # 尝试保存更多详细设置
    try:
        mw.pm.profile['ts_location'] = ts_location
        mw.pm.profile['ts_x_offset'] = ts_x_offset
        mw.pm.profile['ts_y_offset'] = ts_y_offset
        mw.pm.profile['ts_small_height'] = ts_small_height
        mw.pm.profile['ts_background_color'] = ts_background_color
        mw.pm.profile['ts_small_width'] = ts_small_width
        mw.pm.profile['ts_orient_vertical'] = ts_orient_vertical
        mw.pm.profile['ts_default_eraser_mode'] = "false"  # Don't start with eraser mode on
        
        # 保存当前橡皮擦大小，而不是固定值
        eraser_size = None
        try:
            # 尝试从JavaScript获取当前橡皮擦大小
            eraser_size = mw.reviewer.web.evaluateJavaScript("eraser_indicator_size")
        except:
            # 如果失败，使用默认值
            eraser_size = 5
        
        mw.pm.profile['ts_default_eraser_size'] = eraser_size

        # 保存高亮宽度
        highlight_width = None
        try:
            # 尝试从JavaScript获取当前高亮宽度
            highlight_width = mw.reviewer.web.evaluateJavaScript("highlight_width")
        except:
            # 如果失败，使用默认值
            highlight_width = 24
        
        mw.pm.profile['ts_default_highlight_width'] = highlight_width
        
        # 保存直线和矩形工具的粗细
        line_tool_width = None
        rect_tool_width = None
        try:
            # 尝试从JavaScript获取当前直线和矩形工具粗细
            line_tool_width = mw.reviewer.web.evaluateJavaScript("line_tool_width")
            rect_tool_width = mw.reviewer.web.evaluateJavaScript("rect_tool_width")
        except:
            # 如果失败，使用默认值
            line_tool_width = 4
            rect_tool_width = 4
        
        mw.pm.profile['ts_default_line_tool_width'] = line_tool_width
        mw.pm.profile['ts_default_rect_tool_width'] = rect_tool_width
    except Exception as e:
        print(f"Error saving profile settings: {e}")

def ts_load():
    """
    Load and apply state from profile.
    """
    global ts_state_on, ts_color, ts_line_width, ts_opacity, ts_ConvertDotStrokes, ts_auto_hide
    global ts_auto_hide_pointer, ts_follow, ts_default_small_canvas, ts_zen_mode, ts_location
    global ts_x_offset, ts_y_offset, ts_small_height, ts_small_width, ts_background_color, ts_orient_vertical
    global ts_default_VISIBILITY, ts_default_PerfFreehand, ts_default_Calligraphy, ts_profile_loaded

    # Check if profile is ready before accessing
    if not hasattr(mw, 'pm') or not mw.pm or not getattr(mw.pm, 'profile', None):
        # Not ready yet, we'll retry when profile is fully loaded
        return

    try:
        # 使用get方法获取配置，提供默认值
        ts_state_on = bool(mw.pm.profile.get('ts_state_on', False))
        ts_color = str(mw.pm.profile.get('ts_color', "#272828"))
        
        # 加载笔宽度并确保不小于0.1
        loaded_width = float(mw.pm.profile.get('ts_line_width', 4.0))
        ts_line_width = max(0.1, loaded_width)
        
        ts_opacity = float(mw.pm.profile.get('ts_opacity', 0.8))
        ts_auto_hide = bool(mw.pm.profile.get('ts_auto_hide', True))
        ts_auto_hide_pointer = bool(mw.pm.profile.get('ts_auto_hide_pointer', True))
        ts_default_small_canvas = bool(mw.pm.profile.get('ts_default_small_canvas', False))
        ts_zen_mode = bool(mw.pm.profile.get('ts_zen_mode', False))
        ts_follow = bool(mw.pm.profile.get('ts_follow', False))
        ts_ConvertDotStrokes = bool(mw.pm.profile.get('ts_default_ConvertDotStrokes', True))
        ts_orient_vertical = bool(mw.pm.profile.get('ts_orient_vertical', True))
        ts_y_offset = int(mw.pm.profile.get('ts_y_offset', 2))
        ts_small_width = int(mw.pm.profile.get('ts_small_width', 500))
        ts_small_height = int(mw.pm.profile.get('ts_small_height', 500))
        ts_background_color = str(mw.pm.profile.get('ts_background_color', "#FFFFFF00"))
        ts_x_offset = int(mw.pm.profile.get('ts_x_offset', 2))
        ts_location = int(mw.pm.profile.get('ts_location', 1))
        
        # 各按钮显示状态
        hide_line_button = mw.pm.profile.get('ts_hideLineButtons', False)
        hide_rect_button = mw.pm.profile.get('ts_hideRectButton', False)
        hide_highlight_button = mw.pm.profile.get('ts_hideHighlightButton', False)
        hide_color_picker_button = mw.pm.profile.get('ts_hideColorPickerButton', False)
        hide_eraser_button = mw.pm.profile.get('ts_hideEraserButton', False)
        hide_fullscreen_button = mw.pm.profile.get('ts_hideFullscreenButton', False)
        hide_clean_canvas_button = mw.pm.profile.get('ts_hideCleanCanvasButton', False)
    except (KeyError, AttributeError, ValueError, TypeError) as e:
        # Log the error for debugging
        print(f"Doodle: Error loading profile settings: {str(e)}")
        # Use defaults
        ts_state_on = False
        ts_color = "#272828"
        ts_line_width = 4.0
        ts_opacity = 0.8
        ts_auto_hide = True
        ts_auto_hide_pointer = True
        ts_default_small_canvas = False
        ts_zen_mode = False
        ts_follow = False
        ts_ConvertDotStrokes = True
        ts_orient_vertical = True
        ts_y_offset = 2
        ts_small_width = 500
        ts_small_height = 500
        ts_background_color = "#FFFFFF00"
        ts_x_offset = 2
        ts_location = 1
        hide_line_button = False
        hide_rect_button = False
        hide_highlight_button = False
        hide_color_picker_button = False
        hide_eraser_button = False
        hide_fullscreen_button = False
        hide_clean_canvas_button = False
    
    ts_profile_loaded = True

    # 更新菜单状态(如果菜单已创建)
    if 'ts_menu_switch' in globals() and ts_menu_switch:
        ts_menu_switch.setChecked(ts_state_on)
        ts_menu_auto_hide.setChecked(ts_auto_hide)
        ts_menu_auto_hide_pointer.setChecked(ts_auto_hide_pointer)
        ts_menu_small_default.setChecked(ts_default_small_canvas)
        ts_menu_zen_mode.setChecked(ts_zen_mode)
        ts_menu_follow.setChecked(ts_follow)
        ts_menu_dots.setChecked(ts_ConvertDotStrokes)
        
        # 设置按钮显示状态菜单项的选中状态
        if 'ts_menu_toggle_line' in globals() and ts_menu_toggle_line:
            ts_menu_toggle_line.setChecked(hide_line_button)
        
        if 'ts_menu_toggle_rect' in globals() and ts_menu_toggle_rect:
            ts_menu_toggle_rect.setChecked(hide_rect_button)
        
        if 'ts_menu_toggle_highlight' in globals() and ts_menu_toggle_highlight:
            ts_menu_toggle_highlight.setChecked(hide_highlight_button)
        
        if 'ts_menu_toggle_color_picker' in globals() and ts_menu_toggle_color_picker:
            ts_menu_toggle_color_picker.setChecked(hide_color_picker_button)
            
        if 'ts_menu_toggle_eraser' in globals() and ts_menu_toggle_eraser:
            ts_menu_toggle_eraser.setChecked(hide_eraser_button)
            
        if 'ts_menu_toggle_fullscreen' in globals() and ts_menu_toggle_fullscreen:
            ts_menu_toggle_fullscreen.setChecked(hide_fullscreen_button)
            
        if 'ts_menu_toggle_clean_canvas' in globals() and ts_menu_toggle_clean_canvas:
            ts_menu_toggle_clean_canvas.setChecked(hide_clean_canvas_button)
        
        # 如果需要隐藏按钮，在加载时应用
        if ts_state_on:
            if hide_line_button:
                execute_js("if(document.getElementById('ts_line_button')) document.getElementById('ts_line_button').style.display = 'none';")
            
            if hide_rect_button:
                execute_js("if(document.getElementById('ts_rect_button')) document.getElementById('ts_rect_button').style.display = 'none';")
            
            if hide_highlight_button:
                execute_js("if(document.getElementById('ts_highlight_button')) document.getElementById('ts_highlight_button').style.display = 'none';")
            
            if hide_color_picker_button:
                execute_js("if(document.getElementById('ts_color_picker_button')) document.getElementById('ts_color_picker_button').style.display = 'none';")
                
            if hide_eraser_button:
                execute_js("if(document.getElementById('ts_eraser_button')) document.getElementById('ts_eraser_button').style.display = 'none';")
                
            if hide_fullscreen_button:
                execute_js("if(document.getElementById('ts_switch_fullscreen_button')) document.getElementById('ts_switch_fullscreen_button').style.display = 'none';")
                
            if hide_clean_canvas_button:
                execute_js("if(document.getElementById('ts_clean_canvas_button')) document.getElementById('ts_clean_canvas_button').style.display = 'none';")
    
    # Set menu checkboxes if menu exists
    if 'ts_menu_auto_hide' in globals():
        ts_menu_auto_hide.setChecked(ts_auto_hide)
        ts_menu_auto_hide_pointer.setChecked(ts_auto_hide_pointer)
        ts_menu_small_default.setChecked(ts_default_small_canvas)
        ts_menu_zen_mode.setChecked(ts_zen_mode)
        ts_menu_follow.setChecked(ts_follow)
        ts_menu_dots.setChecked(ts_ConvertDotStrokes)
        if ts_state_on:
            ts_on()

    assure_plugged_in()

    # Save the default mode variables
    ts_default_VISIBILITY = "true"
    ts_default_eraser_mode = str(mw.pm.profile.get('ts_default_eraser_mode', "false")).lower()
    ts_default_eraser_size = float(mw.pm.profile.get('ts_default_eraser_size', 10.0))
    ts_default_highlight_width = float(mw.pm.profile.get('ts_default_highlight_width', 24.0))  # 默认值改为24
    ts_default_line_tool_width = float(mw.pm.profile.get('ts_default_line_tool_width', 1.0))  # 默认值改为1.0
    ts_default_rect_tool_width = float(mw.pm.profile.get('ts_default_rect_tool_width', 1.0))  # 默认值改为1.0
    
    # 确保JavaScript端知道这些设置
    execute_js("eraser_indicator_size = " + str(ts_default_eraser_size) + ";")
    execute_js("highlight_width = " + str(ts_default_highlight_width) + ";")
    execute_js("line_tool_width = " + str(ts_default_line_tool_width) + ";")
    execute_js("rect_tool_width = " + str(ts_default_rect_tool_width) + ";")
    # 设置默认画笔粗细
    execute_js("line_width = 1.0;")

def execute_js(code):
    web_object = mw.reviewer.web
    web_object.eval(code)


def assure_plugged_in():
    global ts_default_review_html
    if not mw.reviewer.revHtml == custom:
        ts_default_review_html = mw.reviewer.revHtml
        mw.reviewer.revHtml = custom

def resize_js():
    execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");
    # 在resize后恢复所有绘制内容
    execute_js("""
        if (typeof redrawSavedShapes === 'function') {
            setTimeout(function() {
                redrawSavedShapes();
                if (typeof reapplyErasedAreas === 'function') {
                    reapplyErasedAreas();
                }
            }, 150);
        }
    """)

def clear_blackboard():
    assure_plugged_in()

    if ts_state_on:
        execute_js("if (typeof clear_canvas === 'function') { clear_canvas(); }")
        # 在清除后重新调整大小并恢复所有绘制内容
        execute_js("""
            if (typeof resize === 'function') {
                setTimeout(function() {
                    resize();
                    if (typeof redrawSavedShapes === 'function') {
                        redrawSavedShapes();
                        if (typeof reapplyErasedAreas === 'function') {
                            reapplyErasedAreas();
                        }
                    }
                }, 101);
            }
        """)

def ts_onload():
    """
    Initialize Doodle.
    """
    global ts_profile_loaded, ts_menu_switch, ts_menu_dots, ts_menu_auto_hide
    global ts_menu_auto_hide_pointer, ts_menu_small_default, ts_menu_zen_mode, ts_menu_follow
    global ts_menu_toggle_arrows, ts_menu_toggle_line, ts_menu_toggle_rect, ts_menu_toggle_highlight, ts_menu_toggle_color_picker
    
    # Setup menu first so we have reference to menu items
    ts_setup_menu()
    
    # Now add the hooks
    addHook("unloadProfile", ts_save)
    addHook("profileLoaded", ts_load)
    addHook("showQuestion", clear_blackboard)
    addHook("showAnswer", resize_js)



def blackboard():
    """
    Returns HTML and JS code for blackboard.
    """
    # 不在这里添加钩子，由ts_on处理
    return """
<div id="canvas_wrapper">
    <canvas id="secondary_canvas" width="100" height="100" ></canvas>
    <canvas id="main_canvas" width="100" height="100"></canvas>

    <div id="pencil_button_bar">
        <!-- SVG icons from https://github.com/tabler/tabler-icons/ -->
        <button id="ts_visibility_button" class="active" title="Toggle visiblity (, comma)"
              onclick="switch_visibility();" >
        <!-- 展开状态的图标：向下的小三角 -->
        <svg id="visibility_icon_expanded" stroke="currentColor" fill="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg" style="display:block;">
            <!-- 向下的三角形 -->
            <path d="M7 10L12 15L17 10" stroke="currentColor" fill="none"></path>
        </svg>
        <!-- 收起状态的图标：向上的大箭头 -->
        <svg id="visibility_icon_collapsed" stroke="currentColor" fill="none" stroke-width="3" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg" style="display:none;">
            <!-- 向上的大箭头，类似"^"形状 -->
            <line x1="4" y1="16" x2="12" y2="8" stroke="currentColor"></line>
            <line x1="20" y1="16" x2="12" y2="8" stroke="currentColor"></line>
        </svg>
        </button>

        <button id="ts_pen_button" class="active" title="Free drawing mode (default)"
              onclick="switch_pen_mode();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M15.728 9.686L14.314 8.272L5 17.586V19H6.414L15.728 9.686ZM17.142 8.272L18.556 6.858L17.142 5.444L15.728 6.858L17.142 8.272ZM7.242 21H3V16.757L16.435 3.322C16.8255 2.9317 17.3521 2.7133 17.9 2.7133C18.4479 2.7133 18.9745 2.9317 19.365 3.322L20.678 4.635C21.0683 5.0255 21.2867 5.5521 21.2867 6.1C21.2867 6.6479 21.0683 7.1745 20.678 7.565L7.243 21H7.242Z" fill="currentColor"/></svg>
        </button>

        <button id="ts_line_button" title="Draw straight line (Alt + L)"
              onclick="switch_line_mode();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M5 19l14-14"></path></svg>
        </button>

        <button id="ts_rect_button" title="Draw rectangle (Alt + R)"
              onclick="switch_rect_mode();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
        </button>

        <button id="ts_highlight_button" title="Highlight tool (Alt + K)"
              onclick="switch_highlight_mode();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
            <!-- 长的倾斜实线 -->
            <path d="M3 19L18 4" stroke-width="7" stroke-opacity="0.7" stroke-linecap="round"></path>
            <!-- 短的倾斜实线 -->
            <path d="M7 22L19 10" stroke-width="7" stroke-opacity="0.5" stroke-linecap="round"></path>
        </svg>
        </button>

        <button id="ts_eraser_button" title="Erase (Alt + Q), Size: Alt+ / Alt- (adjusts with pen width)"
              onclick="switch_eraser_mode();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M19 20h-10.5l-4.5 -4.5a1.5 1.5 0 0 1 0 -2.121l9.689 -9.689a1.5 1.5 0 0 1 2.122 0l4.5 4.5a1.5 1.5 0 0 1 0 2.121l-9.69 9.689a1.5 1.5 0 0 1 -2.121 0z"></path><path d="M16 8l4 4"></path><path d="M8.5 15.5l2 2"></path><path d="M10.5 17.5l-2 -2"></path></svg>
        </button>
        
        <button id="ts_eraser_decrease" title="Decrease size (eraser/highlight/line/rectangle) (hold to continuously decrease)"
              onclick="decrease_eraser_size();" onmousedown="startDecreaseEraser()" onmouseup="stopAdjustEraser()" onmouseleave="stopAdjustEraser()">
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        
        <button id="ts_eraser_increase" title="Increase size (eraser/highlight/line/rectangle) (hold to continuously increase)"  
              onclick="increase_eraser_size();" onmousedown="startIncreaseEraser()" onmouseup="stopAdjustEraser()" onmouseleave="stopAdjustEraser()">
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M9 18l6-6-6-6"/></svg>
        </button>

        <!-- 添加调色按钮 -->
        <button id="ts_color_picker_button" title="Change color for current tool"
              onclick="openColorPicker();">
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 21a9 9 0 0 1 0 -18c4.97 0 9 3.582 9 8c0 1.06 -.474 2.078 -1.318 2.828c-.844 .75 -1.989 1.172 -3.182 1.172h-2.5a2 2 0 0 0 -1 3.75a1.3 1.3 0 0 1 -1 2.25"></path><path d="M8.5 10.5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"></path><path d="M12.5 7.5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"></path><path d="M16.5 10.5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"></path></svg>
        </button>

        <button id="ts_clean_canvas_button" class="active" title="Clean canvas (. dot)"
              onclick="clear_canvas();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M4 7h16"></path><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path><path d="M10 12l4 4m0 -4l-4 4"></path></svg>
        </button>

        <button id="ts_switch_fullscreen_button" class="active" title="Toggle fullscreen canvas(Alt + b)"
              onclick="switch_small_canvas();" >
        <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M9.00002 3.99998H4.00004L4 9M20 8.99999V4L15 3.99997M15 20H20L20 15M4 15L4 20L9.00002 20"></path></svg>
        </button>
    </div>
</div>
<style>
:root {
  """ + get_css_for_toolbar_location( ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color) + """
}
body {
  overflow-x: hidden; /* Hide horizontal scrollbar */
}
/*
    canvas needs touch-action: none so that it doesn't fire bogus
    pointercancel events. See:
    https://stackoverflow.com/questions/59010779/pointer-event-issue-pointercancel-with-pressure-input-pen
*/
#canvas_wrapper, #main_canvas, #secondary_canvas {
   z-index: 999;/* add toggle?*/
  touch-action: pan-y pan-x;/*允许手指滚动*/
  
  position:var(--canvas-bar-position);
  top: var(--canvas-bar-pt);
  right: var(--canvas-bar-pr);
  bottom: var(--canvas-bar-pb);
  left: var(--canvas-bar-pl);
  }
#main_canvas, #secondary_canvas {
  background: var(--background-color);
  opacity: """ + str(ts_opacity) + """;
  border-style: none;
  border-width: 1px;
}
#pencil_button_bar {
  position: fixed !important;
  display: """+get_css_for_zen_mode(ts_zen_mode)+""";
  flex-direction: var(--button-bar-orientation);
  opacity: .5;
  top: var(--button-bar-pt) !important;
  right: var(--button-bar-pr) !important;
  bottom: var(--button-bar-pb) !important;
  left: var(--button-bar-pl) !important;
  z-index: 8000;
  transition: .5s;
  /* 添加样式缩小工具栏 */
  transform: scale(0.7); /* 调整为0.7，缩小工具栏至原来的70%大小 */
  /* 根据工具栏位置设置不同的变换原点 */
  transform-origin: var(--transform-origin) !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  box-sizing: border-box !important;
  max-width: none !important;
  max-height: none !important;
} #pencil_button_bar:hover { 
  opacity: 1;
} #pencil_button_bar > button {
  margin: 2px;
} #pencil_button_bar > button > svg {
  width: 2em;
} #pencil_button_bar > button:hover > svg {
  filter: drop-shadow(0 0 4px #000);
} #pencil_button_bar > button.active > svg > path {
  stroke: #1E90FF; /* 默认激活颜色为蓝色 Royal Blue */
} #pencil_button_bar > button.active > svg > rect {
  stroke: #1E90FF; /* 矩形工具激活时也使用相同的蓝色 */
} 
/* 为特定工具添加自定义颜色类 */
#pencil_button_bar > button.active-custom-color > svg > path,
#pencil_button_bar > button.active-custom-color > svg > rect {
  stroke: var(--current-tool-color, #1E90FF); /* 使用自定义颜色变量，默认为蓝色 */
}
.night_mode #pencil_button_bar > button.active > svg > path {
  stroke: #4169E1; /* 夜间模式使用稍深的蓝色 */
}
.night_mode #pencil_button_bar > button.active > svg > rect {
  stroke: #4169E1; /* 夜间模式矩形工具激活时也使用相同的蓝色 */
} #pencil_button_bar > button > svg > path {
  stroke: #888;
}
#pencil_button_bar > button > svg > rect {
  stroke: #888;
}
.night_mode #pencil_button_bar > button > svg > path {
  /*stroke: #888;*/
}
.night_mode #pencil_button_bar > button > svg > rect {
  /*stroke: #888;*/
}
.nopointer {
  cursor: """+get_css_for_auto_hide_pointer(ts_auto_hide_pointer)+""" !important;
} 
.touch_disable > button:not(:first-child){
    display: none;
}
.nopointer #pencil_button_bar
{
  display: """+get_css_for_auto_hide(ts_auto_hide, ts_zen_mode)+""";
}
</style>

<script>
var visible = """ + ts_default_VISIBILITY + """;
var perfectFreehand = false;
var canvas = document.getElementById('main_canvas');
var wrapper = document.getElementById('canvas_wrapper');
var optionBar = document.getElementById('pencil_button_bar');
var ctx = canvas.getContext('2d');
var secondary_canvas = document.getElementById('secondary_canvas');
var secondary_ctx = secondary_canvas.getContext('2d');
var ts_visibility_button = document.getElementById('ts_visibility_button');
var ts_switch_fullscreen_button = document.getElementById('ts_switch_fullscreen_button');
var ts_eraser_button = document.getElementById('ts_eraser_button');
var ts_eraser_decrease = document.getElementById('ts_eraser_decrease');
var ts_eraser_increase = document.getElementById('ts_eraser_increase');
var ts_pen_button = document.getElementById('ts_pen_button');
var ts_line_button = document.getElementById('ts_line_button');
var ts_rect_button = document.getElementById('ts_rect_button');
var ts_highlight_button = document.getElementById('ts_highlight_button');
var ts_clean_canvas_button = document.getElementById('ts_clean_canvas_button');
var arrays_of_points = [ ];
var convertDotStrokes = """ + str(ts_ConvertDotStrokes).lower() + """;
var color = '#fff';
var calligraphy = false;
var eraser_mode = false;
var line_mode = false;
var rect_mode = false;
var highlight_mode = false;
var drawing_line = false;
var drawing_rect = false;
var drawing_highlight = false;
var line_start_x = 0;
var line_start_y = 0;
var using_surface_eraser = false;
var previous_mode_before_eraser = false;
var eraser_indicator_size = 10;
var highlight_width = 24; // 设置高亮默认宽度为24
var eraser_indicator_visible = false;
var last_mouse_x = 0;
var last_mouse_y = 0;
var erasedAreas = [];
var line_type_history = [ ];
var perfect_cache = [ ];
var line_width = 1.0; // 设置默认画笔粗细为1.0
var line_tool_width = 1.0; // 直线工具专用粗细默认为1.0
var rect_tool_width = 1.0; // 矩形工具专用粗细默认为1.0
var small_canvas = """ +  str(ts_default_small_canvas).lower() + """;
var fullscreen_follow = """ + str(ts_follow).lower() + """;

// 添加数据结构保存直线、矩形和高亮内容
var saved_lines = []; // 存储格式: {startX, startY, endX, endY, width, color, erasedAreas: [{x, y, radius}]}
var saved_rects = []; // 存储格式: {startX, startY, endX, endY, width, color, erasedAreas: [{x, y, radius}]}
var saved_highlights = []; // 存储格式: {startX, startY, endX, endY, width, color, erasedAreas: [{x, y, radius}]}

// 直接在Canvas上绘制直线
function drawLine(startX, startY, endX, endY, lineWidth, lineColor, targetCtx) {
    targetCtx.save();
    targetCtx.beginPath();
    targetCtx.moveTo(startX, startY);
    targetCtx.lineTo(endX, endY);
    targetCtx.lineWidth = lineWidth;
    targetCtx.strokeStyle = lineColor;
    targetCtx.lineCap = 'round'; // 确保线条两端是圆形的
    targetCtx.stroke();
    targetCtx.restore();
}

// 直接在Canvas上绘制矩形（空心矩形，只有边框）
function drawRect(startX, startY, endX, endY, lineWidth, lineColor, targetCtx) {
    targetCtx.save();
    targetCtx.beginPath();
    
    var x = Math.min(startX, endX);
    var y = Math.min(startY, endY);
    var width = Math.abs(endX - startX);
    var height = Math.abs(endY - startY);
    
    targetCtx.lineWidth = lineWidth;
    targetCtx.strokeStyle = lineColor;
    targetCtx.lineCap = 'round';
    targetCtx.lineJoin = 'round'; // 确保拐角是圆形的
    targetCtx.rect(x, y, width, height);
    targetCtx.stroke();
    targetCtx.restore();
}

// 在直线和矩形绘制函数后添加高亮绘制函数
function drawHighlight(startX, startY, endX, endY, lineWidth, color, targetCtx) {
    // 存储原始透明度设置
    let originalGlobalAlpha = targetCtx.globalAlpha;
    
    targetCtx.save();
    targetCtx.beginPath();
    targetCtx.moveTo(startX, startY);
    targetCtx.lineTo(endX, endY);
    
    // 设置线宽为普通线宽的highlight_width倍，以便达到高亮效果
    targetCtx.lineWidth = lineWidth * highlight_width;
    
    // 处理颜色和透明度
    var highlightColor = color;
    
    // 如果颜色是带透明度的，保留原样
    if (color.startsWith('#') && color.length === 9) {
        highlightColor = color;
        // 确保不重复应用globalAlpha
        targetCtx.globalAlpha = 1.0;
    } 
    // 如果是标准RGB格式，添加50%透明度
    else if (color.startsWith('#') && color.length === 7) {
        highlightColor = color + '80'; // 添加50%透明度
        // 确保不重复应用globalAlpha
        targetCtx.globalAlpha = 1.0;
    }
    // 其他情况使用固定透明度
    else {
        targetCtx.globalAlpha = 0.5;
    }
    
    targetCtx.strokeStyle = highlightColor;
    targetCtx.lineCap = 'round';
    targetCtx.stroke();
    targetCtx.restore();
    
    // 恢复原始透明度
    targetCtx.globalAlpha = originalGlobalAlpha;
}

// 修改保存高亮的代码，确保颜色中包含透明度信息
function addHighlightToSaved(startX, startY, endX, endY, width, color) {
    // 在保存高亮前处理颜色透明度
    let processedColor = color;
    if (color.startsWith('#') && color.length === 7) {
        processedColor = color + '80'; // 添加50%透明度
    }
    
    saved_highlights.push({
        startX: startX,
        startY: startY,
        endX: endX,
        endY: endY,
        width: width,
        color: processedColor, // 使用处理后的颜色
        erasedAreas: []
    });
}

// 添加高亮模式切换函数
function switch_highlight_mode() {
    // 关闭橡皮擦模式
    if (eraser_mode) {
        eraser_mode = false;
        ts_eraser_button.className = '';
        eraser_indicator_visible = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
    
    // 关闭直线模式
    if (line_mode) {
        line_mode = false;
        ts_line_button.className = '';
    }
    
    // 关闭矩形模式
    if (rect_mode) {
        rect_mode = false;
        ts_rect_button.className = '';
    }
    
    // 切换高亮模式
    highlight_mode = !highlight_mode;
    if (highlight_mode) {
        ts_highlight_button.className = 'active-custom-color';
        ts_pen_button.className = ''; // 确保笔按钮不是激活状态
        stop_drawing(); // 停止任何正在进行的自由绘制
    } else {
        ts_highlight_button.className = '';
    }
}

var isPointerDown = false;
var mouseX = 0;
var mouseY = 0;
var drawingWithPressurePenOnly = false;
var pleaseRedrawEverything = false;
var fullClear = false;

canvas.onselectstart = function() { return false; };
secondary_canvas.onselectstart = function() { return false; };
wrapper.onselectstart = function() { return false; };

function ts_clear() {
    pleaseRedrawEverything = true;
    fullClear = true;
}

function clear_canvas() {
    stop_drawing();
    arrays_of_points = [];
    strokes = [];
    perfect_cache = [];
    line_type_history = [];
    // 清除直线、矩形和高亮数据及其擦除状态
    saved_lines = [];
    saved_rects = [];
    saved_highlights = [];
    clearErasedAreas();
    ts_clear();
}

function stop_drawing() {
    isPointerDown = false;
    drawingWithPressurePenOnly = false;
    if (drawing_line) {
        drawing_line = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
    if (drawing_rect) {
        drawing_rect = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
    if (drawing_highlight) {
        drawing_highlight = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
}

function start_drawing() {
    isPointerDown = true;
}

function draw_last_line_segment() {
    window.requestAnimationFrame(draw_last_line_segment);
    draw_upto_latest_point_async(nextLine, nextPoint, nextStroke);
}

var nextLine = 0;
var nextPoint = 0;
var nextStroke = 0;
var p1,p2,p3;

function is_last_path_and_currently_drawn(i){
    return (isPointerDown && arrays_of_points.length-1 == i);
}

function all_drawing_finished(i){
    return (!isPointerDown && arrays_of_points.length-1 == i);
}

async function draw_path_at_some_point_async(startX, startY, midX, midY, endX, endY, lineWidth) {
    ctx.beginPath();
    ctx.moveTo((startX + (midX - startX) / 2), (startY + (midY - startY)/ 2));
    ctx.quadraticCurveTo(midX, midY, (midX + (endX - midX) / 2), (midY + (endY - midY)/ 2));
    ctx.lineWidth = lineWidth;
    ctx.stroke();
}

async function draw_upto_latest_point_async(startLine, startPoint, startStroke){
    var fullRedraw = false;
    if (pleaseRedrawEverything) {
        fullRedraw = true;
        startLine = 0;
        startPoint = 0;
        startStroke = 0;
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    }

    // 保存当前颜色
    const originalColor = ctx.strokeStyle;
    const originalFillStyle = ctx.fillStyle;

    for(var i = startLine; i < arrays_of_points.length; i++){
        var needPerfectDraw = false;
        nextLine = i;
        p2 = arrays_of_points[i][startPoint > 1 ? startPoint-2 : 0];
        p3 = arrays_of_points[i][startPoint > 0 ? startPoint-1 : 0];

        // 设置每个笔画的颜色
        if (arrays_of_points[i].length > 0) {
            const strokeColor = arrays_of_points[i][0][4]; // 获取存储的颜色
            if (strokeColor) {
                ctx.strokeStyle = strokeColor;
                ctx.fillStyle = strokeColor;
            }
        }

        for(var j = startPoint; j < arrays_of_points[i].length; j++){
            nextPoint = j + 1;
            p1 = p2;
            p2 = p3;
            p3 = arrays_of_points[i][j];
            if(!perfectFreehand){
                draw_path_at_some_point_async(p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p3[3]);
            }
            else {needPerfectDraw = true;}
        }
        if(needPerfectDraw) { 
            var path = !perfect_cache[i] || is_last_path_and_currently_drawn(i)  
                ? new Path2D(
                        getFreeDrawSvgPath(
                            arrays_of_points[i],
                            !is_last_path_and_currently_drawn(i)))
                : perfect_cache[i]
            perfect_cache[i] = path
            ctx.fill(path);
        }     
        if(all_drawing_finished(i)){
            nextLine++;
            nextPoint = 0;
        }
        startPoint = 0;
    }

    // 恢复原始颜色
    ctx.strokeStyle = originalColor;
    ctx.fillStyle = originalFillStyle;

    if (fullRedraw) {
        // 重绘所有保存的直线、矩形和高亮
        redrawSavedShapes();
        
        pleaseRedrawEverything = false;
        fullRedraw = false;
        nextPoint = strokes.length == 0 ? 0 : nextPoint;
        nextStroke = strokes.length == 0 ? 0 : nextStroke;
        if(fullClear){
            nextLine = 0;
            nextStroke = 0;
            fullClear = false;
        }
        
        // 重新应用所有擦除区域
        reapplyErasedAreas();
    }
}

// 添加函数重绘保存的形状
function redrawSavedShapes() {
    // 重绘所有直线
    for (let i = 0; i < saved_lines.length; i++) {
        const line = saved_lines[i];
        drawLine(
            line.startX,
            line.startY,
            line.endX,
            line.endY,
            line.width,
            line.color,
            ctx
        );
        
        // 应用擦除区域
        if (line.erasedAreas && line.erasedAreas.length > 0) {
            ctx.save();
            ctx.globalCompositeOperation = 'destination-out';
            line.erasedAreas.forEach(area => {
                ctx.beginPath();
                ctx.arc(area.x, area.y, area.radius, 0, Math.PI * 2);
                ctx.fill();
            });
            ctx.restore();
        }
    }
    
    // 重绘所有矩形
    for (let i = 0; i < saved_rects.length; i++) {
        const rect = saved_rects[i];
        drawRect(
            rect.startX,
            rect.startY,
            rect.endX,
            rect.endY,
            rect.width,
            rect.color,
            ctx
        );
        
        // 应用擦除区域
        if (rect.erasedAreas && rect.erasedAreas.length > 0) {
            ctx.save();
            ctx.globalCompositeOperation = 'destination-out';
            rect.erasedAreas.forEach(area => {
                ctx.beginPath();
                ctx.arc(area.x, area.y, area.radius, 0, Math.PI * 2);
                ctx.fill();
            });
            ctx.restore();
        }
    }
    
    // 重绘所有高亮
    for (let i = 0; i < saved_highlights.length; i++) {
        const highlight = saved_highlights[i];
        drawHighlight(
            highlight.startX,
            highlight.startY,
            highlight.endX,
            highlight.endY,
            highlight.width,
            highlight.color,
            ctx
        );
        
        // 应用擦除区域
        if (highlight.erasedAreas && highlight.erasedAreas.length > 0) {
            ctx.save();
            ctx.globalCompositeOperation = 'destination-out';
            highlight.erasedAreas.forEach(area => {
                ctx.beginPath();
                ctx.arc(area.x, area.y, area.radius, 0, Math.PI * 2);
                ctx.fill();
            });
            ctx.restore();
        }
    }
    
    // 重绘所有自由绘制的笔画
    // 保存当前颜色
    const originalColor = ctx.strokeStyle;
    const originalFillStyle = ctx.fillStyle;
    
    for (var i = 0; i < arrays_of_points.length; i++) {
        var needPerfectDraw = false;
        p2 = arrays_of_points[i][0];
        p3 = arrays_of_points[i][0];
        
        // 设置每个笔画的颜色
        if (arrays_of_points[i].length > 0) {
            const strokeColor = arrays_of_points[i][0][4]; // 获取存储的颜色
            if (strokeColor) {
                ctx.strokeStyle = strokeColor;
                ctx.fillStyle = strokeColor;
            }
        }
        
        for (var j = 0; j < arrays_of_points[i].length; j++) {
            p1 = p2;
            p2 = p3;
            p3 = arrays_of_points[i][j];
            if (!perfectFreehand) {
                draw_path_at_some_point_async(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p3[3]);
            } else {
                needPerfectDraw = true;
            }
        }
        
        if (needPerfectDraw) {
            var path = perfect_cache[i] || new Path2D(getFreeDrawSvgPath(arrays_of_points[i], true));
            perfect_cache[i] = path;
            ctx.fill(path);
        }
    }
    
    // 恢复原始颜色
    ctx.strokeStyle = originalColor;
    ctx.fillStyle = originalFillStyle;
}

// 清除擦除区域记录的函数
function clearErasedAreas() {
    erasedAreas = [];
}

//Initialize event listeners at the start;
canvas.addEventListener("pointerdown", pointerDownLine);
canvas.addEventListener("pointermove", pointerMoveLine);
window.addEventListener("pointerup", pointerUpLine);

window.requestAnimationFrame(draw_last_line_segment);

function switch_small_canvas() {
    stop_drawing();
    
    small_canvas = !small_canvas;
    if(!small_canvas) {
        ts_switch_fullscreen_button.className = 'active';
    } else {
        ts_switch_fullscreen_button.className = '';
    }
    resize();
}

function switch_visibility() {
	stop_drawing();
    if (visible) {
        canvas.style.display='none';
        secondary_canvas.style.display=canvas.style.display;
        ts_visibility_button.className = '';
        
        // 存储每个工具按钮的显示状态，而不是直接隐藏所有按钮
        var buttonElements = optionBar.querySelectorAll('button:not(#ts_visibility_button)');
        for (var i = 0; i < buttonElements.length; i++) {
            // 将当前显示状态保存为自定义属性
            buttonElements[i].setAttribute('data-original-display', buttonElements[i].style.display || 'block');
            // 隐藏按钮
            buttonElements[i].style.display = 'none';
        }
        
        // 应用折叠样式类，但不直接改变按钮显示
        optionBar.className = 'touch_disable';
        
        // 显示收起状态图标
        document.getElementById('visibility_icon_expanded').style.display = 'none';
        document.getElementById('visibility_icon_collapsed').style.display = 'block';
    } else {
        canvas.style.display='block';
        secondary_canvas.style.display=canvas.style.display;
        ts_visibility_button.className = 'active';
        
        // 恢复每个工具按钮的原始显示状态
        var buttonElements = optionBar.querySelectorAll('button:not(#ts_visibility_button)');
        for (var i = 0; i < buttonElements.length; i++) {
            // 获取之前保存的显示状态
            var originalDisplay = buttonElements[i].getAttribute('data-original-display');
            if (originalDisplay) {
                buttonElements[i].style.display = originalDisplay;
            }
        }
        
        // 移除折叠样式类
        optionBar.className = '';
        
        // 显示展开状态图标
        document.getElementById('visibility_icon_expanded').style.display = 'block';
        document.getElementById('visibility_icon_collapsed').style.display = 'none';
    }
    visible = !visible;
}

function switch_eraser_mode() {
    stop_drawing();
    eraser_mode = !eraser_mode;
    if(eraser_mode) {
        ts_eraser_button.className = 'active';
        ts_pen_button.className = ''; // 确保笔按钮不是激活状态
        ts_line_button.className = ''; // 确保直线按钮不是激活状态
        ts_rect_button.className = ''; // 确保矩形按钮不是激活状态
        ts_highlight_button.className = ''; // 确保高亮按钮不是激活状态
        line_mode = false;
        rect_mode = false;
        highlight_mode = false;
        using_surface_eraser = false;
        eraser_indicator_visible = true;
        if (typeof last_mouse_x !== 'undefined' && typeof last_mouse_y !== 'undefined') {
            draw_eraser_indicator(last_mouse_x, last_mouse_y);
        } else {
            draw_eraser_indicator(canvas.width / 2, canvas.height / 2);
        }
    } else {
        ts_eraser_button.className = '';
        ts_pen_button.className = 'active'; // 返回到笔模式
        eraser_indicator_visible = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
}

function increase_eraser_size() {
    if (eraser_mode) {
        // 增加橡皮擦大小
        eraser_indicator_size += 2;
        if(eraser_indicator_size > 100) eraser_indicator_size = 100;
    
        if (eraser_indicator_visible) {
            let x = canvas.width / 2;
            let y = canvas.height / 2;
        
            if (typeof last_mouse_x !== 'undefined' && typeof last_mouse_y !== 'undefined') {
                x = last_mouse_x;
                y = last_mouse_y;
            }
        
            draw_eraser_indicator(x, y);
        }
    } else if (highlight_mode) {
        // 增加高亮宽度
        highlight_width += 1; // 调整为每次增加1，使调整更精确
        if(highlight_width > 100) highlight_width = 100; // 设置一个合理的最大值100
        
        // 显示高亮宽度指示器
        draw_highlight_indicator();
        
        // 如果正在绘制高亮，更新预览
        if (drawing_highlight && secondary_ctx) {
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
            drawHighlight(
                line_start_x, 
                line_start_y, 
                last_mouse_x, 
                last_mouse_y, 
                line_width, 
                color,
                secondary_ctx
            );
        }
    } else if (line_mode) {
        // 增加直线工具粗细
        line_tool_width += 0.5;
        if(line_tool_width > 50) line_tool_width = 50;
        
        // 显示直线粗细指示器
        draw_line_width_indicator('line');
        
        // 如果正在绘制直线，更新预览
        if (drawing_line && secondary_ctx) {
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
            drawLine(
                line_start_x, 
                line_start_y, 
                last_mouse_x, 
                last_mouse_y, 
                line_tool_width, 
                color,
                secondary_ctx
            );
        }
    } else if (rect_mode) {
        // 增加矩形工具粗细
        rect_tool_width += 0.5;
        if(rect_tool_width > 50) rect_tool_width = 50;
        
        // 显示矩形粗细指示器
        draw_line_width_indicator('rect');
        
        // 如果正在绘制矩形，更新预览
        if (drawing_rect && secondary_ctx) {
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
            drawRect(
                line_start_x, 
                line_start_y, 
                last_mouse_x, 
                last_mouse_y, 
                rect_tool_width, 
                color,
                secondary_ctx
            );
        }
    } else {
        // 普通笔模式，增加线条粗细
        line_width += 0.5;
        if(line_width > 50) line_width = 50;
        
        // 显示普通笔粗细指示器
        draw_pen_width_indicator();
        
        // 更新笔设置，但一定要传入true参数避免重绘
        update_pen_settings(true);
    }
}

function decrease_eraser_size() {
    if (eraser_mode) {
        // 减小橡皮擦大小
        eraser_indicator_size -= 2;
        if(eraser_indicator_size < 5) eraser_indicator_size = 5;
    
        if (eraser_indicator_visible) {
            let x = canvas.width / 2;
            let y = canvas.height / 2;
        
            if (typeof last_mouse_x !== 'undefined' && typeof last_mouse_y !== 'undefined') {
                x = last_mouse_x;
                y = last_mouse_y;
            }
        
            draw_eraser_indicator(x, y);
        }
    } else if (highlight_mode) {
        // 减小高亮宽度
        highlight_width -= 1; // 调整为每次减少1，使调整更精确
        if(highlight_width < 1.0) highlight_width = 1.0; // 最小值调整为1.0
        
        // 显示高亮宽度指示器
        draw_highlight_indicator();
        
        // 如果正在绘制高亮，更新预览
        if (drawing_highlight && secondary_ctx) {
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
            drawHighlight(
                line_start_x, 
                line_start_y, 
                last_mouse_x, 
                last_mouse_y, 
                line_width, 
                color,
                secondary_ctx
            );
        }
    } else if (line_mode) {
        // 减小直线工具粗细
        line_tool_width -= 0.5;
        if(line_tool_width < 0.5) line_tool_width = 0.5;
        
        // 显示直线粗细指示器
        draw_line_width_indicator('line');
        
        // 如果正在绘制直线，更新预览
        if (drawing_line && secondary_ctx) {
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
            drawLine(
                line_start_x, 
                line_start_y, 
                last_mouse_x, 
                last_mouse_y, 
                line_tool_width, 
                color,
                secondary_ctx
            );
        }
    } else if (rect_mode) {
        // 减小矩形工具粗细
        rect_tool_width -= 0.5;
        if(rect_tool_width < 0.5) rect_tool_width = 0.5;
        
        // 显示矩形粗细指示器
        draw_line_width_indicator('rect');
        
        // 如果正在绘制矩形，更新预览
        if (drawing_rect && secondary_ctx) {
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
            drawRect(
                line_start_x, 
                line_start_y, 
                last_mouse_x, 
                last_mouse_y, 
                rect_tool_width, 
                color,
                secondary_ctx
            );
        }
    } else {
        // 普通笔模式，减小线条粗细
        line_width -= 0.5;
        if(line_width < 0.5) line_width = 0.5;
        
        // 显示普通笔粗细指示器
        draw_pen_width_indicator();
        
        // 更新笔设置，但一定要传入true参数避免重绘
        update_pen_settings(true);
    }
}

function draw_eraser_indicator(x, y) {
    if (!eraser_indicator_visible || !eraser_mode) return;
    
    secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    secondary_ctx.save();
    
    secondary_ctx.strokeStyle = 'red';
    secondary_ctx.lineWidth = eraser_indicator_size > 50 ? 2 : 1.5;
    secondary_ctx.setLineDash([3, 3]);
    
    let baseMultiplier;
    if (line_width < 1.0) {
        baseMultiplier = 0.25;
    } else {
        baseMultiplier = line_width / 4;
    }
    
    const indicatorRadius = Math.max(3.0, eraser_indicator_size * baseMultiplier);
    
    secondary_ctx.beginPath();
    secondary_ctx.arc(x, y, indicatorRadius, 0, Math.PI * 2);
    secondary_ctx.stroke();
    
    if (eraser_indicator_size > 30) {
        secondary_ctx.beginPath();
        secondary_ctx.moveTo(x - 5, y);
        secondary_ctx.lineTo(x + 5, y);
        secondary_ctx.moveTo(x, y - 5);
        secondary_ctx.lineTo(x, y + 5);
        secondary_ctx.stroke();
    }
    
    secondary_ctx.restore();
}

// 添加高亮宽度指示器函数
function draw_highlight_indicator() {
    if (!highlight_mode) return;
    
    secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    secondary_ctx.save();
    
    // 获取设备像素比例
    const dpr = window.devicePixelRatio || 1;
    
    // 在画布中央显示高亮宽度预览
    // 使用实际的视口尺寸确保在屏幕中央显示
    const x = secondary_canvas.width / (2 * dpr);
    const y = secondary_canvas.height / (2 * dpr);
    const lineLength = Math.min(200, secondary_canvas.width / (3 * dpr)); // 确保线条不会超出画布
    
    // 显示一个示例高亮线条
    secondary_ctx.beginPath();
    secondary_ctx.moveTo(x - lineLength/2, y);
    secondary_ctx.lineTo(x + lineLength/2, y);
    
    // 设置高亮样式
    secondary_ctx.lineWidth = line_width * highlight_width;
    let highlightColor = color;
    if (color.startsWith('#')) {
        highlightColor = color + '80'; // 添加50%透明度
    }
    secondary_ctx.strokeStyle = highlightColor;
    secondary_ctx.lineCap = 'round';
    secondary_ctx.globalAlpha = 0.5;
    secondary_ctx.stroke();
    
    // 绘制黑色背景框使文字更容易阅读
    // 判断是否为夜间模式
    let isNightMode = document.body.classList.contains('night_mode');
    let fontSize = 16;
    let textY = y - 30;
    
    // 设置文本样式
    secondary_ctx.globalAlpha = 1.0;
    secondary_ctx.font = fontSize + 'px Arial';
    secondary_ctx.textAlign = 'center';
    
    // 高亮宽度文本
    let text = 'Highlight Width: ' + highlight_width.toFixed(1);
    let textWidth = secondary_ctx.measureText(text).width;
    
    // 绘制文本背景
    secondary_ctx.fillStyle = isNightMode ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.7)';
    secondary_ctx.fillRect(x - textWidth/2 - 10, textY - fontSize, textWidth + 20, fontSize + 10);
    
    // 绘制文本
    secondary_ctx.fillStyle = isNightMode ? 'white' : 'black';
    secondary_ctx.fillText(text, x, textY);
    
    // 移除自动清除功能，由stopAdjustEraser统一管理
    // 保留绘制中的预览恢复功能
    if (!isAdjusting) {
        setTimeout(function() {
            if (!isAdjusting) {
                secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
                if (drawing_highlight) {
                    // 如果正在绘制高亮，恢复预览
                    drawHighlight(
                        line_start_x, 
                        line_start_y, 
                        last_mouse_x, 
                        last_mouse_y, 
                        line_width, 
                        color,
                        secondary_ctx
                    );
                }
            }
        }, 2500); // 增加显示时间
    }
    
    secondary_ctx.restore();
}

function resize() {
    var card = document.getElementsByClassName('card')[0];
    
    if (!card){
        window.setTimeout(resize, 100);
        return;
    }
    
    // 保存当前的绘图状态以便稍后恢复
    const savedLines = JSON.parse(JSON.stringify(saved_lines));
    const savedRects = JSON.parse(JSON.stringify(saved_rects));
    const savedHighlights = JSON.parse(JSON.stringify(saved_highlights));
    const savedErasedAreas = JSON.parse(JSON.stringify(erasedAreas));
    const savedArraysOfPoints = JSON.parse(JSON.stringify(arrays_of_points));
    const savedStrokes = JSON.parse(JSON.stringify(strokes || []));
    const savedPerfectCache = perfect_cache.slice(); // 浅拷贝数组，因为Path2D对象可能无法深拷贝
    
    canvas_wrapper.style.display='none';
    canvas.style["border-style"] = "none";
    document.documentElement.style.setProperty('--canvas-bar-pt', '0px');
    document.documentElement.style.setProperty('--canvas-bar-pr', '0px');
    document.documentElement.style.setProperty('--canvas-bar-pb', 'unset');
    document.documentElement.style.setProperty('--canvas-bar-pl', 'unset');
    document.documentElement.style.setProperty('--canvas-bar-position', 'absolute');
    
    if(!small_canvas && !fullscreen_follow){
        ctx.canvas.width = Math.max(card.scrollWidth, document.documentElement.clientWidth);
        ctx.canvas.height = Math.max(document.documentElement.scrollHeight, document.documentElement.clientHeight);        
    }
    else if(small_canvas){
        ctx.canvas.width = Math.min(document.documentElement.clientWidth, 
        getComputedStyle(document.documentElement).getPropertyValue('--small-canvas-width'));
        ctx.canvas.height = Math.min(document.documentElement.clientHeight, 
        getComputedStyle(document.documentElement).getPropertyValue('--small-canvas-height'));
        canvas.style["border-style"] = "dashed";
        document.documentElement.style.setProperty('--canvas-bar-pt', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pt'));
        document.documentElement.style.setProperty('--canvas-bar-pr', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pr'));
        document.documentElement.style.setProperty('--canvas-bar-pb', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pb'));
        document.documentElement.style.setProperty('--canvas-bar-pl', 
        getComputedStyle(document.documentElement).getPropertyValue('--button-bar-pl'));
        document.documentElement.style.setProperty('--canvas-bar-position', 'fixed');
    }
    else{
        document.documentElement.style.setProperty('--canvas-bar-position', 'fixed');
        ctx.canvas.width = document.documentElement.clientWidth-1;
        ctx.canvas.height = document.documentElement.clientHeight-1;
    }
    secondary_ctx.canvas.width = ctx.canvas.width;
    secondary_ctx.canvas.height = ctx.canvas.height;
    canvas_wrapper.style.display='block';
    
    canvas.style.touchAction = "pan-y pan-x";
    secondary_canvas.style.touchAction = "pan-y pan-x";
    wrapper.style.touchAction = "pan-y pan-x";
    
    var dpr = window.devicePixelRatio || 1;
    
    canvas.style.height = ctx.canvas.height + 'px';
    wrapper.style.width = ctx.canvas.width + 'px';
    secondary_canvas.style.height = canvas.style.height;
    secondary_canvas.style.width = canvas.style.width;
    
    ctx.canvas.width *= dpr;
    ctx.canvas.height *= dpr;
    ctx.scale(dpr, dpr);
    secondary_ctx.canvas.width *= dpr;
    secondary_ctx.canvas.height *= dpr;
    secondary_ctx.scale(dpr, dpr);
    
    // 恢复原始的绘图状态
    saved_lines = savedLines;
    saved_rects = savedRects;
    saved_highlights = savedHighlights;
    erasedAreas = savedErasedAreas;
    arrays_of_points = savedArraysOfPoints;
    strokes = savedStrokes;
    
    // 尝试恢复perfect_cache，但Path2D对象可能无法正确深拷贝
    // 如果出现问题，在redrawSavedShapesAfterResize中会重新创建
    try {
        perfect_cache = savedPerfectCache;
    } catch (e) {
        perfect_cache = [];
        console.log("无法恢复perfect_cache，将重新创建");
    }
    
    // 设置抗锯齿
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    secondary_ctx.imageSmoothingEnabled = true;
    secondary_ctx.imageSmoothingQuality = 'high';
    
    // 使用一个短延迟来确保画布准备好后再重绘
    setTimeout(function() {
        // 首先清空当前画布
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        // 重绘所有形状
        redrawSavedShapesAfterResize();
        // 重新应用擦除区域
        reapplyErasedAreas();
    }, 50);
    
    update_pen_settings(true); // 使用true避免触发不必要的重绘
}

// 专门用于resize后的重绘，避免透明度叠加问题
function redrawSavedShapesAfterResize() {
    // 首先绘制手写线条
    for(var i = 0; i < arrays_of_points.length; i++){
        var needPerfectDraw = false;
        p2 = arrays_of_points[i][0];
        p3 = arrays_of_points[i][0];
        
        // 设置每个笔画的颜色
        if (arrays_of_points[i].length > 0) {
            const strokeColor = arrays_of_points[i][0][4]; // 获取存储的颜色
            if (strokeColor) {
                ctx.strokeStyle = strokeColor;
                ctx.fillStyle = strokeColor;
            }
        }
        
        for(var j = 0; j < arrays_of_points[i].length; j++){
            p1 = p2;
            p2 = p3;
            p3 = arrays_of_points[i][j];
            if(!perfectFreehand){
                // 保存绘图状态
                ctx.save();
                // 启用抗锯齿
                ctx.imageSmoothingEnabled = true;
                ctx.imageSmoothingQuality = 'high';
                
                ctx.beginPath();
                ctx.moveTo((p1[0] + (p2[0] - p1[0]) / 2), (p1[1] + (p2[1] - p1[1])/ 2));
                ctx.quadraticCurveTo(p2[0], p2[1], (p2[0] + (p3[0] - p2[0]) / 2), (p2[1] + (p3[1] - p2[1])/ 2));
                ctx.lineWidth = p3[3];
                ctx.stroke();
                
                // 恢复绘图状态
                ctx.restore();
            }
            else {needPerfectDraw = true;}
        }
        
        if(needPerfectDraw) { 
            var path = perfect_cache[i] || new Path2D(getFreeDrawSvgPath(arrays_of_points[i], true));
            perfect_cache[i] = path;
            ctx.fill(path);
        }
    }
    
    // 绘制直线
    for (let i = 0; i < saved_lines.length; i++) {
        const line = saved_lines[i];
        // 保存当前绘图状态
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(line.startX, line.startY);
        ctx.lineTo(line.endX, line.endY);
        ctx.lineWidth = line.width;
        ctx.strokeStyle = line.color;
        ctx.lineCap = 'round';
        // 启用抗锯齿
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.stroke();
        ctx.restore();
    }
    
    // 绘制矩形
    for (let i = 0; i < saved_rects.length; i++) {
        const rect = saved_rects[i];
        // 保存当前绘图状态
        ctx.save();
        ctx.beginPath();
        
        var x = Math.min(rect.startX, rect.endX);
        var y = Math.min(rect.startY, rect.endY);
        var width = Math.abs(rect.endX - rect.startX);
        var height = Math.abs(rect.endY - rect.startY);
        
        ctx.lineWidth = rect.width;
        ctx.strokeStyle = rect.color;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        // 启用抗锯齿
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.rect(x, y, width, height);
        ctx.stroke();
        ctx.restore();
    }
    
    // 绘制高亮，确保每次只应用一次透明度
    for (let i = 0; i < saved_highlights.length; i++) {
        const highlight = saved_highlights[i];
        // 保存当前绘图状态
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(highlight.startX, highlight.startY);
        ctx.lineTo(highlight.endX, highlight.endY);
        
        // 设置线宽
        ctx.lineWidth = highlight.width * highlight_width;
        
        // 确保使用已保存的颜色（带透明度的）
        let highlightColor = highlight.color;
        // 如果保存的颜色不含透明度，添加透明度
        if (highlightColor.startsWith('#') && highlightColor.length === 7) {
            highlightColor = highlightColor + '80';
        }
        
        ctx.strokeStyle = highlightColor;
        ctx.lineCap = 'round';
        // 重要：不设置全局透明度，依赖颜色本身的透明度
        // 启用抗锯齿
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.stroke();
        ctx.restore();
    }
}

// 修改drawLine函数，确保直线平滑度
function drawLine(startX, startY, endX, endY, lineWidth, lineColor, targetCtx) {
    targetCtx.save();
    // 启用抗锯齿
    targetCtx.imageSmoothingEnabled = true;
    targetCtx.imageSmoothingQuality = 'high';
    
    targetCtx.beginPath();
    targetCtx.moveTo(startX, startY);
    targetCtx.lineTo(endX, endY);
    targetCtx.lineWidth = lineWidth;
    targetCtx.strokeStyle = lineColor;
    targetCtx.lineCap = 'round'; // 确保线条两端是圆形的
    targetCtx.stroke();
    targetCtx.restore();
}

// 修改drawRect函数，确保矩形平滑度
function drawRect(startX, startY, endX, endY, lineWidth, lineColor, targetCtx) {
    targetCtx.save();
    // 启用抗锯齿
    targetCtx.imageSmoothingEnabled = true;
    targetCtx.imageSmoothingQuality = 'high';
    
    targetCtx.beginPath();
    
    var x = Math.min(startX, endX);
    var y = Math.min(startY, endY);
    var width = Math.abs(endX - startX);
    var height = Math.abs(endY - startY);
    
    targetCtx.lineWidth = lineWidth;
    targetCtx.strokeStyle = lineColor;
    targetCtx.lineCap = 'round';
    targetCtx.lineJoin = 'round'; // 确保拐角是圆形的
    targetCtx.rect(x, y, width, height);
    targetCtx.stroke();
    targetCtx.restore();
}

// 修改drawHighlight函数，完全避免透明度叠加
function drawHighlight(startX, startY, endX, endY, lineWidth, color, targetCtx) {
    // 存储原始状态
    targetCtx.save();
    // 启用抗锯齿
    targetCtx.imageSmoothingEnabled = true;
    targetCtx.imageSmoothingQuality = 'high';
    
    targetCtx.beginPath();
    targetCtx.moveTo(startX, startY);
    targetCtx.lineTo(endX, endY);
    
    // 设置线宽为普通线宽的highlight_width倍，以便达到高亮效果
    targetCtx.lineWidth = lineWidth * highlight_width;
    
    // 确保颜色包含透明度，而不是使用全局透明度
    var highlightColor = color;
    // 如果颜色是标准RGB格式，添加透明度
    if (color.startsWith('#') && color.length === 7) {
        highlightColor = color + '80'; // 添加50%透明度
    }
    // 如果颜色已经有透明度，使用原样
    
    targetCtx.strokeStyle = highlightColor;
    targetCtx.lineCap = 'round';
    
    // 重要：不设置全局透明度
    targetCtx.stroke();
    targetCtx.restore();
}

// 修改addHighlightToSaved函数，确保保存的颜色中包含透明度
function addHighlightToSaved(startX, startY, endX, endY, width, color) {
    // 处理颜色透明度
    let processedColor = color;
    if (color.startsWith('#') && color.length === 7) {
        processedColor = color + '80'; // 添加50%透明度
    }
    
    saved_highlights.push({
        startX: startX,
        startY: startY,
        endX: endX,
        endY: endY,
        width: width,
        color: processedColor, // 使用处理后的颜色
        erasedAreas: []
    });
}

// 修改resize_js函数，确保重绘过程更可靠
function resize_js() {
    execute_js(`
        if (typeof resize === 'function') { 
            resize();
            // 在resize完成后直接使用专用函数进行重绘，避免透明度叠加
            setTimeout(function() {
                if (typeof redrawSavedShapesAfterResize === 'function') {
                    redrawSavedShapesAfterResize();
                }
                if (typeof reapplyErasedAreas === 'function') {
                    reapplyErasedAreas();
                }
            }, 100);
        }
    `);
}

window.addEventListener('resize', resize);
window.addEventListener('load', resize);

function update_pen_settings(doNotRedraw = false){
    if (line_width < 0.1) {
        line_width = 0.1;
    }
    
    ctx.lineJoin = ctx.lineCap = 'round';
    ctx.lineWidth = line_width;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    secondary_ctx.lineJoin = ctx.lineJoin;
    secondary_ctx.lineWidth = ctx.lineWidth;
    secondary_ctx.strokeStyle = ctx.strokeStyle;
    secondary_ctx.fillStyle = ctx.fillStyle;
    
    if (eraser_indicator_size < 3 && line_width < 1.0) {
        eraser_indicator_size = 3;
    }
    
    // 只有在不是调整粗细时才需要重绘
    if (doNotRedraw !== true) {
        // 仅当不是在调整大小过程中时才进行完全重绘
        if (!isAdjusting) {
            ts_redraw();
            // 确保在重绘后恢复所有形状和擦除区域
            setTimeout(function() {
                redrawSavedShapes();
                reapplyErasedAreas();
            }, 50);
        }
    }
}

function ts_redraw() {
	pleaseRedrawEverything = true;
}

function pointerDownLine(e) {
    if (e.pointerType === 'touch') {
        return;
    }
    
    wrapper.classList.add('nopointer');
    if (!e.isPrimary) { return; }
    if (e.pointerType[0] == 'p') { drawingWithPressurePenOnly = true }
    else if (drawingWithPressurePenOnly) { return; }
    
    if(!isPointerDown){
        event.preventDefault();
        
        // 检测Surface Pen橡皮擦
        if (e.button === 5 || e.buttons === 32) {
            using_surface_eraser = true;
            previous_mode_before_eraser = false;
            if (!eraser_mode) {
                eraser_mode = true;
                ts_eraser_button.className = 'active';
                eraser_indicator_visible = false;
            }
        }
        
        if (eraser_mode) {
            start_drawing();
        } else if (line_mode) {
            // 直线模式下的开始
            line_start_x = e.offsetX;
            line_start_y = e.offsetY;
            drawing_line = true;
            isPointerDown = true;
            
            // 清除任何之前的预览
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        } else if (rect_mode) {
            // 矩形模式下的开始
            line_start_x = e.offsetX;
            line_start_y = e.offsetY;
            drawing_rect = true;
            isPointerDown = true;
            
            // 清除任何之前的预览
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        } else if (highlight_mode) {
            // 高亮模式下的开始
            line_start_x = e.offsetX;
            line_start_y = e.offsetY;
            drawing_highlight = true;
            isPointerDown = true;
            
            // 清除任何之前的预览
            secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        } else {
            // 自由绘制模式，存储当前颜色
            arrays_of_points.push([[
                e.offsetX,
                e.offsetY,
                e.pointerType[0] == 'p' ? e.pressure : 2,
                e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width,
                color // 存储当前颜色
            ]]);
            line_type_history.push('L');
            start_drawing();
        }
    }
}

function pointerMoveLine(e) {
    if (e.pointerType === 'touch') {
        return;
    }
    
    if (!e.isPrimary) { return; }
	if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    
    last_mouse_x = e.offsetX;
    last_mouse_y = e.offsetY;
    
    if (drawing_line) {
        // 在辅助画布上预览直线
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        drawLine(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            line_tool_width, // 使用直线专用粗细
            color,
            secondary_ctx
        );
    } else if (drawing_rect) {
        // 在辅助画布上预览矩形
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        drawRect(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            rect_tool_width, // 使用矩形专用粗细
            color,
            secondary_ctx
        );
    } else if (drawing_highlight) {
        // 在辅助画布上预览高亮
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        drawHighlight(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            line_width, 
            color,
            secondary_ctx
        );
    } else if (eraser_mode && eraser_indicator_visible && !using_surface_eraser) {
        draw_eraser_indicator(e.offsetX, e.offsetY);
    }
    
    if (isPointerDown) {
        if (eraser_mode) {
            if (using_surface_eraser) {
                eraseAtPointWithSurfacePen(e.offsetX, e.offsetY, e.pointerType[0] == 'p' ? e.pressure : 0.5);
            } else {
                eraseAtPoint(e.offsetX, e.offsetY);
            }
        } else if (!drawing_line && !drawing_rect && !drawing_highlight) {
            // 正常自由绘制
            arrays_of_points[arrays_of_points.length-1].push([
                e.offsetX,
                e.offsetY,
                e.pointerType[0] == 'p' ? e.pressure : 2,
                e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width]);
        }
    }
}

function pointerUpLine(e) {
    if (e.pointerType === 'touch') {
        return;
    }
    
    wrapper.classList.remove('nopointer');
    if (!e.isPrimary) { return; }
    if (e.pointerType[0] != 'p' && drawingWithPressurePenOnly) { return; }
    
    if (drawing_line) {
        // 完成直线绘制，直接绘制到主Canvas
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        drawLine(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            line_tool_width, // 使用直线专用粗细
            color,
            ctx
        );
        
        // 保存直线数据
        saved_lines.push({
            startX: line_start_x,
            startY: line_start_y,
            endX: e.offsetX,
            endY: e.offsetY,
            width: line_tool_width,
            color: color
        });
        
        drawing_line = false;
    } else if (drawing_rect) {
        // 完成矩形绘制，直接绘制到主Canvas
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        drawRect(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            rect_tool_width, // 使用矩形专用粗细
            color,
            ctx
        );
        
        // 保存矩形数据
        saved_rects.push({
            startX: line_start_x,
            startY: line_start_y,
            endX: e.offsetX,
            endY: e.offsetY,
            width: rect_tool_width,
            color: color
        });
        
        drawing_rect = false;
    } else if (drawing_highlight) {
        // 完成高亮绘制，直接绘制到主Canvas
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
        drawHighlight(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            line_width, 
            color,
            ctx
        );
        
        // 保存高亮数据
        addHighlightToSaved(
            line_start_x, 
            line_start_y, 
            e.offsetX, 
            e.offsetY, 
            line_width,
            color
        );
        
        drawing_highlight = false;
    } else if (isPointerDown) {
        if (!eraser_mode) {
            arrays_of_points[arrays_of_points.length-1].push([
                e.offsetX,
                e.offsetY,
                e.pointerType[0] == 'p' ? e.pressure : 2,
                e.pointerType[0] == 'p' ? (1.0 + e.pressure * line_width * 2) : line_width]);
            }
        }
    
	stop_drawing();
    
    if (using_surface_eraser && eraser_mode) {
        eraser_mode = false;
        ts_eraser_button.className = '';
        using_surface_eraser = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
}

// 添加函数用于检查点是否在橡皮擦范围内
function isPointInEraserRadius(px, py, eraserX, eraserY, eraserRadius) {
    // 计算点与橡皮擦中心之间的距离
    const dx = px - eraserX;
    const dy = py - eraserY;
    // 如果距离小于等于橡皮擦半径，则点在橡皮擦内
    return (dx * dx + dy * dy) <= eraserRadius * eraserRadius;
}

// 添加函数用于检查线段是否与橡皮擦相交
function isLineIntersectEraser(x1, y1, x2, y2, eraserX, eraserY, eraserRadius) {
    // 检查线段的端点是否在橡皮擦内
    if (isPointInEraserRadius(x1, y1, eraserX, eraserY, eraserRadius) || 
        isPointInEraserRadius(x2, y2, eraserX, eraserY, eraserRadius)) {
        return true;
    }
    
    // 线段到橡皮擦中心的最短距离
    const lineLength = Math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));
    if (lineLength === 0) {
        // 如果线段长度为0，则是一个点
        return isPointInEraserRadius(x1, y1, eraserX, eraserY, eraserRadius);
    }
    
    // 计算线段到橡皮擦中心的最短距离
    const t = ((eraserX - x1) * (x2 - x1) + (eraserY - y1) * (y2 - y1)) / (lineLength * lineLength);
    const clampedT = Math.max(0, Math.min(1, t));
    
    const closestX = x1 + clampedT * (x2 - x1);
    const closestY = y1 + clampedT * (y2 - y1);
    
    return isPointInEraserRadius(closestX, closestY, eraserX, eraserY, eraserRadius);
}

// 修改eraseAtPoint函数，记录擦除区域
function eraseAtPoint(x, y) {
    const absoluteMinRadius = 3.0;
    
    let baseMultiplier;
    if (line_width < 1.0) {
        baseMultiplier = 0.25;
    } else {
        baseMultiplier = line_width / 4;
    }
    
    const eraserRadius = Math.max(absoluteMinRadius, eraser_indicator_size * baseMultiplier);
    
    // 正常的擦除操作
    ctx.save();
    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.arc(x, y, eraserRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    
    // 更新直线的擦除状态
    saved_lines.forEach(line => {
        if (isLineIntersectEraser(line.startX, line.startY, line.endX, line.endY, x, y, eraserRadius)) {
            if (!line.erasedAreas) {
                line.erasedAreas = [];
            }
            line.erasedAreas.push({x, y, radius: eraserRadius});
        }
    });
    
    // 更新矩形的擦除状态
    saved_rects.forEach(rect => {
        const x1 = Math.min(rect.startX, rect.endX);
        const y1 = Math.min(rect.startY, rect.endY);
        const x2 = Math.max(rect.startX, rect.endX);
        const y2 = Math.max(rect.startY, rect.endY);
        
        if (isLineIntersectEraser(x1, y1, x2, y1, x, y, eraserRadius) || // 上边
            isLineIntersectEraser(x1, y2, x2, y2, x, y, eraserRadius) || // 下边
            isLineIntersectEraser(x1, y1, x1, y2, x, y, eraserRadius) || // 左边
            isLineIntersectEraser(x2, y1, x2, y2, x, y, eraserRadius)) { // 右边
            if (!rect.erasedAreas) {
                rect.erasedAreas = [];
            }
            rect.erasedAreas.push({x, y, radius: eraserRadius});
        }
    });
    
    // 更新高亮的擦除状态
    saved_highlights.forEach(highlight => {
        if (isLineIntersectEraser(highlight.startX, highlight.startY, highlight.endX, highlight.endY, x, y, eraserRadius)) {
            if (!highlight.erasedAreas) {
                highlight.erasedAreas = [];
            }
            highlight.erasedAreas.push({x, y, radius: eraserRadius});
        }
    });
    
    erasedAreas.push({
        x: x,
        y: y,
        radius: eraserRadius,
        type: 'mouse'
    });
}

function eraseAtPointWithSurfacePen(x, y, pressure) {
    const absoluteMinRadius = 3.0;
    
    let baseMinRadius, baseMaxRadius;
    
    if (line_width < 1.0) {
        baseMinRadius = 3.0;
        baseMaxRadius = 12.0;
    } else {
        baseMinRadius = line_width * 1.5;
        baseMaxRadius = line_width * 6;
    }
    
    const minRadius = Math.max(absoluteMinRadius, baseMinRadius); 
    const maxRadius = Math.max(absoluteMinRadius * 2, baseMaxRadius);
    
    const pressureValue = pressure || 0.5;
    const eraserRadius = minRadius + (maxRadius - minRadius) * pressureValue;
    
    // 正常的擦除操作 - 现在会擦除所有绘制内容，包括直线
    ctx.save();
    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.arc(x, y, eraserRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    
    // 从保存的直线数组中移除与橡皮擦相交的直线
    saved_lines = saved_lines.filter(line => !isLineIntersectEraser(
        line.startX, line.startY, line.endX, line.endY, x, y, eraserRadius
    ));
    
    // 从保存的矩形数组中移除与橡皮擦相交的矩形
    saved_rects = saved_rects.filter(rect => {
        const x1 = Math.min(rect.startX, rect.endX);
        const y1 = Math.min(rect.startY, rect.endY);
        const x2 = Math.max(rect.startX, rect.endX);
        const y2 = Math.max(rect.startY, rect.endY);
        
        // 检查矩形的四条边是否与橡皮擦相交
        return !(
            isLineIntersectEraser(x1, y1, x2, y1, x, y, eraserRadius) || // 上边
            isLineIntersectEraser(x1, y2, x2, y2, x, y, eraserRadius) || // 下边
            isLineIntersectEraser(x1, y1, x1, y2, x, y, eraserRadius) || // 左边
            isLineIntersectEraser(x2, y1, x2, y2, x, y, eraserRadius)    // 右边
        );
    });
    
    // 从保存的高亮数组中移除与橡皮擦相交的高亮
    saved_highlights = saved_highlights.filter(highlight => !isLineIntersectEraser(
        highlight.startX, highlight.startY, highlight.endX, highlight.endY, x, y, eraserRadius
    ));
    
    erasedAreas.push({
        x: x,
        y: y,
        radius: eraserRadius,
        type: 'surface'
    });
}

// 添加高亮工具的键盘快捷键
document.addEventListener('keyup', function(e) {
    if (e.key === ".") {
        clear_canvas();
    }
    if (e.key === ",") {
        switch_visibility();
    }
    if ((e.key === "b" || e.key === "B") && e.altKey) {
        e.preventDefault();
        switch_small_canvas();
    }
    if ((e.key === "q" || e.key === "Q") && e.altKey) {
        e.preventDefault();
        switch_eraser_mode();
    }
    if ((e.key === "l" || e.key === "L") && e.altKey) {
        e.preventDefault();
        switch_line_mode();
    }
    if ((e.key === "r" || e.key === "R") && e.altKey) {
        e.preventDefault();
        switch_rect_mode();
    }
    if ((e.key === "k" || e.key === "K") && e.altKey) {
        e.preventDefault();
        switch_highlight_mode();
    }
    if ((e.key === "+" || e.key === "=") && e.altKey) {
        e.preventDefault();
        increase_eraser_size();
    }
    if (e.key === "-" && e.altKey) {
        e.preventDefault();
        decrease_eraser_size();
    }
});
    
document.addEventListener('keydown', function(e) {
    if (e.altKey) {
        if (e.key === "+" || e.key === "=") {
            e.preventDefault();
            increase_eraser_size();
        }
        if (e.key === "-") {
            e.preventDefault();
            decrease_eraser_size();
        }
    }
});

var eraserAdjustInterval;
var isAdjusting = false; // 添加新变量跟踪是否在调整中

function startIncreaseEraser() {
  isAdjusting = true;
  increase_eraser_size();
  eraserAdjustInterval = setInterval(increase_eraser_size, 100);
}

function startDecreaseEraser() {
  isAdjusting = true;
  decrease_eraser_size(); 
  eraserAdjustInterval = setInterval(decrease_eraser_size, 100);
}

function stopAdjustEraser() {
  clearInterval(eraserAdjustInterval);
  isAdjusting = false; 
  
  // 在停止调整2秒后清除指示器
  setTimeout(function() {
    if (!isAdjusting) { // 只有在没有调整状态时才清除
      secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
  }, 2000);
}

// 重新应用擦除区域的函数
function reapplyErasedAreas() {
    if (!erasedAreas || erasedAreas.length === 0) return;
    
    ctx.save();
    ctx.globalCompositeOperation = 'destination-out';
    
    for (let i = 0; i < erasedAreas.length; i++) {
        const area = erasedAreas[i];
    ctx.beginPath();
        ctx.arc(area.x, area.y, area.radius, 0, Math.PI * 2);
    ctx.fill();
    }
    
    ctx.restore();
}

// 修改现有switch_pen_mode函数，确保也关闭高亮模式
function switch_pen_mode() {
    // 关闭橡皮擦模式
    if (eraser_mode) {
        eraser_mode = false;
        ts_eraser_button.className = '';
        eraser_indicator_visible = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
    
    // 关闭直线模式
    if (line_mode) {
        line_mode = false;
        ts_line_button.className = '';
    }
    
    // 关闭矩形模式
    if (rect_mode) {
        rect_mode = false;
        ts_rect_button.className = '';
    }
    
    // 关闭高亮模式
    if (highlight_mode) {
        highlight_mode = false;
        ts_highlight_button.className = '';
    }
    
    // 切换笔模式，使用自定义颜色类
    if (ts_pen_button.className === 'active-custom-color') {
        ts_pen_button.className = '';
    } else {
        ts_pen_button.className = 'active-custom-color';
    }
}

// 修改switch_line_mode函数，删除对draw_line_width_indicator的调用
function switch_line_mode() {
    // 关闭橡皮擦模式
    if (eraser_mode) {
        eraser_mode = false;
        ts_eraser_button.className = '';
        eraser_indicator_visible = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
    
    // 关闭矩形模式
    if (rect_mode) {
        rect_mode = false;
        ts_rect_button.className = '';
    }
    
    // 关闭高亮模式
    if (highlight_mode) {
        highlight_mode = false;
        ts_highlight_button.className = '';
    }
    
    // 切换直线模式
    line_mode = !line_mode;
    if (line_mode) {
        ts_line_button.className = 'active-custom-color';
        ts_pen_button.className = ''; // 确保笔按钮不是激活状态
        stop_drawing(); // 停止任何正在进行的自由绘制
    } else {
        ts_line_button.className = '';
    }
}

// 修改switch_rect_mode函数，删除对draw_line_width_indicator的调用
function switch_rect_mode() {
    // 关闭橡皮擦模式
    if (eraser_mode) {
        eraser_mode = false;
        ts_eraser_button.className = '';
        eraser_indicator_visible = false;
        secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    }
    
    // 关闭直线模式
    if (line_mode) {
        line_mode = false;
        ts_line_button.className = '';
    }
    
    // 关闭高亮模式
    if (highlight_mode) {
        highlight_mode = false;
        ts_highlight_button.className = '';
    }
    
    // 切换矩形模式
    rect_mode = !rect_mode;
    if (rect_mode) {
        ts_rect_button.className = 'active-custom-color';
        ts_pen_button.className = ''; // 确保笔按钮不是激活状态
        stop_drawing(); // 停止任何正在进行的绘制
    } else {
        ts_rect_button.className = '';
    }
}

// 添加线条宽度指示器函数
function draw_line_width_indicator(toolType) {
    if (!line_mode && !rect_mode) return;
    
    let currentWidth;
    let displayText;
    
    if (toolType === 'line' || line_mode) {
        currentWidth = line_tool_width;
        displayText = 'Line Width: ' + line_tool_width.toFixed(1);
    } else if (toolType === 'rect' || rect_mode) {
        currentWidth = rect_tool_width;
        displayText = 'Rectangle Width: ' + rect_tool_width.toFixed(1);
    } else {
        return; // 未知工具类型
    }
    
    // 仅清除secondary_canvas，不影响主画布
    secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    secondary_ctx.save();
    
    // 获取设备像素比例
    const dpr = window.devicePixelRatio || 1;
    
    // 在画布中央显示线条宽度预览
    const x = secondary_canvas.width / (2 * dpr);
    const y = secondary_canvas.height / (2 * dpr);
    const lineLength = Math.min(200, secondary_canvas.width / (3 * dpr)); // 确保线条不会超出画布
    
    // 显示一个示例线条
    secondary_ctx.beginPath();
    secondary_ctx.moveTo(x - lineLength/2, y);
    secondary_ctx.lineTo(x + lineLength/2, y);
    
    // 设置线条样式
    secondary_ctx.lineWidth = currentWidth;
    secondary_ctx.strokeStyle = color;
    secondary_ctx.lineCap = 'round';
    secondary_ctx.stroke();
    
    // 绘制背景框使文字更容易阅读
    let isNightMode = document.body.classList.contains('night_mode');
    let fontSize = 16;
    let textY = y - 30;
    
    // 设置文本样式
    secondary_ctx.globalAlpha = 1.0;
    secondary_ctx.font = fontSize + 'px Arial';
    secondary_ctx.textAlign = 'center';
    
    // 线条宽度文本
    let textWidth = secondary_ctx.measureText(displayText).width;
    
    // 绘制文本背景
    secondary_ctx.fillStyle = isNightMode ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.7)';
    secondary_ctx.fillRect(x - textWidth/2 - 10, textY - fontSize, textWidth + 20, fontSize + 10);
    
    // 绘制文本
    secondary_ctx.fillStyle = isNightMode ? 'white' : 'black';
    secondary_ctx.fillText(displayText, x, textY);
    
    // 移除自动清除功能，由stopAdjustEraser统一管理
    // 保留绘制中的预览恢复功能
    if (!isAdjusting) {
        setTimeout(function() {
            if (!isAdjusting) {
                secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
                
                // 如果正在绘制，恢复预览
                if (drawing_line) {
                    drawLine(
                        line_start_x, 
                        line_start_y, 
                        last_mouse_x, 
                        last_mouse_y, 
                        line_tool_width, // 使用直线专用粗细
                        color,
                        secondary_ctx
                    );
                } else if (drawing_rect) {
                    drawRect(
                        line_start_x, 
                        line_start_y, 
                        last_mouse_x, 
                        last_mouse_y, 
                        rect_tool_width, // 使用矩形专用粗细
                        color,
                        secondary_ctx
                    );
                }
            }
        }, 2000);
    }
    
    secondary_ctx.restore();
}

// 更新箭头按钮的title提示
document.addEventListener('DOMContentLoaded', function() {
    const decreaseButton = document.getElementById('ts_eraser_decrease');
    const increaseButton = document.getElementById('ts_eraser_increase');
    
    if (decreaseButton) {
        decreaseButton.title = "Decrease size (eraser/highlight/line/rectangle)";
    }
    
    if (increaseButton) {
        increaseButton.title = "Increase size (eraser/highlight/line/rectangle)";
    }
});

// 添加普通笔宽度指示器函数
function draw_pen_width_indicator() {
    secondary_ctx.clearRect(0, 0, secondary_canvas.width, secondary_canvas.height);
    secondary_ctx.save();
    
    // 获取设备像素比例
    const dpr = window.devicePixelRatio || 1;
    
    // 在画布中央显示线条宽度预览
    const x = secondary_canvas.width / (2 * dpr);
    const y = secondary_canvas.height / (2 * dpr);
    const lineLength = Math.min(200, secondary_canvas.width / (3 * dpr)); // 确保线条不会超出画布
    
    // 显示一个示例线条
    secondary_ctx.beginPath();
    secondary_ctx.moveTo(x - lineLength/2, y);
    secondary_ctx.lineTo(x + lineLength/2, y);
    
    // 设置线条样式
    secondary_ctx.lineWidth = line_width;
    secondary_ctx.strokeStyle = color;
    secondary_ctx.lineCap = 'round';
    secondary_ctx.stroke();
    
    // 绘制背景框使文字更容易阅读
    let isNightMode = document.body.classList.contains('night_mode');
    let fontSize = 16;
    let textY = y - 30;
    
    // 设置文本样式
    secondary_ctx.globalAlpha = 1.0;
    secondary_ctx.font = fontSize + 'px Arial';
    secondary_ctx.textAlign = 'center';
    
    // 线条宽度文本
    let displayText = 'Pen Width: ' + line_width.toFixed(1);
    let textWidth = secondary_ctx.measureText(displayText).width;
    
    // 绘制文本背景
    secondary_ctx.fillStyle = isNightMode ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.7)';
    secondary_ctx.fillRect(x - textWidth/2 - 10, textY - fontSize, textWidth + 20, fontSize + 10);
    
    // 绘制文本
    secondary_ctx.fillStyle = isNightMode ? 'white' : 'black';
    secondary_ctx.fillText(displayText, x, textY);
    
    // 移除自动清除功能，由stopAdjustEraser统一管理
    
    secondary_ctx.restore();
}

// 添加颜色选择器相关函数
function openColorPicker() {
    // 使用Python部分的QColorDialog来处理颜色选择
    pycmd("doodle:open_color_picker");
}

// 更新当前工具的颜色
function updateToolColor(newColor) {
    color = newColor;
    update_pen_settings(true); // 更新设置但不重绘现有内容
    
    // 设置CSS变量用于工具图标颜色
    document.documentElement.style.setProperty('--current-tool-color', newColor);
    
    // 更新当前激活工具的颜色
    updateActiveToolColor();
}

// 新增：更新当前激活工具的颜色
function updateActiveToolColor() {
    // 检查各个绘图工具的激活状态，并应用自定义颜色类
    if (!eraser_mode) { // 橡皮擦模式下不应用自定义颜色
        if (ts_pen_button.className === 'active') {
            ts_pen_button.className = 'active-custom-color';
        }
        
        if (line_mode && ts_line_button.className === 'active') {
            ts_line_button.className = 'active-custom-color';
        }
        
        if (rect_mode && ts_rect_button.className === 'active') {
            ts_rect_button.className = 'active-custom-color';
        }
        
        if (highlight_mode && ts_highlight_button.className === 'active') {
            ts_highlight_button.className = 'active-custom-color';
        }
    }
}

// 在页面加载时设置颜色选择按钮的初始边框颜色
document.addEventListener('DOMContentLoaded', function() {
    // 设置初始CSS变量
    document.documentElement.style.setProperty('--current-tool-color', color);
    
    // 如果有工具处于激活状态，应用自定义颜色类
    if (ts_pen_button.className === 'active') {
        ts_pen_button.className = 'active-custom-color';
    }
});
</script>
"""

@slot()
def ts_show_instructions():
    """
    显示Doodle插件的使用说明对话框
    """
    dialog = InstructionsDialog(mw)
    dialog.exec()

def custom(*args, **kwargs):
    global ts_state_on
    default = ts_default_review_html(*args, **kwargs)
    if not ts_state_on:
        return default
    output = (
        default +
        blackboard() + 
        "<script>color = '" + str(ts_color) + "';</script>" +
        "<script>line_width = " + str(ts_line_width) + ";</script>" +
        "<script>if (typeof updateToolColor === 'function') { updateToolColor('" + str(ts_color) + "'); }</script>" +
        "<script>if (typeof reapplyErasedAreas === 'function') { setTimeout(reapplyErasedAreas, 100); }</script>"
    )
    return output


mw.reviewer.revHtml = custom


def checkProfile():
    """
    Check if profile is loaded and handle error gracefully
    """
    # Check if mw.pm (profile manager) exists and is ready
    if not hasattr(mw, 'pm') or not mw.pm:
        showWarning(TS_ERROR_NO_PROFILE)
        return False
        
        # Check if profile is loaded
    if not ts_profile_loaded:
        # Try to access profile to see if it's available now
        try:
            if mw.pm.name:
                # Profile exists but ts_profile_loaded flag not set
                # This means ts_load() hasn't run yet
                ts_load()
                return True
        except:
            # If any error occurs, show warning
            showWarning(TS_ERROR_NO_PROFILE)
            return False
            
        showWarning(TS_ERROR_NO_PROFILE)
        return False
    
    return True


def ts_on():
    """
    Turn on plugin.
    """
    checkProfile()

    global ts_state_on
    ts_state_on = True
    ts_menu_switch.setChecked(True)
    
    # 确保钩子注册，使调色盘按钮可以工作
    try:
        # 为兼容Anki 25版本，确保消息处理钩子正确注册
        gui_hooks.webview_did_receive_js_message.append(handle_ankidraw_message)
    except Exception as e:
        print(f"Error registering hook: {e}")
    
    return True


def ts_off():
    """
    Turn off plugin.
    """
    checkProfile()

    global ts_state_on
    ts_state_on = False
    ts_menu_switch.setChecked(False)
    
    # 移除消息处理钩子
    try:
        gui_hooks.webview_did_receive_js_message.remove(handle_ankidraw_message)
    except (ValueError, AttributeError) as e:
        print(f"Error removing hook: {e}")
    
    return True


def handle_ankidraw_message(handled, message, context):
    """处理来自JavaScript的消息"""
    # 只处理特定前缀的消息，避免干扰其他操作
    try:
        if isinstance(message, str) and message.startswith("doodle:open_color_picker"):
            ts_change_color()
            # 为兼容Anki 25版本，返回格式为(handled, result)
            return (True, "")  # 返回一个元组 (handled, result)，结果为空字符串
    except Exception as e:
        print(f"Error in color picker handler: {e}")
    
    # 不是我们的消息，保持原来的处理状态
    return handled

@slot()
def ts_dots():
    """
    Switch dot conversion.
    """
    global ts_ConvertDotStrokes
    ts_ConvertDotStrokes = not ts_ConvertDotStrokes
    execute_js("convertDotStrokes = " + str(ts_ConvertDotStrokes).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")


@slot()
def ts_change_auto_hide_settings():
    """
    Switch auto hide toolbar setting.
    """
    global ts_auto_hide
    ts_auto_hide = not ts_auto_hide
    ts_switch()
    ts_switch()

@slot()
def ts_change_follow_settings():
    """
    Switch whiteboard follow screen.
    """
    global ts_follow
    ts_follow = not ts_follow
    execute_js("fullscreen_follow = " + str(ts_follow).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")

@slot()
def ts_change_small_default_settings():
    """
    Switch default small canvas mode setting.
    """
    global ts_default_small_canvas
    
    # 保存当前工具栏按钮的显示状态
    button_states = {
        'ts_line_button': ts_menu_toggle_line.isChecked(),
        'ts_rect_button': ts_menu_toggle_rect.isChecked(),
        'ts_highlight_button': ts_menu_toggle_highlight.isChecked(),
        'ts_color_picker_button': ts_menu_toggle_color_picker.isChecked(),
        'ts_eraser_button': ts_menu_toggle_eraser.isChecked(),
        'ts_switch_fullscreen_button': ts_menu_toggle_fullscreen.isChecked(),
        'ts_clean_canvas_button': ts_menu_toggle_clean_canvas.isChecked(),
        'ts_eraser_decrease': ts_menu_toggle_arrows.isChecked(),
        'ts_eraser_increase': ts_menu_toggle_arrows.isChecked()
    }
    
    # 切换Small Canvas选项
    ts_default_small_canvas = not ts_default_small_canvas
    
    # 重新加载界面
    ts_switch()
    ts_switch()
    
    # 恢复工具栏按钮的显示状态
    for button_id, is_checked in button_states.items():
        display_value = 'block' if is_checked else 'none'
        execute_js(f"document.getElementById('{button_id}').style.display = '{display_value}';")

@slot()
def ts_change_zen_mode_settings():
    """
    Switch default zen mode setting.
    """
    global ts_zen_mode
    ts_zen_mode = not ts_zen_mode
    ts_switch()
    ts_switch()
    
@slot()
def ts_change_auto_hide_pointer_settings():
    """
    Switch auto hide pointer setting.
    """
    global ts_auto_hide_pointer
    ts_auto_hide_pointer = not ts_auto_hide_pointer
    ts_switch()
    ts_switch()
      

@slot()
def ts_switch():
    """
    Switch Doodle.
    """
    if ts_state_on:
        ts_off()
    else:
        ts_on()

    # Reload current screen.
    if mw.state == "review":
        #mw.moveToState('overview')
        mw.moveToState('review')
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    if mw.state == "overview":
        mw.overview.refresh()

def ts_setup_menu():
    """
    Initialize menu. 
    """
    global ts_menu_switch, ts_menu_dots, ts_menu_auto_hide, ts_menu_auto_hide_pointer, ts_menu_small_default, ts_menu_zen_mode, ts_menu_follow, ts_menu_toggle_arrows, ts_menu_toggle_line
    global ts_menu_toggle_rect, ts_menu_toggle_highlight, ts_menu_toggle_color_picker
    global ts_menu_toggle_eraser, ts_menu_toggle_fullscreen, ts_menu_toggle_clean_canvas

    try:
        mw.addon_view_menu
    except AttributeError:
        mw.addon_view_menu = QMenu("""&Doodle""", mw)
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(),
                                    mw.addon_view_menu)

    # Clear existing actions from the menu
    mw.addon_view_menu.clear()

    # Create all actions but don't add them to the main menu
    ts_menu_switch = QAction("""&Enable Doodle""", mw, checkable=True)
    # 移除 ts_menu_dots 的创建但保留全局变量
    ts_menu_dots = QAction("", mw)  # 创建一个空的Action，但不显示在UI中
    ts_menu_auto_hide = QAction("""Auto &hide toolbar when drawing""", mw, checkable=True)
    ts_menu_auto_hide_pointer = QAction("""Auto &hide pointer when drawing""", mw, checkable=True)
    ts_menu_follow = QAction("""&Follow when scrolling (faster on big cards)""", mw, checkable=True)
    ts_menu_small_default = QAction("""&Small Canvas by default""", mw, checkable=True)
    ts_menu_zen_mode = QAction("""Enable Zen Mode(hide toolbar until this is disabled)""", mw, checkable=True)
    ts_menu_color = QAction("""Set &pen color""", mw)
    ts_menu_width = QAction("""Set pen &width""", mw)
    ts_menu_opacity = QAction("""Set pen &opacity""", mw)
    ts_toolbar_settings = QAction("""&Toolbar and canvas location settings""", mw)
    # 添加新的Instructions菜单项
    ts_menu_instructions = QAction("""&Instructions""", mw)

    # Create toggle actions
    ts_menu_toggle_arrows = QAction("""Toggle &Arrows""", mw, checkable=True)
    ts_menu_toggle_line = QAction("""Toggle &Line Button""", mw, checkable=True)
    ts_menu_toggle_rect = QAction("""Toggle &Rectangle Button""", mw, checkable=True)
    ts_menu_toggle_highlight = QAction("""Toggle &Highlight Button""", mw, checkable=True)
    ts_menu_toggle_color_picker = QAction("""Toggle &Color Picker Button""", mw, checkable=True)
    ts_menu_toggle_eraser = QAction("""Toggle &Eraser Button""", mw, checkable=True)
    ts_menu_toggle_fullscreen = QAction("""Toggle F&ullscreen Button""", mw, checkable=True)
    ts_menu_toggle_clean_canvas = QAction("""Toggle &Clean Canvas Button""", mw, checkable=True)

    # Set shortcut
    ts_toggle_seq = QKeySequence("Ctrl+r")
    ts_menu_switch.setShortcut(ts_toggle_seq)

    # Create a new QDialog to hold the menu layout
    menu_dialog = QDialog(mw)
    menu_dialog.setWindowTitle("Doodle Menu")

    # Only add Enable Doodle and Open Doodle Menu to the main menu
    mw.addon_view_menu.addAction(ts_menu_switch)

    # Add the Instructions menu item to the main menu
    mw.addon_view_menu.addAction(ts_menu_instructions)

    # Add the Open Doodle Menu button to the main menu
    open_menu_button = QAction("Open Doodle Menu", mw)
    mw.addon_view_menu.addAction(open_menu_button)
    open_menu_button.triggered.connect(menu_dialog.show)

    # Connect actions to their handlers
    ts_menu_switch.triggered.connect(ts_switch)
    ts_menu_dots.triggered.connect(ts_dots)
    ts_menu_auto_hide.triggered.connect(ts_change_auto_hide_settings)
    ts_menu_auto_hide_pointer.triggered.connect(ts_change_auto_hide_pointer_settings)
    ts_menu_follow.triggered.connect(ts_change_follow_settings)
    ts_menu_small_default.triggered.connect(ts_change_small_default_settings)
    ts_menu_zen_mode.triggered.connect(ts_change_zen_mode_settings)
    ts_menu_color.triggered.connect(ts_change_color)
    ts_menu_width.triggered.connect(ts_change_width)
    ts_menu_opacity.triggered.connect(ts_change_opacity)
    ts_toolbar_settings.triggered.connect(ts_change_toolbar_settings)
    # 连接Instructions菜单项
    ts_menu_instructions.triggered.connect(instructions_dialog.show_instructions)
    ts_menu_toggle_arrows.triggered.connect(ts_toggle_arrows)
    ts_menu_toggle_line.triggered.connect(ts_toggle_line)
    ts_menu_toggle_rect.triggered.connect(ts_toggle_rect)
    ts_menu_toggle_highlight.triggered.connect(ts_toggle_highlight)
    ts_menu_toggle_color_picker.triggered.connect(ts_toggle_color_picker)
    ts_menu_toggle_eraser.triggered.connect(ts_toggle_eraser)
    ts_menu_toggle_fullscreen.triggered.connect(ts_toggle_fullscreen)
    ts_menu_toggle_clean_canvas.triggered.connect(ts_toggle_clean_canvas)

    # Create a new menu layout with two columns
    menu_layout = QGridLayout()
    menu_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding around the edges
    menu_layout.setHorizontalSpacing(20)  # Add space between columns
    menu_layout.setVerticalSpacing(10)  # Consistent vertical spacing for all items

    # Helper function to create a widget with a checkbox and action
    def create_menu_item(action, with_checkbox=True):
        # Create a horizontal layout
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)
        
        # Add a checkbox or placeholder with the same width
        if with_checkbox:
            checkbox = QCheckBox()
            checkbox.setChecked(action.isChecked())
            
            # 复选框直接连接到action的触发器，这样当复选框状态改变时会直接触发action
            checkbox.clicked.connect(action.trigger)
            
            # action的状态改变时更新复选框状态
            action.toggled.connect(checkbox.setChecked)
            
            h_layout.addWidget(checkbox)
        else:
            # Create an invisible placeholder with the same width as a checkbox
            placeholder = QWidget()
            checkbox_width = QCheckBox().sizeHint().width()
            placeholder.setFixedWidth(checkbox_width)
            h_layout.addWidget(placeholder)
        
        # Add the button
        button = QToolButton()
        button.setDefaultAction(action)
        button.setStyleSheet("QToolButton { border: none; text-align: left; }")
        
        # Add "..." to actions that open dialogs
        if action in [ts_menu_color, ts_menu_width, ts_menu_opacity, ts_toolbar_settings]:
            button.setText(button.text() + "...")
            
        h_layout.addWidget(button)
        h_layout.addStretch()  # Push everything to the left
        
        # Create a widget to hold the layout
        container = QWidget()
        container.setLayout(h_layout)
        return container

    # First group: Dialog-opening items (without checkboxes but aligned)
    menu_layout.addWidget(create_menu_item(ts_menu_color, False), 0, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_width, False), 0, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_opacity, False), 1, 0)
    menu_layout.addWidget(create_menu_item(ts_toolbar_settings, False), 1, 1)

    # Second group: Checkable items - start at row 2 to maintain consistent spacing
    menu_layout.addWidget(create_menu_item(ts_menu_switch), 2, 0)
    # 移除 ts_menu_dots 菜单项，调整后续行号和布局
    menu_layout.addWidget(create_menu_item(ts_menu_auto_hide), 2, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_auto_hide_pointer), 3, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_follow), 3, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_small_default), 4, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_zen_mode), 4, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_arrows), 5, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_line), 5, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_rect), 6, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_highlight), 6, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_color_picker), 7, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_eraser), 7, 1)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_fullscreen), 8, 0)
    menu_layout.addWidget(create_menu_item(ts_menu_toggle_clean_canvas), 8, 1)

    menu_dialog.setLayout(menu_layout)

# Define a function to apply selected options
@slot()
def apply_selected_options():
    # Logic to apply selected options
    pass

@slot()
def ts_toggle_arrows():
    """
    根据菜单选中状态设置箭头按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_arrows.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_eraser_decrease').style.display = '{display_value}';")
    execute_js(f"document.getElementById('ts_eraser_increase').style.display = '{display_value}';")

@slot()
def ts_toggle_line():
    """
    根据菜单选中状态设置直线按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_line.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_line_button').style.display = '{display_value}';")

@slot()
def ts_toggle_rect():
    """
    根据菜单选中状态设置矩形按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_rect.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_rect_button').style.display = '{display_value}';")

@slot()
def ts_toggle_highlight():
    """
    根据菜单选中状态设置高亮按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_highlight.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_highlight_button').style.display = '{display_value}';")

@slot()
def ts_toggle_color_picker():
    """
    根据菜单选中状态设置色板按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_color_picker.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_color_picker_button').style.display = '{display_value}';")

@slot()
def ts_toggle_eraser():
    """
    根据菜单选中状态设置橡皮擦按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_eraser.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_eraser_button').style.display = '{display_value}';")

@slot()
def ts_toggle_fullscreen():
    """
    根据菜单选中状态设置全屏按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_fullscreen.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_switch_fullscreen_button').style.display = '{display_value}';")

@slot()
def ts_toggle_clean_canvas():
    """
    根据菜单选中状态设置清除画布按钮的显示状态
    """
    # 获取当前菜单项的选中状态
    is_checked = ts_menu_toggle_clean_canvas.isChecked()
    # 根据选中状态设置显示或隐藏 - 勾选时显示，取消勾选时隐藏
    display_value = 'block' if is_checked else 'none'
    execute_js(f"document.getElementById('ts_clean_canvas_button').style.display = '{display_value}';")

#TS_ERROR_NO_PROFILE = "No profile loaded"

#
# ONLOAD SECTION
#

ts_onload()
