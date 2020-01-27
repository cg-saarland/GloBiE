import glm
import scene


def readVec2(data):
    v = [float(val) for val in data[0:2]]
    return glm.vec2(*v)


def readVec3(data):
    v = [float(val) for val in data[0:3]]
    return glm.vec3(*v)


class Parser(object):
    def __init__(self, group):
        self.vertices = [glm.vec3(0.0)]
        self.normals = [glm.vec3(0.0)]
        self.texcoords = [glm.vec2(0.0)]
        self.mesh = None
        self.group = group

    def read_file(self, file):
        for line in file:
            self.parse(line)

    def parse(self, line):
        if line.startswith('#'):
            return

        values = line.split()
        if len(values) < 2:
            return

        attrib = 'parse_%s' % values[0]
        args = values[1:]

        if hasattr(self, attrib):
            parse_function = getattr(self, attrib)
            parse_function(args)
        # else:
        # print("unable to read line:", line)

    def parse_v(self, args):
        self.vertices.append(readVec3(args))

    def parse_vn(self, args):
        self.normals.append(readVec3(args))

    def parse_vt(self, args):
        self.texcoords.append(readVec2(args))

    def parse_o(self, args):
        self.mesh = scene.Mesh(args[0])
        self.group.add(self.mesh)

    def parse_f(self, args):
        if self.mesh is None:
            self.parse_o(['unnamed mesh'])

        prim0 = scene.Triangle(*[glm.vec3(0.0), glm.vec3(0.0), glm.vec3(0.0)])
        self.mesh.add(prim0)

        for i, v in enumerate(args):
            vidx, tidx, nidx = (list(map(int, [j or 0
                                               for j in v.split('/')])) +
                                [0, 0])[:3]

            # wrap index around
            if vidx < 0:
                vidx = len(self.vertices) - vidx
            if tidx < 0:
                tidx = len(self.texcoords) - tidx
            if nidx < 0:
                nidx = len(self.normals) - nidx

            if i < 3:
                prim0.vertex(i, self.vertices[vidx], self.texcoords[tidx],
                             self.normals[nidx])
            elif i == 3:
                # second triangle for quad face
                prim1 = scene.Triangle(prim0.vertices[0], prim0.vertices[2],
                                       self.vertices[vidx])
                prim1.texcoords = [
                    prim0.texcoords[0], prim0.texcoords[2],
                    self.texcoords[tidx]
                ]
                prim1.normals = [
                    prim0.normals[0], prim0.normals[2], self.normals[nidx]
                ]
                self.mesh.add(prim1)


def read(group, file):
    parser = Parser(group)
    parser.read_file(file)
