import json
import glm
from remote import fetch, CachedFile
import scene
import wavefront
import openctm
from pathlib import Path


def readTransform(tTransform):
    tDx = tDy = tDz = 0
    tRx = tRy = tRz = 0
    tSx = tSy = tSz = 1

    tf = glm.mat4(1)

    if tTransform is None:
        return tf

    if "Position" in tTransform:
        tPosition = tTransform["Position"]

        if tPosition is not None:
            tDx, tDy, tDz = tPosition.get("X", 0), tPosition.get(
                "Y", 0), tPosition.get("Z", 0)
            tf = glm.translate(tf, glm.vec3(tDx, tDy, tDz))

    if "Rotation" in tTransform:
        tRotation = tTransform["Rotation"]
        if tRotation is not None:
            if "W" in tRotation and tRotation["W"] <= 1.000001:
                tRx = tRotation["X"]
                tRy = tRotation["Y"]
                tRz = tRotation["Z"]
                tW = tRotation["W"]
                R = glm.mat4_cast(glm.quat(tRx, tRy, tRz, tW))
            else:
                # only one rotation axis allowed
                tRx = glm.radians(tRotation["X"])
                tRy = glm.radians(tRotation["Y"])
                tRz = glm.radians(tRotation["Z"])
                Rx = glm.rotate(glm.mat4(1), tRx, glm.vec3(1, 0, 0))
                Ry = glm.rotate(glm.mat4(1), tRy, glm.vec3(0, 1, 0))
                Rz = glm.rotate(glm.mat4(1), tRz, glm.vec3(0, 0, 1))
                R = Rz * Ry * Rx

            tf = tf * R

    if "Scale" in tTransform:
        tScaling = tTransform["Scale"]
        if tScaling is not None:
            tSx, tSy, tSz = tScaling.get("X", 0), tScaling.get(
                "Y", 0), tScaling.get("Z", 0)
            tf = glm.scale(tf, glm.vec3(tSx, tSy, tSz))

    # print("LOG", "Position:", tDx, tDy, tDz, "Rotation:", tRx, tRy, tRz, "Scaling:", tSx, tSy, tSz)
    return tf


def loadGeometry(geometry, file, parent: scene.SceneNode):
    if file is None:
        return None

    group = scene.Group(geometry)

    group.parent = parent
    if file.suffix == '.obj':
        pass  # wavefront.read(group, file.open())

    if file.suffix == '.ctm':
        openctm.read(group, file.resolve())

    return group


def load(igxc, basepath):
    if "Objects" not in igxc:
        raise AttributeError("'Objects' not in igxc")
    if "Geometries" not in igxc:
        raise AttributeError("'Geometries' not in igxc")

    # fetch all referenced geometry
    tFileImport = dict()

    if 'BasePath' in igxc:
        basepath = CachedFile(igxc['BasePath'])

    try:
        for k, v in igxc['Geometries'].items():
            filename = basepath / v
            if filename.is_file():
                tFileImport[k] = filename
            else:
                tFileImport[k] = fetch(filename, v[-4:])
            # print(tFileImport[k])
    except FileNotFoundError as e:
        print(e)
        raise
    except ConnectionError as e:
        print(e)
        raise
    except Exception as e:
        print(e)
        print(type(e))
        raise

    print(len(tFileImport), 'files referenced in total')

    # traverse scene graph
    objects = dict()
    meshes = dict()
    root = None

    for tObject in igxc['Objects']:
        tComponentPath = tObject.get('Path')

        comp = scene.Group(tComponentPath)
        objects[tComponentPath] = comp

        if (tComponentPath == '.'):
            root = comp
            tParentPath = ''
        elif ("." in tComponentPath):
            tParentPath = tComponentPath[0:tComponentPath.rfind('.')]
            comp.parent = objects.get(tParentPath, root)
            comp.parent.add(comp)
        else:
            tParentPath = '.'
            root.add(comp)

        # print("LOG", "Processing Component", tComponentPath, "Parent:", tParentPath)

        comp.transform = readTransform(tObject.get('Transform', None))

        tGeometry = tObject.get('Geometry')
        # print("LOG", "Geometry:", tGeometry)
        if tGeometry is not None:
            # if tGeometry in meshes:
            #     geo = meshes.get(tGeometry)
            # else:
            geometryFile = tFileImport.get(tGeometry)
            # print("LOG", "geometryFile:", geometryFile)
            geo = loadGeometry(tGeometry, geometryFile, comp)
            meshes[tGeometry] = geo
            # print("LOG", "geo:", geo)

            if geo is not None:
                comp.add(geo)
            else:
                print("LOG", "Geometry:", tGeometry, "not found")

    print(len(meshes), 'meshes used in total')
    return root
