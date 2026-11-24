from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton, QFrame
)
from config.settings import ASSISTANT_NAME, USER_NAME


class HudSignals(QObject):
    append_chat = pyqtSignal(str, str)
    set_state = pyqtSignal(str)
    set_pulse = pyqtSignal(bool)
    set_speaking = pyqtSignal(bool)
    set_status_text = pyqtSignal(str)


def render_arc_core(state: str, pulse: bool, speaking: bool) -> QPixmap:
    """Draws a glowing JARVIS-style Arc Reactor HUD visualizer."""
    size = 220
    pm = QPixmap(size, size)
    pm.fill(QColor("#0B1120"))

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)

    palette = {
        "calm": ("#06B6D4", "#0E7490"),
        "active": ("#38BDF8", "#0284C7"),
        "listening": ("#10B981", "#047857"),
        "thinking": ("#A855F7", "#6B21A8"),
        "alert": ("#F43F5E", "#BE123C"),
    }
    primary_hex, secondary_hex = palette.get(state, palette["calm"])
    primary = QColor(primary_hex)
    secondary = QColor(secondary_hex)

    center = size // 2

    painter.setPen(QPen(secondary, 4))
    painter.setBrush(Qt.NoBrush)
    outer_r = 88 if (pulse or speaking) else 82
    painter.drawEllipse(center - outer_r, center - outer_r, outer_r * 2, outer_r * 2)

    painter.setPen(QPen(primary, 6))
    mid_r = 64 if pulse else 60
    painter.drawEllipse(center - mid_r, center - mid_r, mid_r * 2, mid_r * 2)

    core_r = 38 if (speaking and pulse) else 32
    painter.setPen(Qt.NoPen)
    painter.setBrush(primary)
    painter.drawEllipse(center - core_r, center - core_r, core_r * 2, core_r * 2)

    painter.setPen(QColor("#0B1120"))
    painter.setFont(QFont("Consolas", 10, QFont.Bold))
    painter.drawText(0, center - 10, size, 20, Qt.AlignCenter, ASSISTANT_NAME)

    painter.end()
    return pm


class JarvisMainWindow(QWidget):
    def __init__(self, on_command_submit, on_mic_click, on_stop_click, on_diag_click):
        super().__init__()
        self.on_command_submit = on_command_submit
        self.on_mic_click = on_mic_click
        self.on_stop_click = on_stop_click
        self.on_diag_click = on_diag_click

        self.core_state = "calm"
        self.pulse = False
        self.speaking = False

        self.signals = HudSignals()
        self.signals.append_chat.connect(self._append_chat)
        self.signals.set_state.connect(self._set_state)
        self.signals.set_pulse.connect(self._set_pulse)
        self.signals.set_speaking.connect(self._set_speaking)
        self.signals.set_status_text.connect(self._set_status_text)

        self._build_ui()
        self._refresh_core()

    def _build_ui(self):
        self.setWindowTitle(f"{ASSISTANT_NAME} — Autonomous Windows Command HUD")
        self.resize(520, 720)
        self.setMinimumSize(420, 560)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #070B14;
                color: #E2E8F0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setSpacing(10)

        header = QLabel(f"◈ {ASSISTANT_NAME} SYSTEM INTERFACE • ONLINE")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8; letter-spacing: 1px;")
        root.addWidget(header)

        core_card = QFrame()
        core_card.setStyleSheet("background-color: #0B1120; border: 1px solid #1E293B; border-radius: 14px; padding: 10px;")
        core_layout = QVBoxLayout(core_card)

        self.core_label = QLabel()
        self.core_label.setAlignment(Qt.AlignCenter)
        core_layout.addWidget(self.core_label)

        self.status_label = QLabel(f"Standing by for your command, {USER_NAME}.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #7DD3FC; font-family: Consolas, monospace;")
        core_layout.addWidget(self.status_label)

        root.addWidget(core_card)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #0B1120; border: 1px solid #1E293B; border-radius: 10px; padding: 8px;"
        )
        root.addWidget(self.console, stretch=1)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Enter command (e.g., 'open chrome', 'system status', 'volume 60')...")
        self.input_box.setStyleSheet(
            "background-color: #111827; border: 1px solid #334155; border-radius: 8px; padding: 9px; color: #F8FAFC;"
        )
        self.input_box.returnPressed.connect(self._handle_send)
        input_row.addWidget(self.input_box, stretch=1)

        send_btn = QPushButton("Execute")
        send_btn.setStyleSheet("background-color: #0284C7; color: white;")
        send_btn.clicked.connect(self._handle_send)
        input_row.addWidget(send_btn)
        root.addLayout(input_row)

        action_row = QHBoxLayout()

        mic_btn = QPushButton("🎤 Voice Command")
        mic_btn.setStyleSheet("background-color: #059669; color: white;")
        mic_btn.clicked.connect(self.on_mic_click)
        action_row.addWidget(mic_btn)

        diag_btn = QPushButton("📊 System Stats")
        diag_btn.setStyleSheet("background-color: #1E293B; color: #38BDF8;")
        diag_btn.clicked.connect(self.on_diag_click)
        action_row.addWidget(diag_btn)

        stop_btn = QPushButton("⏹ Mute Voice")
        stop_btn.setStyleSheet("background-color: #334155; color: #F8FAFC;")
        stop_btn.clicked.connect(self.on_stop_click)
        action_row.addWidget(stop_btn)

        root.addLayout(action_row)

    def _handle_send(self):
        text = self.input_box.text().strip()
        if text:
            self.input_box.clear()
            self.on_command_submit(text)

    def _refresh_core(self):
        pm = render_arc_core(self.core_state, self.pulse, self.speaking)
        self.core_label.setPixmap(pm)

    def _append_chat(self, sender: str, message: str):
        color = "#38BDF8" if sender == ASSISTANT_NAME else "#34D399"
        escaped = (
            message.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        self.console.append(f"<p><b style='color:{color};'>[{sender}]</b><br>{escaped}</p>")

    def _set_state(self, state: str):
        self.core_state = state
        self._refresh_core()

    def _set_pulse(self, pulse: bool):
        self.pulse = pulse
        self._refresh_core()

    def _set_speaking(self, speaking: bool):
        self.speaking = speaking
        self._refresh_core()

    def _set_status_text(self, text: str):
        self.status_label.setText(text)

    def closeEvent(self, event):
        self.on_stop_click()
        super().closeEvent(event)
