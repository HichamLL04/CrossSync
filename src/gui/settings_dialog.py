import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.setWindowTitle(self.tr("settings_title"))
        self.setMinimumWidth(500)
        self.setStyleSheet(parent.styleSheet())
        self.setup_ui()
        self.load_values()

    def tr(self, key):
        return self.parent_app.tr(key)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(15)

        # Embedding model input
        self.embedding_lbl = QLabel(self.tr("emb_model_lbl"))
        self.embedding_input = QLineEdit()
        form_layout.addRow(self.embedding_lbl, self.embedding_input)

        # Provider combo
        self.provider_lbl = QLabel(self.tr("llm_provider_lbl"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["none", "ollama", "gemini", "openai"])
        self.provider_combo.currentTextChanged.connect(self.toggle_llm_fields)
        form_layout.addRow(self.provider_lbl, self.provider_combo)

        # Model Name input
        self.model_lbl = QLabel(self.tr("model_lbl"))
        self.model_input = QLineEdit()
        form_layout.addRow(self.model_lbl, self.model_input)

        # API Key input
        self.api_key_lbl = QLabel(self.tr("api_key_lbl"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(self.api_key_lbl, self.api_key_input)

        # Ollama URL input
        self.ollama_url_lbl = QLabel(self.tr("ollama_url_lbl"))
        self.ollama_url_input = QLineEdit()
        form_layout.addRow(self.ollama_url_lbl, self.ollama_url_input)

        layout.addLayout(form_layout)

        # Connection testing section (Buttons)
        test_layout = QHBoxLayout()
        self.btn_test_ollama = QPushButton(self.tr("test_ollama_btn"))
        self.btn_test_ollama.clicked.connect(self.test_ollama)
        self.btn_test_llm = QPushButton(self.tr("test_llm_btn"))
        self.btn_test_llm.clicked.connect(self.test_llm_connection)
        test_layout.addWidget(self.btn_test_ollama)
        test_layout.addWidget(self.btn_test_llm)
        layout.addLayout(test_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #333333; min-height: 1px;")
        layout.addWidget(line)

        # Save / Cancel Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel = QPushButton(self.tr("cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save = QPushButton(self.tr("save_settings"))
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setStyleSheet("""
            QPushButton#btnSave {
                background-color: #0e639c;
                border: 1px solid #1177bb;
            }
            QPushButton#btnSave:hover {
                background-color: #1177bb;
            }
        """)
        self.btn_save.clicked.connect(self.save_and_accept)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_values(self):
        config = self.parent_app.config
        self.embedding_input.setText(config.get("embedding_model", ""))
        self.provider_combo.setCurrentText(config.get("llm_provider", "none"))
        self.model_input.setText(config.get("llm_model", ""))
        self.api_key_input.setText(config.get("api_key", ""))
        self.ollama_url_input.setText(config.get("ollama_url", ""))
        self.toggle_llm_fields()

    def toggle_llm_fields(self):
        prov = self.provider_combo.currentText()
        if prov == "none":
            self.model_input.setEnabled(False)
            self.api_key_input.setEnabled(False)
            self.ollama_url_input.setEnabled(False)
            self.btn_test_ollama.setEnabled(False)
            self.btn_test_llm.setEnabled(False)
        elif prov == "ollama":
            self.model_input.setEnabled(True)
            self.api_key_input.setEnabled(False)
            self.ollama_url_input.setEnabled(True)
            self.btn_test_ollama.setEnabled(True)
            self.btn_test_llm.setEnabled(True)
        elif prov in ["gemini", "openai"]:
            self.model_input.setEnabled(True)
            self.api_key_input.setEnabled(True)
            self.ollama_url_input.setEnabled(False)
            self.btn_test_ollama.setEnabled(False)
            self.btn_test_llm.setEnabled(True)

    def test_ollama(self):
        url = self.ollama_url_input.text().strip()
        self.parent_app.log(self.tr("ollama_testing").format(url=url))
        try:
            res = requests.get(f"{url}/api/tags", timeout=5)
            if res.status_code == 200:
                models_info = res.json().get("models", [])
                model_names = [m["name"] for m in models_info]
                self.parent_app.log(f"[OLLAMA OK] Installed models: {', '.join(model_names)}")
                QMessageBox.information(
                    self, 
                    self.tr("ollama_ok_title"), 
                    self.tr("ollama_ok_msg").format(models="\n".join(model_names))
                )
            else:
                self.parent_app.log(self.tr("ollama_err_msg").format(code=res.status_code))
                QMessageBox.warning(
                    self, 
                    self.tr("ollama_err_title"), 
                    self.tr("ollama_err_msg").format(code=res.status_code)
                )
        except Exception as e:
            self.parent_app.log(self.tr("ollama_conn_fail").format(url=url, e=e))
            QMessageBox.critical(
                self, 
                self.tr("ollama_err_title"), 
                self.tr("ollama_conn_fail").format(url=url, e=e)
            )

    def test_llm_connection(self):
        provider = self.provider_combo.currentText()
        model = self.model_input.text().strip()
        api_key = self.api_key_input.text().strip()
        url = self.ollama_url_input.text().strip()

        if provider == "none":
            QMessageBox.warning(self, self.tr("api_key_warn_title"), self.tr("llm_provider_warn_msg"))
            return

        if provider in ["gemini", "openai"] and not api_key:
            QMessageBox.warning(
                self, 
                self.tr("api_key_warn_title"), 
                self.tr("api_key_warn_msg").format(provider=provider)
            )
            return

        self.parent_app.log(self.tr("llm_testing").format(provider=provider, model=model))
        try:
            from src.llm_client import LLMClient
            client = LLMClient(provider=provider, model=model, api_key=api_key, url=url)
            response = client.test_connection()
            self.parent_app.log(f"[{provider.upper()} OK] Response: '{response}'")
            QMessageBox.information(
                self, 
                self.tr("llm_ok_title").format(provider=provider.upper()), 
                self.tr("llm_ok_msg").format(response=response)
            )
        except Exception as e:
            self.parent_app.log(self.tr("llm_err_msg").format(provider=provider.upper(), e=e))
            QMessageBox.critical(
                self, 
                self.tr("llm_err_title").format(provider=provider.upper()), 
                self.tr("llm_err_msg").format(provider=provider.upper(), e=e)
            )

    def save_and_accept(self):
        self.parent_app.config["embedding_model"] = self.embedding_input.text().strip()
        self.parent_app.config["llm_provider"] = self.provider_combo.currentText()
        self.parent_app.config["llm_model"] = self.model_input.text().strip()
        self.parent_app.config["api_key"] = self.api_key_input.text().strip()
        self.parent_app.config["ollama_url"] = self.ollama_url_input.text().strip()
        self.parent_app.save_config()
        self.accept()
