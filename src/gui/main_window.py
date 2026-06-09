import sys
import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTextEdit,
    QProgressBar, QRadioButton, QGroupBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.translations import TRANSLATIONS, LANGUAGES
from src.gui.widgets import DragDropField, WriteStream
from src.gui.settings_dialog import SettingsDialog
from src.gui.worker import SyncWorker

# Main Window
class SubSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")
        self.config = self.load_config()

        self.setMinimumSize(700, 680)
        self.setup_ui()
        self.update_ui_texts()
        self.load_values()

        # Redirect stdout/stderr
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.stdout_stream = WriteStream()
        self.stderr_stream = WriteStream()
        self.stdout_stream.message.connect(self.log)
        self.stderr_stream.message.connect(self.log)
        sys.stdout = self.stdout_stream
        sys.stderr = self.stderr_stream

    def tr(self, key):
        lang = self.config.get("lang", "es")
        return TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {})).get(key, key)

    def load_config(self):
        defaults = {
            "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
            "llm_provider": "none",
            "llm_model": "qwen2.5:7b-instruct",
            "api_key": "",
            "ollama_url": "http://localhost:11434",
            "mode": "individual",
            "lang": "es"
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return {**defaults, **json.load(f)}
            except Exception:
                pass
        return defaults

    def save_config(self):
        config_data = {
            "embedding_model": self.config.get("embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"),
            "llm_provider": self.config.get("llm_provider", "none"),
            "llm_model": self.config.get("llm_model", "qwen2.5:7b-instruct"),
            "api_key": self.config.get("api_key", ""),
            "ollama_url": self.config.get("ollama_url", "http://localhost:11434"),
            "mode": "batch" if self.radio_batch.isChecked() else "individual",
            "lang": self.lang_combo.currentData()
        }
        # Keep internal config dict synced
        self.config = config_data
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            self.log(f"Error saving config: {e}")

    def closeEvent(self, event):
        self.save_config()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        event.accept()

    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                font-family: 'Segoe UI', 'Roboto', 'Helvetica', sans-serif;
                font-size: 13px;
                color: #e0e0e0;
            }
            QLabel {
                font-weight: bold;
                color: #b0b0b0;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QPushButton {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #007acc;
                color: #ffffff;
            }
            QPushButton#btnSync {
                background-color: #0e639c;
                border: 1px solid #1177bb;
                font-size: 15px;
                padding: 10px;
            }
            QPushButton#btnSync:hover {
                background-color: #1177bb;
            }
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QComboBox:hover {
                border-color: #007acc;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                selection-background-color: #007acc;
                selection-color: #ffffff;
            }
            QTextEdit {
                background-color: #000000;
                border: 1px solid #333333;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                color: #00ff00;
                border-radius: 6px;
            }
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 4px;
                text-align: center;
                background-color: #1e1e1e;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                width: 20px;
            }
            QRadioButton {
                spacing: 5px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Row (Title, Lang dropdown, Settings)
        header_layout = QHBoxLayout()
        self.title_lbl = QLabel()
        self.title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(self.title_lbl)

        header_layout.addStretch()

        # Language selection
        self.lang_lbl = QLabel()
        self.lang_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        
        # Select loaded language
        loaded_lang = self.config.get("lang", "es")
        idx = self.lang_combo.findData(loaded_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self.change_language)

        # Settings gear button
        self.btn_settings = QPushButton()
        self.btn_settings.clicked.connect(self.open_settings)

        header_layout.addWidget(self.lang_lbl)
        header_layout.addWidget(self.lang_combo)
        header_layout.addWidget(self.btn_settings)
        main_layout.addLayout(header_layout)

        # Mode Selection Box
        self.mode_box = QGroupBox()
        mode_layout = QHBoxLayout(self.mode_box)
        self.radio_individual = QRadioButton()
        self.radio_batch = QRadioButton()
        self.radio_individual.setChecked(True)
        mode_layout.addWidget(self.radio_individual)
        mode_layout.addWidget(self.radio_batch)
        self.radio_individual.toggled.connect(self.toggle_mode_views)
        self.radio_batch.toggled.connect(self.toggle_mode_views)
        main_layout.addWidget(self.mode_box)

        # File Inputs Box
        self.files_group = QGroupBox()
        files_layout = QVBoxLayout(self.files_group)
        files_layout.setSpacing(10)

        # Row 1: Unsynced
        self.unsynced_label = QLabel()
        self.unsynced_field = DragDropField("")
        self.unsynced_btn = QPushButton()
        self.unsynced_btn.clicked.connect(self.browse_unsynced)
        row1 = QHBoxLayout()
        row1.addWidget(self.unsynced_field)
        row1.addWidget(self.unsynced_btn)
        files_layout.addWidget(self.unsynced_label)
        files_layout.addLayout(row1)

        # Row 2: Synced Ref
        self.synced_label = QLabel()
        self.synced_field = DragDropField("")
        self.synced_btn = QPushButton()
        self.synced_btn.clicked.connect(self.browse_synced)
        row2 = QHBoxLayout()
        row2.addWidget(self.synced_field)
        row2.addWidget(self.synced_btn)
        files_layout.addWidget(self.synced_label)
        files_layout.addLayout(row2)

        # Row 3: Output
        self.output_label = QLabel()
        self.output_field = DragDropField("")
        self.output_btn = QPushButton()
        self.output_btn.clicked.connect(self.browse_output)
        row3 = QHBoxLayout()
        row3.addWidget(self.output_field)
        row3.addWidget(self.output_btn)
        files_layout.addWidget(self.output_label)
        files_layout.addLayout(row3)

        main_layout.addWidget(self.files_group)

        # Action Buttons
        self.btn_sync = QPushButton()
        self.btn_sync.setObjectName("btnSync")
        self.btn_sync.clicked.connect(self.start_sync)
        main_layout.addWidget(self.btn_sync)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Terminal Log Console
        self.console_label = QLabel()
        main_layout.addWidget(self.console_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

    def update_ui_texts(self):
        self.setWindowTitle(self.tr("title"))
        self.title_lbl.setText(self.tr("title"))
        self.lang_lbl.setText(self.tr("lang_lbl"))
        self.btn_settings.setText("⚙️ " + self.tr("settings_btn"))
        
        self.mode_box.setTitle(self.tr("mode_title"))
        self.radio_individual.setText(self.tr("mode_single"))
        self.radio_batch.setText(self.tr("mode_batch"))

        is_batch = self.radio_batch.isChecked()
        if is_batch:
            self.files_group.setTitle(self.tr("files_group_batch"))
            self.unsynced_label.setText(self.tr("unsynced_lbl_batch"))
            self.unsynced_field.setPlaceholderText(self.tr("unsynced_placeholder_batch"))
            self.synced_label.setText(self.tr("synced_lbl_batch"))
            self.synced_field.setPlaceholderText(self.tr("synced_placeholder_batch"))
            self.output_label.setText(self.tr("output_lbl_batch"))
            self.output_field.setPlaceholderText(self.tr("output_placeholder_batch"))
        else:
            self.files_group.setTitle(self.tr("files_group_single"))
            self.unsynced_label.setText(self.tr("unsynced_lbl_single"))
            self.unsynced_field.setPlaceholderText(self.tr("unsynced_placeholder_single"))
            self.synced_label.setText(self.tr("synced_lbl_single"))
            self.synced_field.setPlaceholderText(self.tr("synced_placeholder_single"))
            self.output_label.setText(self.tr("output_lbl_single"))
            self.output_field.setPlaceholderText(self.tr("output_placeholder_single"))

        self.unsynced_btn.setText(self.tr("browse"))
        self.synced_btn.setText(self.tr("browse"))
        self.output_btn.setText(self.tr("browse"))

        self.btn_sync.setText(self.tr("sync_btn"))
        self.console_label.setText(self.tr("console_title"))

    def load_values(self):
        if self.config.get("mode") == "batch":
            self.radio_batch.setChecked(True)
        else:
            self.radio_individual.setChecked(True)
        self.toggle_mode_views()

    def change_language(self):
        new_lang = self.lang_combo.currentData()
        self.config["lang"] = new_lang
        self.save_config()
        self.update_ui_texts()

    def toggle_mode_views(self):
        is_batch = self.radio_batch.isChecked()
        self.unsynced_field.is_dir = is_batch
        self.synced_field.is_dir = is_batch
        self.output_field.is_dir = is_batch

        if is_batch:
            self.files_group.setTitle(self.tr("files_group_batch"))
            self.unsynced_label.setText(self.tr("unsynced_lbl_batch"))
            self.unsynced_field.setPlaceholderText(self.tr("unsynced_placeholder_batch"))
            self.synced_label.setText(self.tr("synced_lbl_batch"))
            self.synced_field.setPlaceholderText(self.tr("synced_placeholder_batch"))
            self.output_label.setText(self.tr("output_lbl_batch"))
            self.output_field.setPlaceholderText(self.tr("output_placeholder_batch"))
        else:
            self.files_group.setTitle(self.tr("files_group_single"))
            self.unsynced_label.setText(self.tr("unsynced_lbl_single"))
            self.unsynced_field.setPlaceholderText(self.tr("unsynced_placeholder_single"))
            self.synced_label.setText(self.tr("synced_lbl_single"))
            self.synced_field.setPlaceholderText(self.tr("synced_placeholder_single"))
            self.output_label.setText(self.tr("output_lbl_single"))
            self.output_field.setPlaceholderText(self.tr("output_placeholder_single"))

        self.unsynced_field.clear()
        self.synced_field.clear()
        self.output_field.clear()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def browse_unsynced(self):
        is_batch = self.radio_batch.isChecked()
        if is_batch:
            path = QFileDialog.getExistingDirectory(self, self.tr("select_unsynced_dir"))
        else:
            path, _ = QFileDialog.getOpenFileName(self, self.tr("select_unsynced_file"), "", "Subtitles (*.srt)")
        if path:
            self.unsynced_field.setText(path)

    def browse_synced(self):
        is_batch = self.radio_batch.isChecked()
        if is_batch:
            path = QFileDialog.getExistingDirectory(self, self.tr("select_synced_dir"))
        else:
            path, _ = QFileDialog.getOpenFileName(self, self.tr("select_synced_file"), "", "Subtitles (*.srt)")
        if path:
            self.synced_field.setText(path)

    def browse_output(self):
        is_batch = self.radio_batch.isChecked()
        if is_batch:
            path = QFileDialog.getExistingDirectory(self, self.tr("select_output_dir"))
        else:
            path, _ = QFileDialog.getSaveFileName(self, self.tr("select_output_file"), "", "Subtitles (*.srt)")
        if path:
            self.output_field.setText(path)

    def log(self, text):
        self.log_text.append(text)
        self.log_text.ensureCursorVisible()

    def start_sync(self):
        is_batch = self.radio_batch.isChecked()
        unsynced = self.unsynced_field.text().strip()
        synced = self.synced_field.text().strip()
        output = self.output_field.text().strip()

        if not unsynced or not synced or not output:
            QMessageBox.warning(self, self.tr("empty_fields_title"), self.tr("empty_fields_warn"))
            return

        params = {
            "embedding_model": self.config.get("embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"),
            "llm_provider": self.config.get("llm_provider", "none"),
            "llm_model": self.config.get("llm_model", ""),
            "api_key": self.config.get("api_key", ""),
            "ollama_url": self.config.get("ollama_url", ""),
            "lang": self.config.get("lang", "es"),
            "unsynced": unsynced,
            "synced": synced,
            "output": output,
            "unsynced_dir": unsynced,
            "synced_dir": synced,
            "output_dir": output
        }

        self.log_text.clear()
        self.log("=== SubSync Alignment Started ===")

        self.btn_sync.setEnabled(False)
        self.progress_bar.show()

        mode = "batch" if is_batch else "individual"
        self.worker = SyncWorker(mode, params)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.sync_finished)
        self.worker.start()

    def sync_finished(self, success, message):
        self.btn_sync.setEnabled(True)
        self.progress_bar.hide()
        if success:
            self.log(f"\n=== SUCCESS ===\n{message}")
            QMessageBox.information(self, self.tr("sync_success_title"), message)
        else:
            self.log(f"\n=== ERROR ===\n{message}")
            QMessageBox.critical(self, self.tr("sync_error_title"), message)
