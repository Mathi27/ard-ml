#!/usr/bin/env python3
"""
Teachable Machine -> Serial (OS-independent version)
======================================================

Cross-platform (Windows / macOS / Linux) replacement for the Windows-only
TeachableMachine2Serial.exe app.

What it does:
  1. Looks for "converted_keras.zip" next to this script (the file you export
     from Teachable Machine -> Tensorflow -> Keras).
  2. Extracts it (once) into a "converted_keras" folder.
  3. Loads the Keras model (keras_model.h5) and the labels (labels.txt).
  4. Opens your webcam, grabs frames, runs inference, and PRINTS which class
     was detected (e.g. "Class 1", "Class 2", "Class 3" - whatever names you
     gave them in Teachable Machine) along with the confidence.
  5. Optionally sends the detected class name over a Serial port to an
     Arduino, same as the original app.

Requirements (install once):
    pip install tensorflow tf_keras opencv-python pillow numpy pyserial

Note on Apple Silicon Macs: use `pip install tensorflow-macos tensorflow-metal`
instead of plain `tensorflow` if the normal install fails.

Usage:
    python teachable_machine_to_serial.py

Press "q" in the preview window (or Ctrl+C in the terminal) to quit.
"""

import os
import sys
import time
import zipfile
import pathlib

import numpy as np
import cv2
from PIL import Image

# Teachable Machine exports Keras 2 .h5 models, which Keras 3 (the default
# in TensorFlow >= 2.16) can't load. tf_keras is the legacy Keras 2 package.
from tf_keras.models import load_model
from tf_keras.layers import DepthwiseConv2D as _KerasDepthwiseConv2D


class _PatchedDepthwiseConv2D(_KerasDepthwiseConv2D):
    """
    Teachable Machine's exported .h5 models were saved with an older Keras
    that wrote a 'groups' argument into DepthwiseConv2D's config. Newer
    Keras/TensorFlow versions reject unknown kwargs and raise:
        ValueError: Unrecognized keyword arguments ... {'groups': 1}
    This subclass just discards that argument so the old model file still
    loads correctly, without needing to downgrade TensorFlow.
    """

    def __init__(self, *args, **kwargs):
        kwargs.pop("groups", None)
        super().__init__(*args, **kwargs)


try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


# ----------------------------------------------------------------------
# Paths - all built with pathlib / os.path so they work on any OS
# ----------------------------------------------------------------------
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ZIP_PATH = SCRIPT_DIR / "converted_keras.zip"
EXTRACT_DIR = SCRIPT_DIR / "converted_keras"

# Folders macOS's Finder/Archive Utility injects into zips - always skip these
IGNORED_DIR_NAMES = {"__MACOSX"}


def _is_ignored(path: pathlib.Path) -> bool:
    return any(part in IGNORED_DIR_NAMES or part.startswith(".") for part in path.parts)


def find_model_files():
    """
    Recursively search EXTRACT_DIR for a *.h5 model file and a labels.txt
    file, regardless of what subfolder they ended up in or what the .h5 is
    named (Teachable Machine usually calls it keras_model.h5, but this
    doesn't assume that). Skips macOS's __MACOSX junk folder.
    """
    h5_candidates = [
        p for p in EXTRACT_DIR.rglob("*.h5") if not _is_ignored(p)
    ]
    label_candidates = [
        p for p in EXTRACT_DIR.rglob("labels.txt") if not _is_ignored(p)
    ]

    if not h5_candidates or not label_candidates:
        sys.exit(
            "ERROR: Extracted the zip but couldn't find a *.h5 model file "
            "and/or labels.txt inside it (ignoring __MACOSX). Make sure you "
            "exported a 'Keras' model (not TensorFlow.js or TFLite) from "
            f"Teachable Machine.\nLooked inside: {EXTRACT_DIR}"
        )

    if len(h5_candidates) > 1:
        print(f"Note: found multiple .h5 files, using the first one: {h5_candidates[0]}")
    if len(label_candidates) > 1:
        print(f"Note: found multiple labels.txt files, using the first one: {label_candidates[0]}")

    return h5_candidates[0], label_candidates[0]


