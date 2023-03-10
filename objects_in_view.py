from mathutils import Vector
import bpy


def camera_as_planes(scene, obj):
    """
    Return planes in world-space which represent the camera view bounds.
    """
    from mathutils.geometry import normal

    camera = obj.data
    # normalize to ignore camera scale
    matrix = obj.matrix_world.normalized()
    frame = [matrix @ v for v in camera.view_frame(scene=scene)]
    origin = matrix.to_translation()

    planes = []
    from mathutils import Vector
    is_persp = (camera.type != 'ORTHO')
    for i in range(4):
        # find the 3rd point to define the planes direction
        if is_persp:
            frame_other = origin
        else:
            frame_other = frame[i] + matrix.col[2].xyz

        n = normal(frame_other, frame[i - 1], frame[i])
        d = -n.dot(frame_other)
        planes.append((n, d))

    if not is_persp:
        # add a 5th plane to ignore objects behind the view
        n = normal(frame[0], frame[1], frame[2])
        d = -n.dot(origin)
        planes.append((n, d))

    return planes


def side_of_plane(p, v):
    return p[0].dot(v) + p[1]


def is_segment_in_planes(p1, p2, planes):
    dp = p2 - p1

    p1_fac = 0.0
    p2_fac = 1.0

    for p in planes:
        div = dp.dot(p[0])
        if div != 0.0:
            t = -side_of_plane(p, p1)
            if div > 0.0:
                # clip p1 lower bounds
                if t >= div:
                    return False
                if t > 0.0:
                    fac = (t / div)
                    p1_fac = max(fac, p1_fac)
                    if p1_fac > p2_fac:
                        return False
            elif div < 0.0:
                # clip p2 upper bounds
                if t > 0.0:
                    return False
                if t > div:
                    fac = (t / div)
                    p2_fac = min(fac, p2_fac)
                    if p1_fac > p2_fac:
                        return False

    ## If we want the points
    # p1_clip = p1.lerp(p2, p1_fac)
    # p2_clip = p1.lerp(p2, p2_fac)
    return True


def point_in_object(obj, pt):
    xs = [v[0] for v in obj.bound_box]
    ys = [v[1] for v in obj.bound_box]
    zs = [v[2] for v in obj.bound_box]
    pt = obj.matrix_world.inverted() @ pt
    return (min(xs) <= pt.x <= max(xs) and
            min(ys) <= pt.y <= max(ys) and
            min(zs) <= pt.z <= max(zs))


def object_in_planes(obj, planes):
    from mathutils import Vector

    matrix = obj.matrix_world
    box = [matrix @ Vector(v) for v in obj.bound_box]
    for v in box:
        if all(side_of_plane(p, v) > 0.0 for p in planes):
            # one point was in all planes
            return True

    # possible one of our edges intersects
    edges = ((0, 1), (0, 3), (0, 4), (1, 2),
             (1, 5), (2, 3), (2, 6), (3, 7),
             (4, 5), (4, 7), (5, 6), (6, 7))
    if any(is_segment_in_planes(box[e[0]], box[e[1]], planes)
           for e in edges):
        return True

    return False


def objects_in_planes(objects, planes, origin):
    """
    Return all objects which are inside (even partially) all planes.
    """
    return [obj for obj in objects
            if point_in_object(obj, origin) or
            object_in_planes(obj, planes)]


def select_objects_in_camera():
    from bpy import context
    scene = context.scene
    origin = scene.camera.matrix_world.to_translation()
    planes = camera_as_planes(scene, scene.camera)
    objects_in_view = objects_in_planes(scene.objects, planes, origin)

    return set(objects_in_view)

