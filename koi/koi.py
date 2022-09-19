import random
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage
from krita import DockWidget, Krita
from urllib import request
import requests
import json
from io import BytesIO
from zipfile import ZipFile
import re


class DoubleSlider(QSlider):

    # create our our signal that we can connect to if necessary
    doubleValueChanged = pyqtSignal(float)

    def __init__(self, decimals=2, *args, **kargs):
        super().__init__(Qt.Horizontal)
        self._multi = 10**decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def emitDoubleValueChanged(self):
        value = float(super(DoubleSlider, self).value()) / self._multi
        self.doubleValueChanged.emit(value)

    def value(self):
        return float(super(DoubleSlider, self).value()) / self._multi

    def setMinimum(self, value):
        return super(DoubleSlider, self).setMinimum(value * self._multi)

    def setMaximum(self, value):
        return super(DoubleSlider, self).setMaximum(value * self._multi)

    def setSingleStep(self, value):
        return super(DoubleSlider, self).setSingleStep(int(value * self._multi))

    def singleStep(self):
        return float(super(DoubleSlider, self).singleStep()) / self._multi

    def setValue(self, value):
        super(DoubleSlider, self).setValue(int(value * self._multi))


# Widget that combines a slider and a spinbox
class DoubleSliderSpinBox(QWidget):
    def __init__(self, parent=None):
        super(DoubleSliderSpinBox, self).__init__(parent)

        self.slider = DoubleSlider()
        self.spinbox = QDoubleSpinBox()

        self.slider.doubleValueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)

        layout = QHBoxLayout()
        layout.addWidget(self.slider)
        layout.addWidget(self.spinbox)

        # Remove all margins etc
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    def setMinimum(self, value):
        self.slider.setMinimum(value)
        self.spinbox.setMinimum(value)

    def setMaximum(self, value):
        self.slider.setMaximum(value)
        self.spinbox.setMaximum(value)

    def setSingleStep(self, value):
        self.slider.setSingleStep(value)
        self.spinbox.setSingleStep(value)

    def setValue(self, value):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def value(self):
        return self.slider.value()


class SliderSpinBox(QWidget):
    def __init__(self, parent=None):
        super(SliderSpinBox, self).__init__(parent)

        self.slider = QSlider(Qt.Horizontal)
        self.spinbox = QSpinBox()

        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)

        layout = QHBoxLayout()
        layout.addWidget(self.slider)
        layout.addWidget(self.spinbox)

        # Remove all margins etc
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    def setMinimum(self, value):
        self.slider.setMinimum(value)
        self.spinbox.setMinimum(value)

    def setMaximum(self, value):
        self.slider.setMaximum(value)
        self.spinbox.setMaximum(value)

    def setSingleStep(self, value):
        self.slider.setSingleStep(value)
        self.spinbox.setSingleStep(value)

    def setValue(self, value):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def value(self):
        return self.slider.value()


class SeedSpinBox(QWidget):
    # It's a normal spinbox, but it has a checkbox to enable/disable randomization
    def __init__(self, parent=None):
        super(SeedSpinBox, self).__init__(parent)

        self.checkbox = QCheckBox()
        self.spinbox = QSpinBox()

        # set the min and max values for the spinbox
        self.spinbox.setMinimum(0)
        self.spinbox.setMaximum(999999999)

        # Set the text of the checkbox to "Random"
        self.checkbox.setText("Random")

        layout = QHBoxLayout()
        layout.addWidget(self.spinbox)
        layout.addWidget(self.checkbox)

        # Remove all margins etc
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    def getValue(self):
        if self.checkbox.isChecked():
            self.spinbox.setValue(random.randint(0, 999999999))
        return self.spinbox.value()


