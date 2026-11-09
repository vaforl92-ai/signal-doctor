

import sys

import time

import serial

import numpy as np

import pyqtgraph as pg



from collections import deque

from scipy.signal import butter, sosfiltfilt



from PySide6.QtWidgets import (

    QApplication, QMainWindow, QWidget,

    QVBoxLayout, QHBoxLayout, QLabel,

    QPushButton, QFrame, QStackedWidget,

    QGridLayout, QComboBox, QDoubleSpinBox

)

from PySide6.QtCore import Qt, QTimer







PORT = "COM6"

BAUD_RATE = 115200



REFERENCE_VOLTAGE = 5.0

MAX_POINTS = 2048

DISPLAY_POINTS = 256



FFT_SAMPLES = 512

FFT_SIZE = 4096



DSP_SAMPLES = 512

MEASUREMENT_SAMPLES = 512





class SignalDoctor(QMainWindow):



    def __init__(self):

        super().__init__()



        self.setWindowTitle("Signal Doctor")

        self.resize(1280, 800)

        self.setMinimumSize(1050, 680)



        self.timestamps = deque(maxlen=MAX_POINTS)

        self.adc_values = deque(maxlen=MAX_POINTS)



        self.serial_buffer = bytearray()

        self.total_bytes = 0

        self.total_samples = 0



        self.serial = None



        self.setStyleSheet("""

            QMainWindow {

                background: #0b1020;

            }



            QWidget {

                color: #dce6f5;

                font-family: Segoe UI;

                font-size: 13px;

            }



            QFrame#sidebar {

                background: #10182a;

                border-right: 1px solid #26334b;

            }



            QFrame#panel {

                background: #141e32;

                border: 1px solid #293b57;

                border-radius: 9px;

            }



            QLabel#logo {

                color: #55dce5;

                font-size: 23px;

                font-weight: bold;

            }



            QLabel#small_text {

                color: #8192ad;

                font-size: 10px;

            }



            QLabel#page_title {

                font-size: 23px;

                font-weight: bold;

                color: #e8efff;

            }



            QLabel#panel_title {

                color: #55dce5;

                font-weight: bold;

                font-size: 12px;

            }



            QLabel#value {

                font-size: 21px;

                font-weight: bold;

                color: #e8efff;

            }



            QPushButton {

                background: transparent;

                color: #9aabc5;

                border: none;

                border-radius: 6px;

                padding: 11px;

                text-align: left;

            }



            QPushButton:hover {

                background: #1d2c46;

                color: #ffffff;

            }



            QPushButton:checked {

                background: #173c50;

                color: #55dce5;

                border-left: 3px solid #55dce5;

            }



            QComboBox, QDoubleSpinBox {

                background: #0f192c;

                color: #e8efff;

                border: 1px solid #344967;

                border-radius: 5px;

                padding: 7px;

                min-width: 90px;

            }



            QComboBox:hover, QDoubleSpinBox:hover {

                border: 1px solid #55dce5;

            }



            QComboBox QAbstractItemView {

                background: #141e32;

                color: #e8efff;

                selection-background-color: #173c50;

            }

        """)



        self.create_interface()

        self.connect_arduino()



        self.timer = QTimer()

        self.timer.timeout.connect(self.read_data)

        self.timer.start(30)



    # ==============================

    # ПОДКЛЮЧЕНИЕ ARDUINO

    # ==============================



    def connect_arduino(self):



        try:

            self.serial = serial.Serial(

                PORT,

                BAUD_RATE,

                timeout=0

            )



            time.sleep(2)

            self.serial.reset_input_buffer()



            self.connection.setText(

                f"● DEVICE CONNECTED | {PORT}"

            )



            self.connection.setStyleSheet(

                "color: #55dca5; font-weight: bold;"

            )



            self.dashboard_status.setText(

                "Arduino connected. Receiving signal data."

            )



            self.osc_status.setText(

                f"Подключено к Arduino через {PORT}. "

                "Ожидание данных..."

            )



        except serial.SerialException as error:



            self.serial = None



            self.connection.setText(

                "● DEVICE DISCONNECTED"

            )



            self.connection.setStyleSheet(

                "color: #e7b45c; font-weight: bold;"

            )



            self.dashboard_status.setText(

                f"Connection error: {error}"

            )



            self.osc_status.setText(

                f"Ошибка подключения: {error}"

            )



    # ==============================

    # ГЛАВНЫЙ ИНТЕРФЕЙС

    # ==============================



    def create_interface(self):



        central = QWidget()

        self.setCentralWidget(central)



        main_layout = QHBoxLayout(central)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)



        sidebar = QFrame()

        sidebar.setObjectName("sidebar")

        sidebar.setFixedWidth(230)



        side_layout = QVBoxLayout(sidebar)

        side_layout.setContentsMargins(17, 25, 17, 20)



        logo = QLabel("SIGNAL DOCTOR")

        logo.setObjectName("logo")



        subtitle = QLabel(

            "Signal generation & analysis"

        )

        subtitle.setObjectName("small_text")



        side_layout.addWidget(logo)

        side_layout.addWidget(subtitle)

        side_layout.addSpacing(30)



        self.stack = QStackedWidget()

        self.buttons = []



        sections = [

            "Dashboard",

            "Signal Generator",

            "Oscilloscope",

            "Spectrum Analyzer",

            "DSP Laboratory",

            "Measurements",

            "Device Settings"

        ]



        for i, section in enumerate(sections):



            button = QPushButton(section)

            button.setCheckable(True)



            button.clicked.connect(

                lambda checked=False, index=i:

                self.change_page(index)

            )



            side_layout.addWidget(button)

            self.buttons.append(button)



            self.stack.addWidget(

                self.create_page(section)

            )



        side_layout.addStretch()



        version = QLabel(

            "Version 1.4 | Arduino UNO"

        )

        version.setObjectName("small_text")

        side_layout.addWidget(version)



        content = QWidget()



        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(

            27, 23, 27, 23

        )

        content_layout.setSpacing(19)



        header = QHBoxLayout()



        heading = QLabel(

            "Signal processing system"

        )

        heading.setObjectName("page_title")



        self.connection = QLabel(

            "● DEVICE DISCONNECTED"

        )



        self.connection.setStyleSheet(

            "color: #e7b45c; font-weight: bold;"

        )



        header.addWidget(heading)

        header.addStretch()

        header.addWidget(self.connection)



        content_layout.addLayout(header)

        content_layout.addWidget(self.stack)



        main_layout.addWidget(sidebar)

        main_layout.addWidget(content, 1)



        self.change_page(0)



    # ==============================

    # СОЗДАНИЕ ПАНЕЛЕЙ

    # ==============================



    def create_panel(self, title, value, description):



        panel = QFrame()

        panel.setObjectName("panel")



        layout = QVBoxLayout(panel)

        layout.setContentsMargins(15, 13, 15, 13)



        title_label = QLabel(title)

        title_label.setObjectName("small_text")



        value_label = QLabel(value)

        value_label.setObjectName("value")



        description_label = QLabel(description)

        description_label.setObjectName("small_text")



        layout.addWidget(title_label)

        layout.addWidget(value_label)

        layout.addWidget(description_label)



        return panel, value_label



    # ==============================

    # СОЗДАНИЕ ГРАФИКА

    # ==============================



    def create_graph(self, title):



        graph = pg.PlotWidget()



        graph.setBackground("#141e32")

        graph.showGrid(

            x=True,

            y=True,

            alpha=0.3

        )



        graph.setLabel(

            "left",

            "Voltage",

            units="V"

        )



        graph.setLabel(

            "bottom",

            "Sample"

        )



        graph.setYRange(0, 5.2)



        graph.setTitle(

            title,

            color="#55dce5",

            size="14pt"

        )



        curve = graph.plot(

            pen=pg.mkPen(

                color="#55dce5",

                width=2

            )

        )



        return graph, curve



    # ==============================

    # СОЗДАНИЕ СТРАНИЦ

    # ==============================



    def create_page(self, name):



        page = QWidget()



        layout = QVBoxLayout(page)

        layout.setSpacing(17)



        title = QLabel(name)

        title.setObjectName("panel_title")



        layout.addWidget(title)



        # DASHBOARD



        if name == "Dashboard":



            grid = QGridLayout()

            grid.setSpacing(12)



            panels = [

                ("HARDWARE", "MCP4725", "DAC converter"),

                ("WAVEFORM", "Sine", "Current signal"),

                ("FREQUENCY", "— Hz", "Estimated frequency"),

                ("AMPLITUDE", "— V", "Peak amplitude")

            ]



            self.dashboard_values = []



            for i, data in enumerate(panels):



                panel, value_label = self.create_panel(

                    *data

                )



                grid.addWidget(panel, 0, i)

                self.dashboard_values.append(value_label)



            layout.addLayout(grid)



            graph_panel = QFrame()

            graph_panel.setObjectName("panel")



            graph_layout = QVBoxLayout(graph_panel)

            graph_layout.setContentsMargins(

                15, 13, 15, 13

            )



            graph_title = QLabel("SIGNAL MONITOR")

            graph_title.setObjectName("panel_title")



            self.dashboard_graph, self.dashboard_curve = (

                self.create_graph(

                    "Live signal from Arduino"

                )

            )



            graph_layout.addWidget(graph_title)

            graph_layout.addWidget(self.dashboard_graph)



            layout.addWidget(graph_panel, 1)



            self.dashboard_status = QLabel(

                "System ready. Waiting for Arduino connection."

            )



            self.dashboard_status.setObjectName("small_text")

            layout.addWidget(self.dashboard_status)



        # OSCILLOSCOPE



        elif name == "Oscilloscope":



            self.osc_status = QLabel(

                "Ожидание подключения..."

            )



            self.osc_status.setStyleSheet(

                "color: #55dce5; background: #141e32;"

                "padding: 10px; font-size: 13px;"

            )



            layout.addWidget(self.osc_status)



            stats = QHBoxLayout()



            self.osc_min = QLabel("MIN: — V")

            self.osc_max = QLabel("MAX: — V")

            self.osc_amplitude = QLabel("AMPLITUDE: — V")



            for label in [

                self.osc_min,

                self.osc_max,

                self.osc_amplitude

            ]:

                label.setObjectName("value")

                stats.addWidget(label)



            layout.addLayout(stats)



            graph_panel = QFrame()

            graph_panel.setObjectName("panel")



            graph_layout = QVBoxLayout(graph_panel)

            graph_layout.setContentsMargins(

                15, 13, 15, 13

            )



            self.osc_graph, self.osc_curve = (

                self.create_graph("Live Oscilloscope")

            )



            graph_layout.addWidget(self.osc_graph)

            layout.addWidget(graph_panel, 1)



            self.osc_samples = QLabel(

                "Получено точек: 0"

            )



            self.osc_samples.setObjectName("small_text")

            layout.addWidget(self.osc_samples)



        # FFT SPECTRUM ANALYZER



        elif name == "Spectrum Analyzer":



            info_panel = QFrame()

            info_panel.setObjectName("panel")



            info_layout = QVBoxLayout(info_panel)

            info_layout.setContentsMargins(15, 12, 15, 12)



            self.spectrum_status = QLabel(

                "Ожидание накопления данных..."

            )

            self.spectrum_status.setObjectName("small_text")



            self.spectrum_frequency = QLabel(

                "Основная частота: — Hz"

            )

            self.spectrum_frequency.setObjectName("value")



            self.spectrum_amplitude = QLabel(

                "Амплитуда основной гармоники: — V"

            )

            self.spectrum_amplitude.setObjectName("value")



            self.spectrum_rate = QLabel(

                "Частота дискретизации: — Hz"

            )

            self.spectrum_rate.setObjectName("small_text")



            info_layout.addWidget(self.spectrum_status)

            info_layout.addWidget(self.spectrum_frequency)

            info_layout.addWidget(self.spectrum_amplitude)

            info_layout.addWidget(self.spectrum_rate)



            layout.addWidget(info_panel)



            spectrum_panel = QFrame()

            spectrum_panel.setObjectName("panel")



            spectrum_layout = QVBoxLayout(spectrum_panel)

            spectrum_layout.setContentsMargins(

                15, 13, 15, 13

            )



            spectrum_title = QLabel(

                "FREQUENCY SPECTRUM | FFT"

            )

            spectrum_title.setObjectName("panel_title")



            self.spectrum_graph = pg.PlotWidget()

            self.spectrum_graph.setBackground("#141e32")



            self.spectrum_graph.showGrid(

                x=True,

                y=True,

                alpha=0.3

            )



            self.spectrum_graph.setLabel(

                "left",

                "Amplitude",

                units="V"

            )



            self.spectrum_graph.setLabel(

                "bottom",

                "Frequency",

                units="Hz"

            )



            self.spectrum_graph.setTitle(

                "Fast Fourier Transform",

                color="#55dce5",

                size="14pt"

            )



            self.spectrum_curve = self.spectrum_graph.plot(

                pen=pg.mkPen(

                    color="#ffb454",

                    width=2

                )

            )



            spectrum_layout.addWidget(spectrum_title)

            spectrum_layout.addWidget(self.spectrum_graph)



            layout.addWidget(spectrum_panel, 1)



        # DSP LABORATORY



        elif name == "DSP Laboratory":



            description = QLabel(

                "Digital filtering and signal comparison"

            )

            description.setObjectName("small_text")

            layout.addWidget(description)



            controls_panel = QFrame()

            controls_panel.setObjectName("panel")



            controls_layout = QVBoxLayout(controls_panel)

            controls_layout.setContentsMargins(

                15, 12, 15, 12

            )



            controls_title = QLabel("FILTER SETTINGS")

            controls_title.setObjectName("panel_title")



            controls_layout.addWidget(controls_title)



            controls_row = QHBoxLayout()



            filter_label = QLabel("Filter type:")



            self.dsp_filter = QComboBox()

            self.dsp_filter.addItems([

                "No filter",

                "Low-pass",

                "High-pass",

                "Band-pass",

                "Noise reduction"

            ])



            low_label = QLabel("Lower cutoff:")



            self.dsp_low_cutoff = QDoubleSpinBox()

            self.dsp_low_cutoff.setRange(0.5, 200.0)

            self.dsp_low_cutoff.setDecimals(1)

            self.dsp_low_cutoff.setSingleStep(0.5)

            self.dsp_low_cutoff.setValue(5.0)

            self.dsp_low_cutoff.setSuffix(" Hz")



            high_label = QLabel("Upper cutoff:")



            self.dsp_high_cutoff = QDoubleSpinBox()

            self.dsp_high_cutoff.setRange(1.0, 200.0)

            self.dsp_high_cutoff.setDecimals(1)

            self.dsp_high_cutoff.setSingleStep(0.5)

            self.dsp_high_cutoff.setValue(15.0)

            self.dsp_high_cutoff.setSuffix(" Hz")



            controls_row.addWidget(filter_label)

            controls_row.addWidget(self.dsp_filter)

            controls_row.addSpacing(12)

            controls_row.addWidget(low_label)

            controls_row.addWidget(self.dsp_low_cutoff)

            controls_row.addSpacing(8)

            controls_row.addWidget(high_label)

            controls_row.addWidget(self.dsp_high_cutoff)

            controls_row.addStretch()



            controls_layout.addLayout(controls_row)



            layout.addWidget(controls_panel)



            self.dsp_status = QLabel(

                "Ожидание данных для цифровой обработки..."

            )

            self.dsp_status.setObjectName("small_text")



            layout.addWidget(self.dsp_status)



            dsp_graph_panel = QFrame()

            dsp_graph_panel.setObjectName("panel")



            dsp_graph_layout = QVBoxLayout(dsp_graph_panel)

            dsp_graph_layout.setContentsMargins(

                15, 13, 15, 13

            )



            dsp_title = QLabel(

                "ORIGINAL SIGNAL vs FILTERED SIGNAL"

            )

            dsp_title.setObjectName("panel_title")



            self.dsp_graph = pg.PlotWidget()

            self.dsp_graph.setBackground("#141e32")



            self.dsp_graph.showGrid(

                x=True,

                y=True,

                alpha=0.3

            )



            self.dsp_graph.setLabel(

                "left",

                "Voltage",

                units="V"

            )



            self.dsp_graph.setLabel(

                "bottom",

                "Sample"

            )



            self.dsp_graph.setTitle(

                "Digital Signal Processing",

                color="#55dce5",

                size="14pt"

            )



            self.dsp_graph.addLegend()



            self.dsp_original_curve = self.dsp_graph.plot(

                pen=pg.mkPen(

                    color="#55dce5",

                    width=2

                ),

                name="Original signal"

            )



            self.dsp_filtered_curve = self.dsp_graph.plot(

                pen=pg.mkPen(

                    color="#ffb454",

                    width=2

                ),

                name="Filtered signal"

            )



            dsp_graph_layout.addWidget(dsp_title)

            dsp_graph_layout.addWidget(self.dsp_graph)



            layout.addWidget(dsp_graph_panel, 1)



            self.dsp_filter.currentTextChanged.connect(

                self.update_dsp

            )



            self.dsp_low_cutoff.valueChanged.connect(

                self.update_dsp

            )



            self.dsp_high_cutoff.valueChanged.connect(

                self.update_dsp

            )



        # MEASUREMENTS



        elif name == "Measurements":



            description = QLabel(

                "Automatic measurement of signal parameters"

            )

            description.setObjectName("small_text")

            layout.addWidget(description)



            grid = QGridLayout()

            grid.setSpacing(12)



            measurement_panels = [

                ("FREQUENCY", "— Hz", "Signal frequency"),

                ("AMPLITUDE", "— V", "Half of peak-to-peak"),

                ("PEAK-TO-PEAK", "— V", "Maximum minus minimum"),

                ("MEAN", "— V", "Average voltage"),

                ("RMS", "— V", "Root mean square"),

                ("MINIMUM", "— V", "Minimum voltage"),

                ("MAXIMUM", "— V", "Maximum voltage"),

                ("SAMPLE RATE", "— Hz", "Sampling frequency")

            ]



            self.measurement_values = {}



            for i, data in enumerate(measurement_panels):



                panel, value_label = self.create_panel(*data)



                row = i // 2

                column = i % 2



                grid.addWidget(panel, row, column)



                self.measurement_values[data[0]] = value_label



            layout.addLayout(grid)



            info_panel = QFrame()

            info_panel.setObjectName("panel")



            info_layout = QVBoxLayout(info_panel)

            info_layout.setContentsMargins(

                15, 13, 15, 13

            )



            info_title = QLabel("MEASUREMENT INFORMATION")

            info_title.setObjectName("panel_title")



            self.measurement_status = QLabel(

                "Ожидание накопления данных..."

            )

            self.measurement_status.setObjectName("small_text")



            self.measurement_samples = QLabel(

                "Использовано отсчётов: 0"

            )

            self.measurement_samples.setObjectName("small_text")



            info_layout.addWidget(info_title)

            info_layout.addWidget(self.measurement_status)

            info_layout.addWidget(self.measurement_samples)



            layout.addWidget(info_panel)

            layout.addStretch()



        # GENERATOR CONTROL

        elif name == "Signal Generator":

            description = QLabel(
                
            )
            description.setObjectName("small_text")
            layout.addWidget(description)

            controls_panel = QFrame()
            controls_panel.setObjectName("panel")
            controls_layout = QVBoxLayout(controls_panel)
            controls_layout.setContentsMargins(18, 16, 18, 16)
            controls_layout.setSpacing(15)

            controls_title = QLabel("GENERATOR SETTINGS")
            controls_title.setObjectName("panel_title")
            controls_layout.addWidget(controls_title)

            settings_grid = QGridLayout()
            settings_grid.setHorizontalSpacing(14)
            settings_grid.setVerticalSpacing(12)

            waveform_label = QLabel("Waveform:")
            self.generator_waveform = QComboBox()
            self.generator_waveform.addItem("Sine", "SINE")
            self.generator_waveform.addItem("Square", "SQUARE")
            self.generator_waveform.addItem("Triangle", "TRIANGLE")
            self.generator_waveform.addItem("Sawtooth", "SAWTOOTH")

            frequency_label = QLabel("Frequency:")
            self.generator_frequency = QDoubleSpinBox()
            self.generator_frequency.setRange(0.5, 7.0)
            self.generator_frequency.setDecimals(2)
            self.generator_frequency.setSingleStep(0.5)
            self.generator_frequency.setValue(5.0)
            self.generator_frequency.setSuffix(" Hz")

            amplitude_label = QLabel("Amplitude:")
            self.generator_amplitude = QDoubleSpinBox()
            self.generator_amplitude.setRange(0.1, 2.4)
            self.generator_amplitude.setDecimals(2)
            self.generator_amplitude.setSingleStep(0.1)
            self.generator_amplitude.setValue(1.9)
            self.generator_amplitude.setSuffix(" V")

            settings_grid.addWidget(waveform_label, 0, 0)
            settings_grid.addWidget(self.generator_waveform, 0, 1)
            settings_grid.addWidget(frequency_label, 1, 0)
            settings_grid.addWidget(self.generator_frequency, 1, 1)
            settings_grid.addWidget(amplitude_label, 2, 0)
            settings_grid.addWidget(self.generator_amplitude, 2, 1)
            settings_grid.setColumnStretch(2, 1)
            controls_layout.addLayout(settings_grid)

            buttons_row = QHBoxLayout()
            buttons_row.setSpacing(10)

            self.generator_apply_button = QPushButton("APPLY SETTINGS")
            self.generator_apply_button.setStyleSheet(
                "QPushButton { background: #173c50; color: #55dce5; "
                "border: 1px solid #286078; border-radius: 6px; "
                "padding: 11px 16px; font-weight: bold; } "
                "QPushButton:hover { background: #20516a; }"
            )

            self.generator_start_button = QPushButton("START")
            self.generator_start_button.setStyleSheet(
                "QPushButton { background: #174c39; color: #65e6a8; "
                "border: 1px solid #267a58; border-radius: 6px; "
                "padding: 11px 20px; font-weight: bold; } "
                "QPushButton:hover { background: #206348; }"
            )

            self.generator_stop_button = QPushButton("STOP")
            self.generator_stop_button.setStyleSheet(
                "QPushButton { background: #542d38; color: #ff9eaa; "
                "border: 1px solid #814352; border-radius: 6px; "
                "padding: 11px 20px; font-weight: bold; } "
                "QPushButton:hover { background: #703b49; }"
            )

            buttons_row.addWidget(self.generator_apply_button)
            buttons_row.addWidget(self.generator_start_button)
            buttons_row.addWidget(self.generator_stop_button)
            buttons_row.addStretch()
            controls_layout.addLayout(buttons_row)

            layout.addWidget(controls_panel)

            status_panel = QFrame()
            status_panel.setObjectName("panel")
            status_layout = QVBoxLayout(status_panel)
            status_layout.setContentsMargins(18, 14, 18, 14)
            status_layout.setSpacing(8)

            status_title = QLabel("GENERATOR STATUS")
            status_title.setObjectName("panel_title")
            self.generator_status = QLabel(
                "Ожидание команды. Проверьте подключение Arduino."
            )
            self.generator_status.setWordWrap(True)
            self.generator_status.setStyleSheet("color: #a7b8d0;")

            self.generator_current_settings = QLabel(
                "SINE | 5.00 Hz | 1.90 V"
            )
            self.generator_current_settings.setObjectName("value")

            status_layout.addWidget(status_title)
            status_layout.addWidget(self.generator_status)
            status_layout.addWidget(self.generator_current_settings)
            layout.addWidget(status_panel)

            info_panel = QFrame()
            info_panel.setObjectName("panel")
            info_layout = QVBoxLayout(info_panel)
            info_layout.setContentsMargins(18, 14, 18, 14)

            info_title = QLabel("GENERATOR INFORMATION")
            info_title.setObjectName("panel_title")
            info_text = QLabel(
                "DAC: MCP4725 | Resolution: 12 bit | Output range: 0–5 V\n"
                "The generated signal is sampled by the Arduino ADC on input A0."
            )
            info_text.setWordWrap(True)
            info_text.setStyleSheet("color: #8192ad;")

            info_layout.addWidget(info_title)
            info_layout.addWidget(info_text)
            layout.addWidget(info_panel)
            layout.addStretch()

            self.generator_apply_button.clicked.connect(
                self.apply_generator_settings
            )
            self.generator_start_button.clicked.connect(
                self.start_generator
            )
            self.generator_stop_button.clicked.connect(
                self.stop_generator
            )

        # ОСТАЛЬНЫЕ РАЗДЕЛЫ



        else:



            panel = QFrame()

            panel.setObjectName("panel")



            panel_layout = QVBoxLayout(panel)



            message = QLabel(

                f"{name}\n\n"

                "This module is being developed.\n"

                "Its controls and functions will be added next."

            )



            message.setAlignment(Qt.AlignCenter)



            message.setStyleSheet(

                "font-size: 15px; color: #a7b8d0;"

            )



            panel_layout.addStretch()

            panel_layout.addWidget(message)

            panel_layout.addStretch()



            layout.addWidget(panel, 1)



        return page



    # ==============================

    # ПЕРЕКЛЮЧЕНИЕ СТРАНИЦ

    # ==============================



    def change_page(self, index):



        self.stack.setCurrentIndex(index)



        for i, button in enumerate(self.buttons):

            button.setChecked(i == index)



    # ==============================

    # ПОЛУЧЕНИЕ ДАННЫХ ARDUINO

    # ==============================



    def read_data(self):



        if self.serial is None:

            return



        try:



            waiting = self.serial.in_waiting



            if waiting > 0:



                received = self.serial.read(waiting)

                self.serial_buffer.extend(received)

                self.total_bytes += len(received)



            new_data = False



            while b"\n" in self.serial_buffer:



                raw_line, _, remaining = (

                    self.serial_buffer.partition(b"\n")

                )



                self.serial_buffer = bytearray(remaining)



                line = raw_line.decode(

                    "utf-8",

                    errors="ignore"

                ).strip()



                if not line or "," not in line:

                    continue



                try:



                    timestamp_text, adc_text = line.split(",", 1)



                    timestamp = int(timestamp_text)

                    adc = int(adc_text)



                    if not 0 <= adc <= 1023:

                        continue



                    self.timestamps.append(timestamp)

                    self.adc_values.append(adc)



                    self.total_samples += 1

                    new_data = True



                except ValueError:

                    continue



            if new_data:

                self.update_graphs()



        except serial.SerialException as error:



            self.connection.setText("● CONNECTION LOST")



            self.connection.setStyleSheet(

                "color: #e76f6f; font-weight: bold;"

            )



            self.dashboard_status.setText(

                f"Ошибка передачи: {error}"

            )



            self.timer.stop()



    # ==============================

    # ОБНОВЛЕНИЕ ГРАФИКОВ

    # ==============================



    def update_graphs(self):



        if not self.adc_values:

            return



        adc = np.asarray(

            list(self.adc_values),

            dtype=float

        )



        voltage = adc * REFERENCE_VOLTAGE / 1023.0



        visible = voltage[-DISPLAY_POINTS:]

        x_values = np.arange(len(visible))



        # DASHBOARD



        self.dashboard_curve.setData(

            x_values,

            visible

        )



        # OSCILLOSCOPE



        self.osc_curve.setData(

            x_values,

            visible

        )



        minimum = float(np.min(visible))

        maximum = float(np.max(visible))



        amplitude = (maximum - minimum) / 2.0



        self.osc_min.setText(

            f"MIN: {minimum:.2f} V"

        )



        self.osc_max.setText(

            f"MAX: {maximum:.2f} V"

        )



        self.osc_amplitude.setText(

            f"AMPLITUDE: {amplitude:.2f} V"

        )



        self.dashboard_values[3].setText(

            f"{amplitude:.2f} V"

        )



        self.dashboard_status.setText(

            "Signal received and displayed in real time."

        )



        self.osc_status.setText(

            f"Порт: {PORT} | Получено байтов: "

            f"{self.total_bytes} | Прочитано точек: "

            f"{self.total_samples}"

        )



        self.osc_samples.setText(

            f"Отображается точек: {len(visible)} "

            f"| Всего получено: {self.total_samples}"

        )



        # FFT ANALYZER



        self.update_spectrum()



        # DSP LABORATORY



        self.update_dsp()



        # MEASUREMENTS



        self.update_measurements()



    # ==============================

    # РАСЧЕТ ЧАСТОТЫ ДИСКРЕТИЗАЦИИ

    # ==============================



    def calculate_sample_rate(self, timestamps):



        if len(timestamps) < 2:

            return None



        differences = (

            (timestamps[1:] - timestamps[:-1])

            & np.uint64(0xFFFFFFFF)

        )



        valid = differences[

            (differences > 0) &

            (differences < 100000)

        ]



        if len(valid) < 2:

            return None



        average_interval = np.median(valid) / 1_000_000.0



        if average_interval <= 0:

            return None



        return 1.0 / average_interval



    # ==============================

    # ИЗМЕРЕНИЕ ЧАСТОТЫ СИГНАЛА

    # ==============================



    def calculate_signal_frequency(

        self,

        signal,

        timestamps,

        sample_rate

    ):



        if len(signal) < 4 or sample_rate is None:

            return None



        # Убираем постоянное смещение

        centered = signal - np.mean(signal)



        # Находим переходы через ноль снизу вверх

        crossings = np.where(

            (centered[:-1] <= 0) &

            (centered[1:] > 0)

        )[0]



        if len(crossings) < 2:

            return None



        # Интерполяция положения перехода

        crossing_positions = []



        for index in crossings:



            y1 = centered[index]

            y2 = centered[index + 1]



            if y2 == y1:

                fraction = 0.0

            else:

                fraction = -y1 / (y2 - y1)



            position = index + fraction

            crossing_positions.append(position)



        crossing_positions = np.asarray(

            crossing_positions,

            dtype=float

        )



        periods = np.diff(crossing_positions)



        # Исключаем слишком короткие и слишком длинные интервалы

        periods = periods[

            (periods > 2) &

            (periods < len(signal) / 2)

        ]



        if len(periods) == 0:

            return None



        average_period = float(np.mean(periods))



        if average_period <= 0:

            return None



        return sample_rate / average_period



    # ИЗМЕРЕНИЯ ПАРАМЕТРОВ СИГНАЛА



    def update_measurements(self):



        if not hasattr(self, "measurement_values"):

            return



        if len(self.adc_values) < MEASUREMENT_SAMPLES:



            self.measurement_status.setText(

                f"Накопление данных: "

                f"{len(self.adc_values)} / "

                f"{MEASUREMENT_SAMPLES} отсчётов"

            )

            return



        timestamps = np.asarray(

            list(self.timestamps)[-MEASUREMENT_SAMPLES:],

            dtype=np.uint64

        )



        adc = np.asarray(

            list(self.adc_values)[-MEASUREMENT_SAMPLES:],

            dtype=float

        )



        voltage = adc * REFERENCE_VOLTAGE / 1023.0



        # Основные статистические характеристики



        minimum = float(np.min(voltage))

        maximum = float(np.max(voltage))



        peak_to_peak = maximum - minimum

        amplitude = peak_to_peak / 2.0



        mean_value = float(np.mean(voltage))



        rms_value = float(

            np.sqrt(np.mean(np.square(voltage)))

        )



        # Частота дискретизации



        sample_rate = self.calculate_sample_rate(

            timestamps

        )



        # Частота исходного сигнала



        frequency = self.calculate_signal_frequency(

            voltage,

            timestamps,

            sample_rate

        )



        # Вывод результатов



        values = {

            "AMPLITUDE": f"{amplitude:.3f} V",

            "PEAK-TO-PEAK": f"{peak_to_peak:.3f} V",

            "MEAN": f"{mean_value:.3f} V",

            "RMS": f"{rms_value:.3f} V",

            "MINIMUM": f"{minimum:.3f} V",

            "MAXIMUM": f"{maximum:.3f} V"

        }



        for key, value in values.items():

            self.measurement_values[key].setText(value)



        if sample_rate is not None:



            self.measurement_values["SAMPLE RATE"].setText(

                f"{sample_rate:.1f} Hz"

            )



        else:



            self.measurement_values["SAMPLE RATE"].setText(

                "— Hz"

            )



        if frequency is not None:



            self.measurement_values["FREQUENCY"].setText(

                f"{frequency:.2f} Hz"

            )



            self.measurement_status.setText(

                "Signal measurements updated successfully."

            )



        else:



            self.measurement_values["FREQUENCY"].setText(

                "— Hz"

            )



            self.measurement_status.setText(

                "Недостаточно периодов для определения частоты."

            )



        self.measurement_samples.setText(

            f"Использовано отсчётов: {len(voltage)} "

            f"| Всего получено: {self.total_samples}"

        )





    # ЦИФРОВАЯ ОБРАБОТКА СИГНАЛА





    def update_dsp(self):



        if not hasattr(self, "dsp_graph"):

            return



        if len(self.adc_values) < DSP_SAMPLES:

            self.dsp_status.setText(

                f"Накопление данных: {len(self.adc_values)} "

                f"/ {DSP_SAMPLES} отсчётов"

            )

            return



        timestamps = np.asarray(

            list(self.timestamps)[-DSP_SAMPLES:],

            dtype=np.uint64

        )



        adc = np.asarray(

            list(self.adc_values)[-DSP_SAMPLES:],

            dtype=float

        )



        original_signal = (

            adc * REFERENCE_VOLTAGE / 1023.0

        )



        sample_rate = self.calculate_sample_rate(

            timestamps

        )



        if sample_rate is None:

            self.dsp_status.setText(

                "Невозможно определить частоту дискретизации."

            )

            return



        nyquist = sample_rate / 2.0



        filter_type = self.dsp_filter.currentText()



        low_cutoff = self.dsp_low_cutoff.value()

        high_cutoff = self.dsp_high_cutoff.value()



        filtered_signal = original_signal.copy()



        try:



            if filter_type == "Low-pass":



                cutoff = high_cutoff



                if cutoff >= nyquist:

                    raise ValueError(

                        "Частота среза должна быть меньше "

                        "частоты Найквиста."

                    )



                sos = butter(

                    4,

                    cutoff,

                    btype="lowpass",

                    fs=sample_rate,

                    output="sos"

                )



                filtered_signal = sosfiltfilt(

                    sos,

                    original_signal

                )



                filter_description = (

                    f"Low-pass | Cutoff: {cutoff:.1f} Hz"

                )



            elif filter_type == "High-pass":



                cutoff = low_cutoff



                if cutoff >= nyquist:

                    raise ValueError(

                        "Частота среза должна быть меньше "

                        "частоты Найквиста."

                    )



                sos = butter(

                    4,

                    cutoff,

                    btype="highpass",

                    fs=sample_rate,

                    output="sos"

                )



                filtered_signal = sosfiltfilt(

                    sos,

                    original_signal

                )



                filter_description = (

                    f"High-pass | Cutoff: {cutoff:.1f} Hz"

                )



            elif filter_type == "Band-pass":



                if low_cutoff >= high_cutoff:

                    raise ValueError(

                        "Нижняя частота должна быть меньше верхней."

                    )



                if high_cutoff >= nyquist:

                    raise ValueError(

                        "Верхняя частота должна быть меньше "

                        "частоты Найквиста."

                    )



                sos = butter(

                    4,

                    [low_cutoff, high_cutoff],

                    btype="bandpass",

                    fs=sample_rate,

                    output="sos"

                )



                filtered_signal = sosfiltfilt(

                    sos,

                    original_signal

                )



                filter_description = (

                    f"Band-pass | "

                    f"{low_cutoff:.1f}–{high_cutoff:.1f} Hz"

                )



            elif filter_type == "Noise reduction":



                window_size = 7



                kernel = np.ones(window_size) / window_size



                filtered_signal = np.convolve(

                    original_signal,

                    kernel,

                    mode="same"

                )



                filter_description = (

                    f"Noise reduction | "

                    f"Moving average: {window_size} samples"

                )



            else:



                filter_description = "Bypass | No filtering"



            x_values = np.arange(len(original_signal))



            self.dsp_original_curve.setData(

                x_values,

                original_signal

            )



            self.dsp_filtered_curve.setData(

                x_values,

                filtered_signal

            )



            self.dsp_graph.setXRange(

                0,

                len(original_signal) - 1,

                padding=0

            )



            minimum = min(

                float(np.min(original_signal)),

                float(np.min(filtered_signal))

            )



            maximum = max(

                float(np.max(original_signal)),

                float(np.max(filtered_signal))

            )



            margin = max((maximum - minimum) * 0.2, 0.1)



            self.dsp_graph.setYRange(

                minimum - margin,

                maximum + margin,

                padding=0

            )



            self.dsp_status.setText(

                f"{filter_description} | "

                f"Sampling rate: {sample_rate:.1f} Hz | "

                f"Nyquist: {nyquist:.1f} Hz"

            )



        except ValueError as error:



            self.dsp_status.setText(

                f"Filter settings error: {error}"

            )



            self.dsp_filtered_curve.setData([], [])



        except Exception as error:



            self.dsp_status.setText(

                f"DSP processing error: {error}"

            )



            self.dsp_filtered_curve.setData([], [])





    # FFT - БЫСТРОЕ ПРЕОБРАЗОВАНИЕ ФУРЬЕ





    def update_spectrum(self):



        if len(self.adc_values) < FFT_SAMPLES:

            self.spectrum_status.setText(

                f"Накопление данных: {len(self.adc_values)} "

                f"/ {FFT_SAMPLES} точек"

            )

            return



        timestamps = np.asarray(

            list(self.timestamps)[-FFT_SAMPLES:],

            dtype=np.uint64

        )



        adc = np.asarray(

            list(self.adc_values)[-FFT_SAMPLES:],

            dtype=float

        )



        voltage = adc * REFERENCE_VOLTAGE / 1023.0



        differences = (

            (timestamps[1:] - timestamps[:-1])

            & np.uint64(0xFFFFFFFF)

        )



        valid = differences[

            (differences > 0) &

            (differences < 100000)

        ]



        if len(valid) < FFT_SAMPLES // 2:

            self.spectrum_status.setText(

                "Недостаточно корректных временных отметок."

            )

            return



        average_interval = np.median(valid) / 1_000_000.0



        if average_interval <= 0:

            return



        sample_rate = 1.0 / average_interval



        signal = voltage - np.mean(voltage)



        window = np.hanning(len(signal))

        windowed_signal = signal * window



        spectrum = np.fft.rfft(

            windowed_signal,

            n=FFT_SIZE

        )



        frequencies = np.fft.rfftfreq(

            FFT_SIZE,

            d=1.0 / sample_rate

        )



        amplitudes = (

            2.0 * np.abs(spectrum) / np.sum(window)

        )



        amplitudes[0] = 0



        peak_index = int(np.argmax(amplitudes[1:]) + 1)



        main_frequency = frequencies[peak_index]

        main_amplitude = amplitudes[peak_index]



        self.spectrum_curve.setData(

            frequencies,

            amplitudes

        )



        max_frequency = min(100.0, sample_rate / 2.0)



        self.spectrum_graph.setXRange(

            0,

            max_frequency,

            padding=0

        )



        self.spectrum_graph.setYRange(

            0,

            max(float(np.max(amplitudes)) * 1.2, 0.05),

            padding=0

        )



        self.spectrum_frequency.setText(

            f"Основная частота: {main_frequency:.2f} Hz"

        )



        self.spectrum_amplitude.setText(

            f"Амплитуда основной гармоники: "

            f"{main_amplitude:.3f} V"

        )



        self.spectrum_rate.setText(

            f"Частота дискретизации: {sample_rate:.1f} Hz"

        )



        self.spectrum_status.setText(

            "FFT analysis active | "

            f"Используется {FFT_SAMPLES} отсчётов"

        )



        self.dashboard_values[2].setText(

            f"{main_frequency:.2f} Hz"

        )



    # ЗАКРЫТИЕ ПРИЛОЖЕНИЯ





    # УПРАВЛЕНИЕ ГЕНЕРАТОРОМ

    def send_generator_command(self, command):
        if self.serial is None or not self.serial.is_open:
            self.generator_status.setText(
                "Ошибка: Arduino не подключена. Проверьте COM-порт."
            )
            return False

        try:
            self.serial.write((command + "\n").encode("utf-8"))
            self.serial.flush()
            return True
        except (serial.SerialException, OSError) as error:
            self.generator_status.setText(
                f"Ошибка отправки команды: {error}"
            )
            return False

    def apply_generator_settings(self):
        waveform = self.generator_waveform.currentData()
        frequency = self.generator_frequency.value()
        amplitude = self.generator_amplitude.value()

        command = f"SET,{waveform},{frequency:.2f},{amplitude:.2f}"
        if self.send_generator_command(command):
            self.generator_current_settings.setText(
                f"{waveform} | {frequency:.2f} Hz | {amplitude:.2f} V"
            )
            self.generator_status.setText(
                "Команда настройки отправлена на Arduino."
            )

    def start_generator(self):
        waveform = self.generator_waveform.currentData()
        frequency = self.generator_frequency.value()
        amplitude = self.generator_amplitude.value()

        settings_command = (
            f"SET,{waveform},{frequency:.2f},{amplitude:.2f}"
        )
        if not self.send_generator_command(settings_command):
            return

        if self.send_generator_command("RUN,1"):
            self.generator_current_settings.setText(
                f"{waveform} | {frequency:.2f} Hz | {amplitude:.2f} V"
            )
            self.generator_status.setText(
                "Команды настройки и запуска отправлены на Arduino. "
                "Проверьте изменение сигнала на осциллографе."
            )

    def stop_generator(self):
        if self.send_generator_command("RUN,0"):
            self.generator_status.setText(
                "Команда остановки отправлена на Arduino."
            )

    def closeEvent(self, event):



        self.timer.stop()



        if self.serial is not None:

            if self.serial.is_open:

                self.serial.close()



        event.accept()







# ЗАПУСК





if __name__ == "__main__":



    app = QApplication(sys.argv)



    window = SignalDoctor()

    window.show()



    sys.exit(app.exec())