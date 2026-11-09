
import sys
import time
import serial
import pyqtgraph as pg

from collections import deque
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QLabel
)
from PySide6.QtCore import QTimer

PORT = "COM6"
BAUD_RATE = 115200
MAX_POINTS = 256
REFERENCE_VOLTAGE = 5.0


class LiveOscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Signal Doctor - Live Oscilloscope")
        self.resize(1100, 650)

        self.voltage_values = deque(maxlen=MAX_POINTS)
        self.serial_buffer = bytearray()
        self.total_bytes = 0
        self.total_samples = 0

        self.status = QLabel("Подключение к Arduino...")
        self.status.setStyleSheet(
            "color: #55dce5; background: #141e32; "
            "padding: 10px; font-size: 14px;"
        )

        try:
            self.serial = serial.Serial(
                PORT, BAUD_RATE, timeout=0
            )
            time.sleep(2)
            self.serial.reset_input_buffer()
            self.status.setText(
                f"Подключено к Arduino: {PORT}. Ожидание данных..."
            )
        except serial.SerialException as error:
            raise RuntimeError(
                f"Не удалось подключиться к Arduino: {error}"
            )

        self.graph = pg.PlotWidget()
        self.graph.setBackground("#141e32")
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.graph.setLabel("left", "Voltage", units="V")
        self.graph.setLabel("bottom", "Sample")
        self.graph.setYRange(0, 5.2)
        self.graph.setXRange(0, MAX_POINTS)
        self.graph.setTitle(
            "Live signal from Arduino",
            color="#55dce5",
            size="14pt"
        )

        self.curve = self.graph.plot(
            pen=pg.mkPen(color="#55dce5", width=2)
        )

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.status)
        layout.addWidget(self.graph)
        self.setCentralWidget(central)

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_data)
        self.timer.start(30)

    def read_data(self):
        waiting = self.serial.in_waiting

        if waiting > 0:
            received = self.serial.read(waiting)
            self.serial_buffer.extend(received)
            self.total_bytes += len(received)

        while b"\n" in self.serial_buffer:
            raw_line, _, remaining = (
                self.serial_buffer.partition(b"\n")
            )
            self.serial_buffer = bytearray(remaining)

            line = raw_line.decode(
                "utf-8", errors="ignore"
            ).strip()

            if not line or "," not in line:
                continue

            try:
                timestamp_text, adc_text = line.split(",", 1)
                timestamp = int(timestamp_text)
                adc = int(adc_text)

                voltage = adc * REFERENCE_VOLTAGE / 1023.0

                self.voltage_values.append(voltage)
                self.total_samples += 1

            except ValueError:
                continue

        if self.voltage_values:
            values = list(self.voltage_values)
            x_values = list(range(len(values)))
            self.curve.setData(x_values, values)

        self.status.setText(
            f"Порт: {PORT} | Получено байтов: {self.total_bytes} "
            f"| Прочитано точек: {self.total_samples}"
        )

    def closeEvent(self, event):
        self.timer.stop()

        if self.serial.is_open:
            self.serial.close()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        window = LiveOscilloscope()
        window.show()
        sys.exit(app.exec())

    except RuntimeError as error:
        print(error)
        sys.exit(1)