def extract_model_if_needed():
    """Extract converted_keras.zip once, on any OS, then locate the model
    and labels files inside it (wherever they landed)."""
    if not ZIP_PATH.exists():
        sys.exit(
            f"ERROR: Could not find '{ZIP_PATH.name}' next to this script.\n"
            f"Export your model from Teachable Machine (Tensorflow -> Keras), "
            f"and save/rename the downloaded zip to exactly 'converted_keras.zip' "
            f"in this folder:\n  {SCRIPT_DIR}"
        )

    if not EXTRACT_DIR.exists():
        print(f"Extracting {ZIP_PATH.name} ...")
        EXTRACT_DIR.mkdir(exist_ok=True)
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            zf.extractall(EXTRACT_DIR)

    return find_model_files()


def load_labels(labels_path: pathlib.Path):
    """
    labels.txt from Teachable Machine looks like:
        0 Class 1 - r
        1 Class 2
        2 Class 3
    Returns a list ["Class 1", "Class 2", "Class 3"] indexed by class id.
    """
    labels = []
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # split off the leading index number, keep the rest as the name
            parts = line.split(" ", 1)
            name = parts[1].strip() if len(parts) > 1 else parts[0]
            labels.append(name)
    return labels


def preprocess(frame_bgr):
    """
    Reproduce Teachable Machine's standard preprocessing:
    resize to 224x224, convert to RGB, normalize to [-1, 1].
    """
    img = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = img.resize((224, 224), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32)
    arr = (arr / 127.5) - 1.0
    return np.expand_dims(arr, axis=0)


def pick_serial_port():
    """Cross-platform serial port picker (works on Windows COM ports,
    macOS /dev/tty.* and Linux /dev/ttyUSB*/ttyACM*)."""
    if not SERIAL_AVAILABLE:
        return None

    use_serial = input("Send results to Arduino over Serial? [y/N]: ").strip().lower()
    if use_serial != "y":
        return None

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found. Continuing without Serial.")
        return None

    print("\nAvailable serial ports:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device}  ({p.description})")

    choice = input(f"Select a port [0-{len(ports) - 1}]: ").strip()
    try:
        idx = int(choice)
        device = ports[idx].device
    except (ValueError, IndexError):
        print("Invalid choice. Continuing without Serial.")
        return None

    try:
        ser = serial.Serial(device, 9600, timeout=1)
        time.sleep(2)  # give the Arduino time to reset after the port opens
        print(f"Connected to {device}\n")
        return ser
    except serial.SerialException as e:
        print(f"Could not open {device}: {e}. Continuing without Serial.")
        return None


def main():
    model_path, labels_path = extract_model_if_needed()

    print(f"Loading model from {model_path} ...")
    model = load_model(
        model_path,
        compile=False,
        custom_objects={"DepthwiseConv2D": _PatchedDepthwiseConv2D},
    )
    labels = load_labels(labels_path)
    print(f"Loaded {len(labels)} classes: {labels}\n")

    ser = pick_serial_port()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit(
            "ERROR: Could not open the webcam. Make sure no other program "
            "(e.g. Teachable Machine in the browser) is currently using it."
        )

    last_sent = None
    print("Running. Press 'q' in the preview window (or Ctrl+C here) to quit.\n")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read from webcam.")
                break

            data = preprocess(frame)
            predictions = model.predict(data, verbose=0)[0]
            class_id = int(np.argmax(predictions))
            class_name = labels[class_id]
            confidence = float(predictions[class_id])

            print(f"Detected: {class_name}  (confidence: {confidence:.2%})")

            if ser is not None and class_name != last_sent:
                ser.write((class_name + "\n").encode("utf-8"))
                last_sent = class_name

            # Debug preview window
            label_text = f"{class_name} ({confidence:.0%})"
            cv2.putText(
                frame, label_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2,
            )
            cv2.imshow("Teachable Machine to Serial - press 'q' to quit", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if ser is not None:
            ser.close()


if __name__ == "__main__":
    main()