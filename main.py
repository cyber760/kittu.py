import re
import sys
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox

from config.settings import ASSISTANT_NAME, USER_NAME, logger
from core.brain import JarvisBrain
from core.database import MemoryDatabase
from core.system_control import WindowsSystemController
from core.voice import VoiceEngine
from ui.main_window import JarvisMainWindow


class JarvisApplication:
    def __init__(self):
        self.db = MemoryDatabase()
        self.brain = JarvisBrain()
        self.system = WindowsSystemController()
        self.voice = VoiceEngine()

        self.window = JarvisMainWindow(
            on_command_submit=self.handle_user_command,
            on_mic_click=self.handle_voice_input,
            on_stop_click=self.voice.stop,
            on_diag_click=lambda: self.handle_user_command("Check system status"),
        )

        greeting = f"All systems online. Welcome back, {USER_NAME}. How can I assist you today?"
        self.window.signals.append_chat.emit(ASSISTANT_NAME, greeting)

    def _execute_intent(self, decision: dict) -> str:
        intent = decision.get("intent", "chat")
        target = decision.get("target", "")
        content = decision.get("content", "")
        number = decision.get("number")

        if intent == "system_status":
            return self.system.get_system_status()
        if intent == "open_app":
            return self.system.open_application(target)
        if intent == "close_app":
            return self.system.close_application(target)
        if intent == "screenshot":
            return self.system.take_screenshot()
        if intent == "set_volume" and number is not None:
            return self.system.set_volume(number)
        if intent == "set_brightness" and number is not None:
            return self.system.set_brightness(number)
        if intent == "play_youtube":
            return self.system.play_youtube(target)
        if intent == "search_web":
            return self.system.search_web(target)
        if intent == "create_file":
            return self.system.create_file(target, content)
        if intent == "save_note":
            return self.db.add_note(target)
        if intent == "list_notes":
            return self.db.list_notes()
        if intent == "lock_pc":
            return self.system.lock_workstation()
        return ""

    def handle_user_command(self, user_text: str):
        self.window.signals.append_chat.emit(USER_NAME, user_text)
        self.window.signals.set_state.emit("thinking")
        self.window.signals.set_status_text.emit("Processing directive...")
        self.db.log_message(USER_NAME, user_text)

        def _process():
            history = self.db.get_recent_messages(limit=8)
            decision = self.brain.process_input(user_text, history)
            action_result = self._execute_intent(decision)

            ai_reply = decision["reply"]
            final_output = f"{action_result}\n\n{ai_reply}" if action_result else ai_reply

            self.db.log_message(ASSISTANT_NAME, final_output, action_taken=decision["intent"])
            self.window.signals.append_chat.emit(ASSISTANT_NAME, final_output)
            self.window.signals.set_state.emit(decision.get("state", "active"))
            self.window.signals.set_status_text.emit("Speaking response...")

            spoken_text = re.sub(r"```.*?```", " Code output displayed on your screen. ", ai_reply, flags=re.S)
            spoken_text = spoken_text[:300].strip()

            if spoken_text:
                self.voice.speak(
                    spoken_text,
                    on_start=lambda: (
                        self.window.signals.set_speaking.emit(True),
                        self.window.signals.set_pulse.emit(True),
                    ),
                    on_pulse=lambda flag: self.window.signals.set_pulse.emit(flag),
                    on_end=lambda: (
                        self.window.signals.set_speaking.emit(False),
                        self.window.signals.set_pulse.emit(False),
                        self.window.signals.set_state.emit("calm"),
                        self.window.signals.set_status_text.emit("Standing by."),
                    ),
                )
            else:
                self.window.signals.set_state.emit("calm")
                self.window.signals.set_status_text.emit("Standing by.")

        threading.Thread(target=_process, daemon=True).start()

    def handle_voice_input(self):
        self.window.signals.set_state.emit("listening")
        self.window.signals.set_status_text.emit("Listening via microphone...")

        def _listen():
            text, err = self.voice.listen_once()
            if text:
                self.handle_user_command(text)
            else:
                self.window.signals.set_state.emit("calm")
                self.window.signals.set_status_text.emit(err or "No voice input received.")

        threading.Thread(target=_listen, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    try:
        jarvis = JarvisApplication()
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        QMessageBox.critical(None, "JARVIS Startup Error", str(e))
        sys.exit(1)

    jarvis.window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
