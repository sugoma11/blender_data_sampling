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
import cv2
from mathutils import Color
from pathlib import Path

# insert your's pathes
if os.name == 'posix':
    base_dir = '/home/alex/python_projects/blender_data_sampling'
elif os.name == 'nt':
    base_dir = 'e:\\blender_data_sampling'

os.chdir(base_dir)
if not os.path.isdir('misty'):
    os.mkdir('misty')

if len(list(Path('./misty').glob('*.jpg'))) == 0:
    num = 0

else:
    last_im = (sorted(Path('./misty').glob('*.jpg'), key=os.path.getmtime)[-1]).name
    num = int(last_im.split('.')[0].split('_')[-1]) + 1

DRAW_BBOXES = True
RENDERING = True

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
NUM_IMAGES = 100
NUM_SAMPLES = 100

LEFT_ANGLE = 0
RIGHT_ANGLE = 360

sys.path.append(base_dir)
from setup_camera import rotate_camera
from bboxes import camera_view_bounds_2d
from get_edges import xxyyzz_edges
from objects_in_view import select_objects_in_camera
from make_grid import make_grid


def l2(obj):
    return round(np.sqrt((obj.location.x - bpy.data.objects['Camera'].location.x) ** 2 + (obj.location.y - bpy.data.objects['Camera'].location.y) ** 2 + (obj.location.z - bpy.data.objects['Camera'].location.z) ** 2), ndigits=0)


targret_objects = list(bpy.data.collections['markers'].objects)
geometry_file_path = os.path.join(base_dir, "geometry2.txt")

with open(geometry_file_path, "w") as file:
    # finding the biggest dimension to correctly relocate objects
    mx_dim = 0
    for object in targret_objects:

        if object.dimensions.x > mx_dim:
            mx_dim = object.dimensions.x

        if object.dimensions.y > mx_dim:
            mx_dim = object.dimensions.y

    low_x, low_y, low_z, high_x, high_y, high_z = xxyyzz_edges(bpy.data.objects['стена'])

    # object for hsv -> rgb transformation
    c = Color()

    for i in range(num, num + NUM_IMAGES):
        h = uniform(0.5, 0.6)
        s = uniform(0.6, 0.9)
        v = uniform(0.5, 0.7)

        # change walls' color
        c.hsv = h, s, v
        bpy.data.objects['стена'].color = c.r, c.g, c.b, 1.0

        # change color of baths' floor
        bpy.data.objects['стена'].active_material.node_tree.nodes["Hue Saturation Value"].inputs[
            0].default_value = uniform(0.45, 0.53)
        bpy.data.objects['стена'].active_material.node_tree.nodes["Hue Saturation Value"].inputs[
            1].default_value = uniform(1.1, 2)
        bpy.data.objects['стена'].active_material.node_tree.nodes["Hue Saturation Value"].inputs[
            2].default_value = uniform(0.9, 2)

        # mist density
        density = uniform(0, .45)
        bpy.data.materials["Material.001"].node_tree.nodes["Principled Volume"].inputs[2].default_value = density

        grid = make_grid(len(targret_objects), low_x, low_y, high_x, high_y, math.ceil(mx_dim))

        # rotating and changing colors
        for j, object in enumerate(targret_objects):

            # x and y are swapped in blender
            object.location.x = low_x + grid[j][1]
            object.location.y = low_y + grid[j][0]
            object.rotation_euler[2] = randint(0, 360) / 180 * math.pi

        x_coords = list(range(low_x, high_x))
        y_coords = list(range(low_y, high_y))

        # rotating camera until we get > 2 objects in view
        while 1:

            # relocate camera
            bpy.data.objects['Camera'].location.x = choice(x_coords)
            bpy.data.objects['Camera'].location.y = choice(y_coords)
            bpy.data.objects['Camera'].location.z = uniform(low_z, high_z)

            rotate_camera(uniform(LEFT_ANGLE, RIGHT_ANGLE))

            # there are a lot of objects thats we don't need in ROI, i.e pools walls, water, Sun etc
            objects_in_camera = set(targret_objects).intersection(select_objects_in_camera())
            valid_objects = []

            # check how much objects in camera
            if len(objects_in_camera) < 3:
                continue

            # checking invalid bboxes
            for obj in objects_in_camera:

                # get bbox of object
                b = camera_view_bounds_2d(bpy.context.scene, bpy.context.scene.camera, bpy.data.objects[obj.name])
                b.distance = l2(obj)
                # check size of bbox; in far figures may looks like a string
                if b.width < 30 or b.height < 5:
                    continue

                # check distance between camera and object
                elif np.sqrt((obj.location.x - bpy.data.objects['Camera'].location.x) ** 2 + (
                        obj.location.y - bpy.data.objects['Camera'].location.y) ** 2 + (
                                     obj.location.z - bpy.data.objects['Camera'].location.z) ** 2) < 1.5:
                    continue

                else:
                    valid_objects.append(b)

                    # saving and rendering
            if len(valid_objects) >= 2:
                ans = []
                f = "image_" + str(i) + ".jpg"
                for obj in valid_objects:
                    ans.append([str(density), str(obj.distance)])
                    print(f'ans list {ans}')
                break

        if RENDERING:
            path = os.path.join(base_dir, 'misty', f)
            bpy.context.scene.render.filepath = path
            bpy.context.scene.render.resolution_x = IMAGE_WIDTH
            bpy.context.scene.render.resolution_y = IMAGE_HEIGHT
            bpy.context.scene.cycles.samples = NUM_SAMPLES
            bpy.context.scene.render.image_settings.file_format = 'JPEG'
            bpy.ops.render.render(write_still=True)

            if DRAW_BBOXES:
                im = cv2.imread(path)
                for box in valid_objects:
                    cv2.rectangle(im, (box.x, box.y), (box.x + box.width, box.y + box.height), (255, 0, 0), 1)
                    cv2.putText(im, box.name, (box.x, box.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 1)
                    cv2.putText(im, str(box.distance), (box.x, box.y - 45),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 1)
                    cv2.putText(im, f'density {density}', (15, 15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 1)

                os.remove(path)
                path = os.path.join(base_dir, 'misty', f'image_{i}.jpg')
                cv2.imwrite(path, im)

        cv2.imwrite(path, im)

        file.write(f)
        file.write('\n')

        for st in ans:
            file.write(' '.join(st))
            file.write('\n')

    file.close()
