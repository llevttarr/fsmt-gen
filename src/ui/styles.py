def apply_styles(self):
    self.setStyleSheet("""
        QWidget {
            background-color: #1e1e2f;
            color: #f0f0f0;
            font-family: "Segoe UI", "Helvetica Neue", sans-serif;
            font-size: 13px;
        }

        QLabel {
            font-weight: bold;
            margin-bottom: 4px;
        }

        QLineEdit {
            padding: 6px 8px;
            border: 1px solid #3a3a4f;
            border-radius: 6px;
            background-color: #2a2a3d;
            color: #f0f0f0;
        }

        QLineEdit:focus {
            border: 1px solid #4a90e2;
            background-color: #2f2f4a;
        }

        QPushButton {
            background-color: #4a90e2;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: bold;
            color: white;
        }

        QPushButton:hover {
            background-color: #6baaf7;
        }

        QPushButton:pressed {
            background-color: #3a78c2;
        }

        QSlider::groove:horizontal {
            height: 6px;
            background: #3a3a4f;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background: #4a90e2;
            border: 1px solid #2f2f4a;
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }

        QSlider::sub-page:horizontal {
            background: #4a90e2;
            border-radius: 3px;
        }

        QSlider::add-page:horizontal {
            background: #2a2a3d;
            border-radius: 3px;
        }
    """)

