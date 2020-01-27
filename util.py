import hashlib
import glm
import scene

from pathlib import Path

default_out_dir = Path.cwd() / 'out'
if not default_out_dir.exists():
    default_out_dir.mkdir(parents=True)


# https://en.wikipedia.org/wiki/ANSI_escape_code#3/4_bit
def colorprint(text: str, color: int) -> None:
    print("\x1B[1;" + str(color) + "m" + text + "\x1B[m")


def prepareOutFilename(inFileName: str, resolution: int) -> str:
    utf8bytes: bytes = (inFileName + str(resolution)).encode("utf8")
    hash_object = hashlib.md5(utf8bytes)
    result: str = "AO_" + hash_object.hexdigest()
    return result


def joinOutputPath(filename: str, extension: str) -> str:
    return default_out_dir / (filename + '.' + extension)


def make_quad(v0, span0, span1):
    v1 = v0 + span0
    v2 = v0 + span0 + span1
    v3 = v0 + span1
    t0 = scene.Triangle(v0, v1, v2)
    t0.globalUVs = [glm.vec2(0.0, 0.0), glm.vec2(1.0, 0.0), glm.vec2(1.0, 1.0)]
    t1 = scene.Triangle(v2, v3, v0)
    t1.globalUVs = [glm.vec2(1.0, 1.0), glm.vec2(0.0, 1.0), glm.vec2(0.0, 0.0)]
    mesh = scene.Mesh('quad')
    mesh.add(t0)
    mesh.add(t1)
    return mesh


def test_scene():
    floor = scene.Group('.floor')
    floor.add(
        make_quad(glm.vec3(-4, 0, 0.8), glm.vec3(8, 0, 0), glm.vec3(0, 6, 0)))
    box = scene.Group('.box')
    s = 2.0
    box.add(
        make_quad(glm.vec3(1.0, 2.0, 1.0), glm.vec3(s, 0, 0),
                  glm.vec3(0, 0, s)))
    box.add(
        make_quad(glm.vec3(1.0, 2.0, 1.0), glm.vec3(0, 0, s),
                  glm.vec3(0, s, 0)))
    box.add(
        make_quad(glm.vec3(1.0, 2.0, 1.0), glm.vec3(0, s, 0),
                  glm.vec3(s, 0, 0)))
    box.add(
        make_quad(glm.vec3(1.0, 2.0, 1.0 + s), glm.vec3(s, 0, 0),
                  glm.vec3(0, s, 0)))
    box.add(
        make_quad(glm.vec3(1.0 + s, 2.0, 1.0), glm.vec3(0, s, 0),
                  glm.vec3(0, 0, s)))
    box.add(
        make_quad(glm.vec3(1.0, 2.0 + s, 1.0), glm.vec3(0, 0, s),
                  glm.vec3(s, 0, 0)))
    root = scene.Group('.')
    root.add(floor)
    root.add(box)
    return root