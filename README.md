# Teachable Machine → Serial

Cross-platform (Windows / macOS / Linux) app that runs your webcam through a
[Teachable Machine](https://teachablemachine.withgoogle.com/) image model and
prints/sends the detected class (e.g. `Class 1`, `Class 2`, `Class 3`) to an
Arduino over Serial.

Files in this project:

| File                              | Purpose                                              |
|------------------------------------|-------------------------------------------------------|
| `teachable_machine_to_serial.py`   | Main Python app                                       |
| `requirements.txt`                 | Python packages to install                            |
| `arduino_code.ino`                 | Arduino sketch that receives the class over Serial    |
| `converted_keras.zip`              | Your exported Teachable Machine model (you provide this) |
| `.gitignore`                       | Keeps venv/model files out of git                     |

---

## 1. Prerequisites

You need **Python 3.10 or 3.11**. Newer versions (3.12/3.13) often don't have
TensorFlow wheels published yet, and you'll get an error like:

```
ERROR: Could not find a version that satisfies the requirement tensorflow
```

Check what you have:

```bash
python3 --version      # macOS / Linux
py --version            # Windows
```

If you don't have 3.10/3.11, install one before continuing:

- **Windows:** download from [python.org/downloads](https://www.python.org/downloads/) (pick 3.11.x). During install, **check "Add python.exe to PATH"**.
- **macOS:** `brew install python@3.11` (install [Homebrew](https://brew.sh) first if needed)
- **Linux (Debian/Ubuntu):** `sudo apt install python3.11 python3.11-venv`

You'll also need the **Arduino IDE** if you're flashing `arduino_code.ino` to a board — [arduino.cc/en/software](https://www.arduino.cc/en/software).

---

## 2. Export your model from Teachable Machine

1. In Teachable Machine, name your classes **before** training (renaming after export doesn't always take effect — you'd need to retrain in a new project).
2. Train your model.
3. Export → **Tensorflow** tab → **Keras** → Download my model.
4. This downloads a `.zip` file (like `converted_keras.zip`). Move/rename it so it's **exactly** `converted_keras.zip`, placed in the same folder as `teachable_machine_to_serial.py`.
   - The script now searches inside the zip recursively for the `.h5` model file and `labels.txt`, so it's fine if Teachable Machine names the `.h5` file something other than `keras_model.h5`, or nests it in a subfolder.

---

## 3. Set up the project (all OSes)

Open a terminal (macOS/Linux) or Command Prompt / PowerShell (Windows) in this project folder.

### Windows

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If `activate` is blocked with a "running scripts is disabled" error in PowerShell, run this once first: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

### macOS

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Apple Silicon (M1/M2/M3/M4) only:** if `tensorflow` fails to install or you see "Could not find a version that satisfies the requirement tensorflow", install the Apple-optimized build instead:
> ```bash
> pip uninstall -y tensorflow
> pip install tensorflow-macos tensorflow-metal
> ```

> The first time you run the script, macOS will prompt for camera access. Go to **System Settings → Privacy & Security → Camera** and make sure your terminal app (Terminal/iTerm) is allowed, or the webcam will silently fail to open.

### Linux

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If OpenCV can't open the webcam, check your user is in the `video` group (`sudo usermod -aG video $USER`, then log out/in), and that no other app (browser tab with Teachable Machine open, Zoom, etc.) is using the camera.

---

## 4. Run it

With the venv still active:

```bash
python teachable_machine_to_serial.py        # macOS / Linux
python teachable_machine_to_serial.py         # Windows (same command)
```

What happens:

1. It extracts `converted_keras.zip` (first run only) and finds the model + labels inside it.
2. Loads the model.
3. Asks if you want to send results to an Arduino over Serial — answer `y` and pick your port from the list, or `n` to just see console/webcam output.
4. Opens your webcam and starts printing the detected class + confidence every frame, e.g.:
   ```
   Detected: Class 1  (confidence: 96.42%)
   ```
5. A preview window shows the same info on-screen for debugging.
6. Press **`q`** in the preview window (or **Ctrl+C** in the terminal) to quit.

---

## 5. Arduino side

1. Open `arduino_code.ino` in the Arduino IDE.
2. Edit the `if (str == "Class 1") ...` blocks to match your actual class names and desired actions.
3. Plug in your board, select the right **Board** and **Port** in the Arduino IDE, and upload the sketch.
4. Close the Arduino IDE's Serial Monitor before running the Python script — **only one program can hold a Serial port open at a time.**
5. Run the Python script and pick that same port when prompted.

---

## Troubleshooting

**`Could not find a version that satisfies the requirement tensorflow`**
Your Python version is too new (or too old/wrong architecture on Apple Silicon). Use Python 3.10/3.11, and on Apple Silicon use `tensorflow-macos` + `tensorflow-metal` instead of plain `tensorflow` (see macOS section above).

**`ERROR: Could not find 'converted_keras.zip' next to this script`**
The zip must be named exactly `converted_keras.zip` and sit in the same folder as the `.py` file.

**`ERROR: Extracted the zip but couldn't find a *.h5 model file and/or labels.txt`**
Make sure you exported the **Keras** format from Teachable Machine (not TensorFlow.js or TFLite). Delete the `converted_keras/` folder and rerun so it re-extracts.

**`ValueError: Unrecognized keyword arguments passed to DepthwiseConv2D: {'groups': 1}`**
Already handled in the script — it patches this automatically. If you still see it, make sure you're running the latest version of `teachable_machine_to_serial.py`.

**Webcam won't open / black preview window**
Close every other app that might be using it (browser tab with Teachable Machine, Zoom, Photo Booth, etc.), and check OS camera permissions (see macOS/Linux notes above).

**No serial ports listed / can't connect to Arduino**
Make sure the Arduino is plugged in, drivers are installed (Windows sometimes needs the CH340/FTDI driver depending on the board), and the Arduino IDE's Serial Monitor is closed.

**Starting fresh**
If things get into a weird state, delete the venv and the extracted model folder, then redo Step 3:

```bash
# macOS/Linux
rm -rf venv converted_keras

# Windows (PowerShell)
Remove-Item -Recurse -Force venv, converted_keras
```
