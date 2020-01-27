import glm


class SceneNode(object):
    def __init__(self, name: str):
        self.name = name
        self.parent: SceneNode = None

    def accept(self, visitor):
        visitor.visit_SceneNode(self, 'forward')
        visitor.visit_SceneNode(self, 'backward')


class Group(SceneNode):
    def __init__(self, name):
        SceneNode.__init__(self, name)
        self.transform = glm.mat4(1)
        self.children = []

    def add(self, node):
        self.children.append(node)

    def accept(self, visitor):
        visitor.visit_Group(self, 'forward')
        for child in self.children:
            child.accept(visitor)
        visitor.visit_Group(self, 'backward')

    def __repr__(self):
        out = []
        for child in self.children:
            lines = repr(child).splitlines()
            out.append(" - %s" % lines[0])
            out += [" " * 3 + line for line in lines[1:]]
        # if self.transform != glm.mat4(1):
        # tf = str(self.transform) + '\n'
        # else:
        tf = ''
        result = ("Group (%s)\n" % (self.name)) + tf + '\n'.join(out)
        if self.parent is not None:
            result = ("Group (%s, parent %s)\n" %
                      (self.name, self.parent.name)) + tf + '\n'.join(out)
        return result


class Mesh(SceneNode):
    def __init__(self, name):
        SceneNode.__init__(self, name)
        self.triangles = []

    def add(self, prim):
        self.triangles.append(prim)

    def accept(self, visitor):
        # self.name = self.parent.parent.name
        visitor.visit_Mesh(self, 'forward')
        visitor.visit_Mesh(self, 'backward')

    def __repr__(self):
        result = "Mesh (%s) with %d triangles" % (self.name, len(
            self.triangles))
        if self.parent is not None:
            result = "Mesh (%s, parent %s, grandparent %s) with %d triangles" % (
                self.name, self.parent.name, self.parent.parent.name,
                len(self.triangles))
        return result


class Triangle(object):
    def __init__(self, v1, v2, v3):
        self.vertices = [v1, v2, v3]
        self.texcoords = None
        self.normals = None
        self.globalUVs = None

    def vertex(self, i, v, t, n, uv=None):
        self.vertices[i] = v

        if (self.texcoords is None):
            self.texcoords = []
        self.texcoords[i] = t if t is not None else glm.vec2(0.0)

        if (self.normals is None):
            self.normals = []
        self.normals[i] = n if n is not None else glm.vec3(0.0)

        if (self.globalUVs is None):
            self.globalUVs = []
        self.globalUVs[i] = uv if uv is not None else glm.vec2(0.0)