class Koi(DockWidget):
    def __init__(self):
        """
        This sets up a basic user interface to interact with.

        TODO/FIXME: Adopt a better approach for managing the UI.
        """
        super().__init__()
        self.ITER = 0

        self.setWindowTitle("Koi")

        # Main WIdget ===
        self.main_widget = QWidget(self)
        self.main_widget.setLayout(QVBoxLayout())
        self.setWidget(self.main_widget)

        # Input & Prompt Settings ===
        self.input_widget = QWidget(self.main_widget)

        self.input_layout = QFormLayout()

        self.prompt = QPlainTextEdit(self.input_widget)
        self.prompt.setPlaceholderText("Describe your end goal...")
        self.prompt.setPlainText(
            "A beautiful mountain landscape in the style of greg rutkowski, oils on canvas."
        )

        self.prompt_scale = DoubleSliderSpinBox(self.input_widget)
        self.prompt_scale.setMinimum(0)
        self.prompt_scale.setMaximum(25)
        self.prompt_scale.setValue(16.5)

        self.steps = SliderSpinBox(self.input_widget)
        self.steps.setMinimum(1)
        self.steps.setMaximum(100)
        self.steps.setValue(60)

        self.image_strength = DoubleSliderSpinBox(self.input_widget)
        self.image_strength.setMinimum(0)
        self.image_strength.setMaximum(1)
        self.image_strength.setValue(0.5)

        self.rescaling = DoubleSliderSpinBox(self.input_widget)
        self.rescaling.setMinimum(-4)
        self.rescaling.setMaximum(4)
        self.rescaling.setValue(0)

        self.seed = SeedSpinBox(self.input_widget)

        self.input_layout.addRow("Prompt", self.prompt)
        self.input_layout.addRow("Prompt Scale", self.prompt_scale)
        self.input_layout.addRow("Image strength", self.image_strength)
        self.input_layout.addRow("Rescaling", self.rescaling)
        self.input_layout.addRow("Steps", self.steps)
        self.input_layout.addRow("Seed", self.seed)

        self.input_widget.setLayout(self.input_layout)

        self.main_widget.layout().addWidget(self.input_widget)

        # Dream button ===
        self.submit = QPushButton(self.main_widget)
        self.submit.setText("Submit")
        self.submit.clicked.connect(self.submit_job)

        self.main_widget.layout().addWidget(self.submit)

        # Backend settings ===

        self.backend_settings = QWidget(self.main_widget)
        self.backend_settings_layout = QFormLayout()

        self.session_token = QLineEdit(self.backend_settings)
        self.session_token.setPlaceholderText("Session Token")
        self.session_token.setText("")

        self.worker_id = QLineEdit(self.backend_settings)
        self.worker_id.setPlaceholderText("Worker ID")
        self.worker_id.setText("")

        self.backend_settings_layout.addRow("Session Token", self.session_token)
        self.backend_settings_layout.addRow("Worker ID", self.worker_id)

        self.backend_settings.setLayout(self.backend_settings_layout)
        self.main_widget.layout().addWidget(self.backend_settings)

    def canvasChanged(self, canvas):
        """
        This function must exists per Krita documentation.
        """
        pass

    def _prompt_text(self):
        return self.prompt.toPlainText().replace("\n", " ")

    def _next_layer_id(self):
        self.ITER += 1
        return self.ITER

    def _safe_layer_name(self, name):
        return re.sub("[^A-Za-z0-9-_]+", "", name.replace(" ", "_"))

    def _add_paint_layer(self, doc, root, bytes, name, x, y, w, h, rescaling):

        returned_file = QImage.fromData(bytes)

        multiplier = 2**rescaling

        returned_file = returned_file.scaled(
            int(w / multiplier),
            int(h / multiplier),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )

        dream_layer = doc.createNode(
            f"{self._safe_layer_name(name)}-{self._next_layer_id()}", "paintLayer"
        )
        root.addChildNode(dream_layer, None)

        # get a pointer to the image's bits and add them to the new layer
        ptr = returned_file.bits()
        ptr.setsize(returned_file.byteCount())
        dream_layer.setPixelData(
            QByteArray(ptr.asstring()),
            x,
            y,
            int(w / multiplier),
            int(h / multiplier),
        )

    def layer2buffer(self, rescaling):
        """
        Turns the current active layer into a I/O Buffer so that it can be sent over HTTP.
        """
        # get current document
        currentDocument = Krita.instance().activeDocument()

        selection = currentDocument.selection()
        x = selection.x()
        y = selection.y()

        multiplier = 2**rescaling

        real_im_width = int(int(selection.width() * multiplier) / 64) * 64
        real_im_height = int(int(selection.height() * multiplier) / 64) * 64

        original_width = int(real_im_width / multiplier)
        original_height = int(real_im_height / multiplier)

        # get current layer
        currentLayer = currentDocument.activeNode()

        # get the pixel data
        pixelData = currentLayer.pixelData(x, y, original_width, original_height)

        # construct QImage
        oi = QImage(pixelData, original_width, original_height, QImage.Format_RGBA8888)

        # Scale
        qImage = oi.scaled(
            real_im_width, real_im_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )

        qImage = qImage.rgbSwapped()

        # now make a buffer and save the image into it
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        qImage.save(buffer, format="PNG")

        # write the data into a buffer and jump to start of file
        image_byte_buffer = BytesIO()
        image_byte_buffer.write(buffer.data())
        image_byte_buffer.read()
        buffer.close()
        image_byte_buffer.seek(0)

        # return bytes
        return image_byte_buffer.read(), x, y, real_im_width, real_im_height

    def submit_job(self, a):
        session_token = self.session_token.text()
        worker_id = self.worker_id.text()

        rescaling = self.rescaling.value()
        image_bytes, x, y, width, height = self.layer2buffer(rescaling)

        prompt = self._prompt_text()
        scale = self.prompt_scale.value()
        steps = self.steps.value()
        denoising_strength = 1 - self.image_strength.value()
        seed = self.seed.getValue()

        doc = Krita.instance().activeDocument()
        root = doc.rootNode()

        # create a new job
        job = KoiJob(
            {
                "session_token": session_token,
                "worker": worker_id,
                "image_bytes": image_bytes,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "prompt": prompt,
                "scale": scale,
                "ddim_steps": steps,
                "denoising_strength": denoising_strength,
                "doc": doc,
                "root": root,
                "seed": seed,
                "rescaling": rescaling,
                "cropping": "center",
            }
        )
        job.finished.connect(self.on_job_finished)
        job.run()

    def on_job_finished(self, job):
        if job["status"] == "failed":
            return

        self._add_paint_layer(
            job["doc"],
            job["root"],
            job["image_bytes"],
            job["prompt"],
            job["x"],
            job["y"],
            job["width"],
            job["height"],
            job["rescaling"],
        )

        job["doc"].refreshProjection()


