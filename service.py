import json
import numpy
import math
import os
import argparse
import sys
import random

# add dependencies for auto-py-to-exe
# https://github.com/pyinstaller/pyinstaller/issues/4363#issuecomment-522350024
# import numpy.random.common
# import numpy.random.bounded_integers
# import numpy.random.entropy

from PIL import Image
from remote import fetch
from pathlib import Path
from urlpath import URL
from util import colorprint, prepareOutFilename, test_scene, joinOutputPath
from remote import CachedFile

import igxc
import scene
import visitor

default_url = 'default/igcx/test-url'
default_file = 'default/igcx/test-file'
default_out = "test"

aoConfig = {"resolution": 1024}


def generateMap(vertices,
                normals,
                texcoord,
                size=(aoConfig["resolution"], aoConfig["resolution"])):
    import ig_rendering_support

    w, h = size
    buff = numpy.zeros((w, h, 4), dtype=numpy.uint8)

    ig_rendering_support.bakeAO(buff, vertices, normals, texcoord)

    blurred = ig_rendering_support.alphaBlur(buff, w, h)

    return Image.frombuffer('RGBA', (w, h), blurred, 'raw', 'RGBA', 0, 1)


def start():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url',
                       help='url to igxc resource',
                       nargs='?',
                       type=str,
                       const=default_url)
    group.add_argument('--file',
                       help='path to igxc resource',
                       nargs='?',
                       type=str,
                       const=default_file)
    group.add_argument('--test',
                       help='use default test scene',
                       action='store_true')
    parser.add_argument('--out',
                        '-o',
                        help='basename of the generated output',
                        type=str,
                        default=default_out)
    parser.add_argument('--debug',
                        help='show debug viewer',
                        action='store_true')
    parser.add_argument('--face-normals',
                        help='use computed face normals',
                        action='store_true')
    args = parser.parse_args()
    dictArgs = vars(args)
    # print(args)

    startWithDirectArgs(dictArgs)


def modifyIgxc(igxcJson, outFileName, mapping):
    igxcJson["ObjectAmbientOcclusionMaps"] = {'.': outFileName}

    for tObject in igxcJson['Objects']:
        nodeName = tObject["Path"]
        if nodeName in mapping:
            tObject["AOTransform"] = mapping[nodeName]


