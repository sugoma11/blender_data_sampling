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
    base_dir = 'e:\\python_projects\\renderering_result'

sys.path.append(base_dir)
from setup_camera import rotate_camera
from bboxes import camera_view_bounds_2d
from get_edges import xxyyzz_edges
from objects_in_view import select_objects_in_camera
from make_grid import make_grid

colors_list = {(0, 0.8, 0.8, 1): 'cian', (0.8, 0, 0.8, 1): 'purple', (0.8, 0.8, 0, 1): 'yellow', (0.1, 0, 0.8, 1): 'blue',
               (0, 0.8, 0, 1): 'green'}

shapes = {'round': 'circle', 'round2': 'circle', 'sqr': 'square', 'triu': 'triangle',
        'circle1': 'hoop', 'circle2': 'hoop', 'gate': 'gate', 'TARGET': 'Target circle'}

# angles of camera rotation
LEFT_ANGLE = 0
RIGHT_ANGLE = 360

DRAW_BBOXES = True
RENDERING = True
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
# necassary minimum 512
NUM_SAMPLES = 12

if DRAW_BBOXES:
    # it's necessary to run another script to install cv2 to blender interpretator 
    import cv2
    

geometry_file_path = os.path.join(base_dir, "geometry.json")
with open(geometry_file_path, "w") as file:
    
    objects_to_move = set(list(bpy.data.collections['move_and_change_color'].objects) + (list(bpy.data.collections['only_move'].objects)))
    # get low and high xxyy coordinates of bath
    low_x, low_y, low_z, high_x, high_y, high_z = xxyyzz_edges(bpy.data.objects['стена'])
    # save initial power of light
    medium_light = 100000
    
    # finding biggest dimension to correctly relocate objects
    mx_dim = 0
    for object in objects_to_move:
        
        if object.dimensions.x > mx_dim:
            mx_dim = object.dimensions.x
            
        if object.dimensions.y > mx_dim:
             mx_dim = object.dimensions.y 
    # object to hsv -> rgb transformation
    c = Color()
    
    for i in range(10, 40):
    
        h = uniform(0.5, 0.6)
        s = uniform(0.6, 0.9)
        v = uniform(0.5, 0.7)
    
        # change walls' color
        c.hsv = h, s, v
        bpy.data.objects['стена'].color = c.r, c.g, c.b, 1.0 
        
        for light in list(bpy.data.collections['lights'].objects):
            # relocate and change power of light
            light.location.x = uniform(low_x, high_x)
            light.location.y = uniform(low_y, high_y)
            light.data.energy = uniform(medium_light - 0.75 * medium_light, medium_light + 0.75 * medium_light)
            light.rotation_euler[2] = randint(0, 360) / 180 * math.pi
            
        
        # get grid for objects
        grid = make_grid(len(objects_to_move), low_x, low_y, high_x, high_y, math.ceil(mx_dim))
        
        # rotating and changing colors
        for j, object in enumerate(objects_to_move):
            
            # x and y are swapped in blender
            object.location.x = low_x + grid[j][1]
            object.location.y = low_y + grid[j][0]
            
            if object in list(bpy.data.collections['move_and_change_color'].objects):
                color = choice(list(colors_list.keys()))
                # rotate only in Oxy
                object.rotation_euler[2] = randint(0, 360) / 180 * math.pi
                object.active_material.node_tree.nodes['Principled BSDF'].inputs["Base Color"].default_value = color
            else:
                object.rotation_euler[2] = randint(0, 360) / 180 * math.pi
                 
        # randomize coordinates for camera    
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
            objects_in_camera = objects_to_move.intersection(select_objects_in_camera())
            valid_objects = []
            
            if len(objects_in_camera) < 3:
                continue
            
            for object in objects_in_camera:
                # get bbox of object
                b = camera_view_bounds_2d(bpy.context.scene, bpy.context.scene.camera, bpy.data.objects[object.name])
            
                # check size of bbox; in far figures may looks like a string
                if b.width < 30 or b.height < 10:
                    continue
                
                # check distance between camera and object
                elif np.sqrt((object.location.x - bpy.data.objects['Camera'].location.x) ** 2 + (object.location.y - bpy.data.objects['Camera'].location.y) ** 2 + (object.location.z - bpy.data.objects['Camera'].location.z) ** 2) < 1.5:
                    continue
                
                else:
                    valid_objects.append(b)     

            
            
            if len(valid_objects) >= 2:
                
                f = "image" + str(i) + ".jpg"
                
                outer_dct = {'file_name': f}

                for l, box in enumerate(valid_objects):
                    object_name = shapes[box.name] + '_' + str(l)
                    temp_dct = {}
                    temp_dct['shape'] = shapes[box.name]
                    if box.color == (0.0, 0.0, 0.0, 1.0):
                        temp_dct['color'] = 'black'
                    elif box.color == (0.8, 0, 0, 1):
                        temp_dct['color'] = 'red'
                    else:
                        temp_dct['color'] = colors_list[box.color]
                    temp_dct["bbox"] = (box.x, box.y, box.width, box.height)
                    outer_dct[object_name] = temp_dct
                    print(outer_dct)

                file.write(dumps(outer_dct, indent=4))
                
                #print()              
                
                #print(f'valid_objects {valid_objects}')
            
                #print('____________________________')
            
                #print(f'in camera {objects_in_camera}')
                
                #print()
                
                #bpy.ops.object.select_all(action='SELECT')
                
                break
            
        if RENDERING:        
            path = os.path.join(base_dir, f)
            bpy.context.scene.render.filepath = path
            bpy.context.scene.render.resolution_x = IMAGE_WIDTH
            bpy.context.scene.render.resolution_y = IMAGE_HEIGHT
            bpy.context.scene.render.image_settings.file_format='JPEG'
            bpy.ops.render.render(write_still = True)
            bpy.context.scene.cycles.samples = NUM_SAMPLES
            if DRAW_BBOXES:
                im = cv2.imread(path)
                for box in valid_objects:
                    cv2.rectangle(im, (box.x, box.y), (box.x + box.width, box.y + box.height), (255, 0, 0), 4)
                    cv2.putText(im, box.name, (box.x, box.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                os.remove(path)
                path = os.path.join(base_dir, f'img_bbox_{i}.jpg')
                cv2.imwrite(path, im)
                        
        # print(objects_to_move.intersection(objects_in_camera))
                