class KoiJob(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parameters, parent=None):
        super().__init__(parent)

        self.parameters = parameters

    def run(self):
        session_token = self.parameters["session_token"]

        # create session
        session = requests.Session()

        # set session token cookie
        session.cookies.set("session_id", session_token)

        # upload image as a post request
        image_bytes = self.parameters["image_bytes"]

        images_bytes_buffer = BytesIO()
        images_bytes_buffer.write(image_bytes)
        images_bytes_buffer.seek(0)

        files = {"file": images_bytes_buffer}

        # send post request
        response = session.post(
            "https://honkies.huestudios.xyz/api/v1/upload_image",
            files=files,
        )

        # Get json
        response_json = response.json()
        filename = response_json["filename"]

        job_id = str(random.randint(0, 1000000))

        # Submit job
        jobs_data = [
            {
                "id": job_id,
                "worker": 0,
                "parameters": {
                    "prompt": self.parameters["prompt"],
                    "scale": self.parameters["scale"],
                    "ddim_steps": self.parameters["ddim_steps"],
                    "width": self.parameters["width"],
                    "height": self.parameters["height"],
                    "seed": self.parameters["seed"],
                    "init_image": filename,
                    "denoising_strength": self.parameters["denoising_strength"],
                    "cropping": self.parameters["cropping"],
                },
            }
        ]

        response = session.get(
            "https://honkies.huestudios.xyz/api/v1/enqueue",
            params={
                "jobs_data": json.dumps(jobs_data),
                "pod_host_id": self.parameters["worker"],
            },
        )

        while True:
            # Poll job status
            response = session.get(
                f"https://honkies.huestudios.xyz/api/v1/jobs/{job_id}",
                params={"pod_host_id": self.parameters["worker"]},
            )

            response_json = response.json()

            if response_json["status"] == "failed":
                self.finished.emit({"status": "failed"})
                return

            if response_json["status"] == "complete":
                break

            time.sleep(1)

        image_io = BytesIO()
        with session.get(
            f"https://honkies.huestudios.xyz/api/v1/jobs/{job_id}/image",
            params={"pod_host_id": self.parameters["worker"]},
            stream=True,
        ) as response:
            for chunk in response.iter_content(chunk_size=8192):
                image_io.write(chunk)

        image_io.seek(0)

        self.finished.emit(
            {
                "status": "complete",
                "image_bytes": image_io.read(),
                "prompt": self.parameters["prompt"],
                "width": self.parameters["width"],
                "height": self.parameters["height"],
                "x": self.parameters["x"],
                "y": self.parameters["y"],
                "doc": self.parameters["doc"],
                "root": self.parameters["root"],
                "rescaling": self.parameters["rescaling"],
            }
        )


# v05ae4cxgn2yc5
# 36615c8f04ee0020529109944a9902ec73d2db00347f7128e24e4045a3742b5