def startWithDirectArgs(args: dict):
    root = None
    igxcFile = None
    igxcContent = None
    urlArgument = None
    basePath = None
    result = None
    outFileHashBase = ""
    outFileNameBase = "AO_result"

    resolutionValue = aoConfig["resolution"]
    if "resolution" in args and args["resolution"] is not None:
        resolutionValue = int(args["resolution"])

    if "url" in args and args["url"] is not None:
        print('fetch url', args["url"])
        urlArgument = URL(args["url"])
        igxcFile = fetch(urlArgument, '.igcx')
        colorprint("source: " + str(urlArgument) + '.igcx', 36)
    elif "file" in args and args["file"] is not None:
        igxcFile = Path(args["file"])
        colorprint("source: " + args["file"], 36)
    elif "igxcContent" in args and args["igxcContent"] is not None:
        igxcContent = args["igxcContent"]
        colorprint("source: bakeDirect POST parameters", 36)

    elif "test" in args and args["test"]:
        outFileNameBase = prepareOutFilename(str(random.randint(1, 1e9)),
                                             resolutionValue)
        root = test_scene()
        colorprint("source: test scene", 36)

    if igxcFile is not None:
        basePath = igxcFile.parent

    if "basePath" in args and args["basePath"] is not None:
        # print(args["basePath"])
        basePath = CachedFile(args["basePath"])
    print("basePath:", basePath)

    debug = "debug" in args and args["debug"]

    if igxcFile is not None:

        with igxcFile.open('r') as resource:
            igxcContent = json.load(resource)

        # if igxcContent is None:
        #     return None

    if igxcContent is None:
        print("No content in igxc")

    # check if configuration is already done
    if "Objects" in igxcContent and igxcContent["Objects"] is not None:
        outFileHashBase = outFileHashBase + json.dumps(igxcContent["Objects"],
                                                       sort_keys=True)
    if "Hashes" in igxcContent and igxcContent["Hashes"] is not None:
        outFileHashBase = outFileHashBase + json.dumps(igxcContent["Hashes"],
                                                       sort_keys=True)
    if outFileHashBase == "" and urlArgument is not None:
        outFileHashBase = urlArgument

    outFileNameBase = prepareOutFilename(outFileHashBase, resolutionValue)

    hasImage = os.path.isfile(joinOutputPath(outFileNameBase, 'png'))
    hasMapping = os.path.isfile(joinOutputPath(outFileNameBase, 'json'))
    if hasImage and hasMapping and not debug:
        colorprint("Taking from cache ({})".format(outFileNameBase), 32)
        mappingResult = None
        with open(joinOutputPath(outFileNameBase, 'json'),
                  'r') as mappingInFile:
            mappingResult = json.load(mappingInFile)
        modifyIgxc(igxcContent, outFileNameBase + '.png', mappingResult)
        result = {
            "urlAoMapImage": outFileNameBase + '.png',
            "urlAoMappingJson": outFileNameBase + '.json',
            "urlIgxcModified": outFileNameBase + '.igxc',
            "urlIgxcOriginal": outFileNameBase + '_original.igxc',
            "transforms": mappingResult,
            "igxcModified": igxcContent
        }
        return result

    # save unmodified version of igxc
    if igxcContent is not None:
        igxcOutfileName = joinOutputPath(outFileNameBase + "_original", 'igxc')
        with open(igxcOutfileName, 'w') as igxcOutfile:
            json.dump(igxcContent,
                      igxcOutfile,
                      indent=4,
                      separators=(',', ': '),
                      sort_keys=False)

    # result not in cache? proceed with baking
    root = None
    try:
        root = igxc.load(igxcContent, basePath)
    except AttributeError as e:
        errorMsg = "attributes missing in igxc ({})".format(" ".join(e.args))
        colorprint("startWithDirectArgs: " + errorMsg, 31)
        print(e)
        result = {
            "error": errorMsg,
            "urlIgxcOriginal": outFileNameBase + '_original.igxc'
        }
        return result
    except ConnectionError as e:
        errorMsg = "file referenced in igxc could not be fetched " + " ".join(
            e.args)
        colorprint("startWithDirectArgs: " + errorMsg, 31)
        print(e)
        result = {
            "error": errorMsg,
            "urlIgxcOriginal": outFileNameBase + '_original.igxc'
        }
        return result
    except Exception as e:
        errorMsg = "igxc couldn't be loaded"
        colorprint("startWithDirectArgs: " + errorMsg, 31)
        print(e)
        print(type(e))
        result = {
            "error": errorMsg,
            "urlIgxcOriginal": outFileNameBase + '_original.igxc'
        }
        return result

    triCounter = visitor.TriCounter()
    root.accept(triCounter)
    print('total triangles', triCounter.count)

    vertices = numpy.ndarray((triCounter.count, 3, 3), dtype=numpy.float)
    normals = numpy.ndarray((triCounter.count, 3, 3), dtype=numpy.float)
    texcoord = numpy.ndarray((triCounter.count, 3, 2), dtype=numpy.float)

    meshCounter = visitor.MeshCounter()
    root.accept(meshCounter)
    print('total meshes', meshCounter.count)

    amountBucketsX = math.ceil(math.sqrt(meshCounter.count))
    amountBucketsY = math.ceil(meshCounter.count / amountBucketsX)
    print('buckets: {}x{}'.format(amountBucketsX, amountBucketsY))
    uvPacker = visitor.SimplePacker(amountBucketsX, amountBucketsY,
                                    resolutionValue)
    triExtractor = visitor.TransformedTriExtractor(vertices,
                                                   normals,
                                                   texcoord,
                                                   packer=uvPacker)
    root.accept(triExtractor)

    # if face normals should be used, empty normals array
    if "face_normals" in args and args["face_normals"] == True:
        normals = numpy.zeros((0, 3, 3), dtype=numpy.float)

    # print(vertices)
    # print(texcoord)
    # print(triExtractor.mapping)
    # print("Packer:", uvPacker.i)

    img = generateMap(vertices, normals, texcoord,
                      (resolutionValue, resolutionValue))

    # save AO map image
    output = joinOutputPath(outFileNameBase, 'png')
    print("Save output at", joinOutputPath(outFileNameBase, 'png'))
    img.save(output)

    # save AO mapping
    mappingOutfileName = joinOutputPath(outFileNameBase, 'json')
    with open(mappingOutfileName, 'w') as outfile:
        json.dump(triExtractor.mapping,
                  outfile,
                  indent=4,
                  separators=(',', ': '),
                  sort_keys=True)

    # extend existing IGXC with AO entries
    if igxcContent is not None:
        modifyIgxc(igxcContent, outFileNameBase + '.png', triExtractor.mapping)
        igxcOutfileName = joinOutputPath(outFileNameBase, 'igxc')
        with open(igxcOutfileName, 'w') as igxcOutfile:
            json.dump(igxcContent,
                      igxcOutfile,
                      indent=4,
                      separators=(',', ': '),
                      sort_keys=False)

    if debug:
        import viewer
        viewer.debug_view(vertices, texcoord, image=img)

    result = {
        "urlAoMapImage": outFileNameBase + '.png',
        "urlAoMappingJson": outFileNameBase + '.json',
        "urlIgxcModified": outFileNameBase + '.igxc',
        "urlIgxcOriginal": outFileNameBase + '_original.igxc',
        "transforms": triExtractor.mapping,
        "igxcModified": igxcContent
    }
    return result


if __name__ == '__main__':
    start()
