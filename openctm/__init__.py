from .openctm import *
import scene
import glm


def read(group, file):
    print('Load', file)
    try:
        ctm = ctmNewContext(CTM_IMPORT)
        ctmLoad(ctm, bytes(str(file), 'utf-8'))
        err = ctmGetError(ctm)
        if err != CTM_NONE:
            raise IOError("Error loading file: " + str(ctmErrorString(err)))

        # Interpret information
        hasNormals = (ctmGetInteger(ctm, CTM_HAS_NORMALS) == CTM_TRUE)

        method = ctmGetInteger(ctm, CTM_COMPRESSION_METHOD)
        if method == CTM_METHOD_RAW:
            methodStr = "RAW"
        elif method == CTM_METHOD_MG1:
            methodStr = "MG1"
        elif method == CTM_METHOD_MG2:
            methodStr = "MG2"
        else:
            methodStr = "Unknown"

        triCount = ctmGetInteger(ctm, CTM_TRIANGLE_COUNT)
        vertCount = ctmGetInteger(ctm, CTM_VERTEX_COUNT)

        # Print information
        print("CTM_FILE_COMMENT:", str(ctmGetString(ctm, CTM_FILE_COMMENT)))
        print("        CTM_NAME:", str(ctmGetString(ctm, CTM_NAME)))
        print("  Triangle count:", triCount)
        print("    Vertex count:", vertCount)
        print("     Has normals:", hasNormals)
        print("          Method:", methodStr)

        # List UV maps
        uvMapCount = ctmGetInteger(ctm, CTM_UV_MAP_COUNT)
        print("       UV maps:", uvMapCount)
        for i in range(uvMapCount):
            print("                CTM_UV_MAP_" + str(i + 1) + ": \"" +
                  str(ctmGetUVMapString(ctm, CTM_UV_MAP_1 + i, CTM_NAME)) +
                  "\", ref = \"" +
                  str(ctmGetUVMapString(ctm, CTM_UV_MAP_1 +
                                        i, CTM_FILE_NAME)) + "\"")

        # List attrib maps
        attribMapCount = ctmGetInteger(ctm, CTM_ATTRIB_MAP_COUNT)
        print("Attribute maps:", attribMapCount)
        for i in range(attribMapCount):
            print(
                "                CTM_ATTRIB_MAP_" + str(i + 1) + ": \"" +
                str(ctmGetAttribMapString(ctm, CTM_ATTRIB_MAP_1 +
                                          i, CTM_NAME)) + "\"")

        pindices = ctmGetIntegerArray(ctm, CTM_INDICES)
        pvertices = ctmGetFloatArray(ctm, CTM_VERTICES)

        # Get normals
        pnormals = None
        if hasNormals:
            pnormals = ctmGetFloatArray(ctm, CTM_NORMALS)

        # Get texture coordinates
        ptexCoords = None
        if uvMapCount > 0:
            ptexCoords = ctmGetFloatArray(ctm, CTM_UV_MAP_1)

        puvCoords = None
        if uvMapCount > 1:
            puvCoords = ctmGetFloatArray(ctm, CTM_UV_MAP_2)

        mesh = scene.Mesh('ctm')
        mesh.parent = group

        def readVec3(array, idx):
            return glm.vec3(array[idx * 3], array[idx * 3 + 1],
                            array[idx * 3 + 2])

        def readVec2(array, idx):
            return glm.vec2(array[idx * 2], array[idx * 2 + 1])

        for i in range(triCount):
            i0, i1, i2 = pindices[i * 3], pindices[i * 3 + 1], pindices[i * 3 +
                                                                        2]
            v0, v1, v2 = readVec3(pvertices,
                                  i0), readVec3(pvertices,
                                                i1), readVec3(pvertices, i2)
            tri = scene.Triangle(v0, v1, v2)

            if hasNormals:
                n0, n1, n2 = readVec3(pnormals, i0), readVec3(pnormals,
                                                              i1), readVec3(
                                                                  pnormals, i2)
                tri.normals = (n0, n1, n2)

            if ptexCoords:
                t0, t1, t2 = readVec2(ptexCoords, i0), readVec2(
                    ptexCoords, i1), readVec2(ptexCoords, i2)
                tri.texcoords = (t0, t1, t2)

            if puvCoords:
                uv0, uv1, uv2 = readVec2(puvCoords, i0), readVec2(
                    puvCoords, i1), readVec2(puvCoords, i2)
                tri.globalUVs = (uv0, uv1, uv2)

            mesh.add(tri)

        group.add(mesh)

    except Exception as e:
        print('Exception occurred:', e)

    finally:
        # Free the OpenCTM context
        ctmFreeContext(ctm)
