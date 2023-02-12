# Data sampling with bpy

To draw bboxes necessary install cv2 to blender python interpretator.

For windows run:

```
import subprocess
import sys
import os

# path to python.exe
python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
py_lib = os.path.join(sys.prefix, 'lib', 'site-packages','pip')

# install opencv
subprocess.call([python_exe, py_lib, "install", "opencv_python"])
# install mediapipe
subprocess.call([python_exe, py_lib, "install", "mediapipe"])
```

For Linux:

```sh
cd path_to_blender]/3.4/python/bin
./python3.10 -m ensurepip
./python3.10 -m pip install opencv-python
```
