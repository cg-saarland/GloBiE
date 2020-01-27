import glm

import scene


class SceneVisitor:
    def visit_SceneNode(self, node: scene.SceneNode, direction: str):
        pass

    def visit_Group(self, group: scene.Group, direction: str):
        pass

    def visit_Mesh(self, mesh: scene.Mesh, direction: str):
        pass


class MeshCounter(SceneVisitor):
    def __init__(self, start=0):
        self.count = start
        self.disable = False

    def visit_Mesh(self, mesh: scene.Mesh, direction: str):
        if direction != 'forward' or self.disable:
            return
        self.count += 1
        # self.disable = True


class TriCounter(SceneVisitor):
    def __init__(self, start=0):
        self.count = start
        self.disable = False

    def visit_Mesh(self, mesh: scene.Mesh, direction: str):
        if direction != 'forward' or self.disable:
            return
        self.count += len(mesh.triangles)
        # self.disable = True


class SimplePacker(object):
    def __init__(self, m: int, n: int, pixelSize: int):
        self.i = 0
        self.m = m
        self.n = n
        tileSize = pixelSize / max([m, n])
        self.paddedScaling = (tileSize - 1) / tileSize

    def bucket(self):
        y = self.i // self.m
        x = self.i % self.m
        if self.i > self.m * self.n - 1:
            return None
        self.i += 1
        M = glm.mat3(self.paddedScaling / self.m, 0, 0, 0,
                     self.paddedScaling / self.n, 0, 0, 0, 1)
        M[2][0] = float(x) / self.m
        M[2][1] = float(y) / self.n

        # debug verbose
        # out = []
        # for child in M:
            # lines = repr(child).splitlines()
            # out.append(" - %s" % lines[0])
            # out += [" " * 3 + line for line in lines[1:]]
        # print("   SimplePacker.bucket x: %d y: %d\n%s" %
        #       (x, y, "\n".join(out)))

        return M


class TransformedTriExtractor(SceneVisitor):
    def __init__(self,
                 vertices,
                 normals,
                 texcoord,
                 startIdx=0,
                 globalTf=glm.mat4(1),
                 packer=SimplePacker(4, 4, 1024)):
        self.vertices = vertices
        self.normals = normals
        self.texcoord = texcoord
        self.tfStack = []
        self.tf = globalTf
        self.idx = startIdx
        self.disable = False
        self.packer = packer
        self.mapping = {}

    def visit_Group(self, group: scene.Group, direction: str):
        if self.disable:
            return

        if direction == 'forward':
            self.tfStack.append(self.tf)
            self.tf = self.tf * group.transform
        else:
            self.tf = self.tfStack.pop()

    def visit_Mesh(self, mesh: scene.Mesh, direction: str):
        if self.disable:
            return
        if direction != 'forward':
            return

        # print("visitting mesh {} with geometry {}".format(
        #     mesh.parent.parent.name, mesh.parent.name))
        hasGlobalUVs = False
        for tri in mesh.triangles:
            if tri.globalUVs is not None:
                hasGlobalUVs = True

        # print("   {}".format(hasGlobalUVs))

        # if hasGlobalUVs:
        uvTf = self.packer.bucket()
        if uvTf is not None:
            allEntries = [x for col in uvTf for x in col]
            # print("   allEntries")
            # print("   {}".format(allEntries))
            self.mapping[mesh.parent.parent.name] = allEntries

        # print("   {}".format(mesh.triangles[0].globalUVs))
        for tri in mesh.triangles:

            for k in range(3):
                vi = glm.vec4(tri.vertices[k], 1.0)
                vo = self.tf * vi
                for i in range(3):
                    self.vertices[self.idx, k, i] = vo[i] / vo[3]
                if tri.normals is not None:
                    ni = glm.vec4(tri.normals[k], 0.0)
                    no = self.tf * ni
                    l = glm.length(no)
                    if l > 0:
                        for i in range(3):
                            self.normals[self.idx, k, i] = no[i] / l
                if tri.globalUVs is None or uvTf is None:
                    self.texcoord[self.idx, k, :] = [1.0, 1.0]
                else:
                    ti = glm.vec3(tri.globalUVs[k], 1.0)
                    to = uvTf * ti
                    for i in range(2):
                        self.texcoord[self.idx, k, i] = to[i] / to[2]

            self.idx += 1
        # self.disable = True
