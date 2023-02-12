import os
# clear blender console
os.system('cls')
import sys
import time
import math
from random import random, randint, choice, choices, uniform
import bpy
import numpy as np
from json import dumps
from mathutils import Color

# insert your's pathes
if os.name == 'posix':
    base_dir = '/home/alex/python_projects/blender_datasampling'
elif os.name == 'nt':
    base_dir = 'e:\\blender_data_sampling'

DRAW_BBOXES = True
RENDERING = True
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480

sys.path.append(base_dir)
from setup_camera import rotate_camera
from bboxes import camera_view_bounds_2d
from get_edges import xxyyzz_edges
from objects_in_view import select_objects_in_camera
from make_grid import make_grid

objects = list(bpy.data.collections['markers'].objects)
