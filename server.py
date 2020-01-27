import json
import os
from pprint import pprint

from pathlib import Path
from bottle import Bottle, run, PasteServer, response, request, static_file
from service import default_out, aoConfig
from bakerman import BakingMan, BakingJob
from util import colorprint, prepareOutFilename, default_out_dir
from remote import cachedir

app = Bottle()

bakingMan = BakingMan()
bakingMan.start()


def extractPostParams(requestParam):
    jobSource = request.POST
    try:
        # check if json entry is available
        jsonSource = request.json
        if jsonSource is not None:
            jobSource = jsonSource
    except Exception as e:
        print("bakeDirect: json couldn't be parsed")
        print(e)
    # print(jobSource)
    return jobSource


def staticFileWithCors(filename, root, **params):
    httpResponse = static_file(filename, root, **params)

    httpResponse.headers['Access-Control-Allow-Origin'] = '*'
    httpResponse.headers[
        'Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    httpResponse.headers[
        'Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

    return httpResponse


def PARAMETER():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers[
        'Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


def routeWithOptions(**kwargs):
    def decorator(callback):
        kwargs['callback'] = callback
        app.route(**kwargs)

        kwargs['method'] = 'OPTIONS'
        kwargs['callback'] = PARAMETER

        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers[
            'Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
        response.headers[
            'Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        app.route(**kwargs)
        return callback

    return decorator


@app.hook('after_request')
def enable_cors():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers[
        'Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


@routeWithOptions(path='/bakeFile/<fileParam:path>', method="GET")
def bakeFile(fileParam: str):
    global bakingMan

    jobParams = {"file": fileParam, "resolution": aoConfig["resolution"]}
    # print(jobParams)
    jobId = bakingMan.addJob(jobParams)
    response.content_type = "application/json"
    return {"jobId": jobId}


@routeWithOptions(path='/getFile/<filename:path>', method="GET")
def getFile(filename):
    colorprint("getFile " + filename, 33)
    return staticFileWithCors(filename, './out/', download=filename)


@routeWithOptions(path='/removeResults/', method="GET")
def removeResults():
    print("remove result files")
    folder = default_out_dir
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path) and str(the_file).startswith("AO_"):
                print("   remove", the_file)
                os.unlink(file_path)
        except Exception as e:
            print(e)

    print("remove cache files")
    folder = cachedir
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                print("   remove", the_file)
                os.unlink(file_path)
        except Exception as e:
            print(e)


@routeWithOptions(path="/bakeUrl/", method="POST")
def bakeUrl():
    global bakingMan
    # print(request)
    # print(request.POST)
    # print(request.POST.__dict__)
    # print(request.headers.__dict__)
    # print(request.method)

    jobSource = extractPostParams(request)

    urlParam = jobSource["url"]
    # print(urlParam)

    resolutionParam = jobSource["resolution"]
    resolutionValue = aoConfig["resolution"]
    if resolutionParam is not None:
        resolutionValue = int(resolutionParam)

    args = {"url": urlParam, "resolution": resolutionValue}
    # print(args)

    jobId = bakingMan.addJob(args)
    response.content_type = "application/json"
    return {"jobId": jobId}


@routeWithOptions(path="/bakeDirect/", method="POST")
def bakeDirect():
    global bakingMan
    # print(request)
    # print(request.POST)
    # print(request.POST.__dict__)
    # print(request.headers.__dict__)
    # print(request.method)

    jobSource = extractPostParams(request)

    igxcString = jobSource["igxcContent"]
    # print(igxcString)
    if not igxcString or igxcString == "null":
        colorprint("No igxcContent found in POST request in bakeDirect/", 31)
        return {"error": "No igxcContent found in POST request in bakeDirect/"}

    try:
        if isinstance(igxcString, str):
            igxcContent = json.loads(igxcString)
        else:
            igxcContent = igxcString
    except Exception as e:
        colorprint("Exception in bakeDirect/", 31)
        print(e)
        return {"error": "igxcContent couldn't be parsed"}
    # print(igxcContent)

    basePath = jobSource["basePath"]
    # print(basepath)

    resolutionValue = aoConfig["resolution"]
    resolutionParam = jobSource["resolution"]
    if resolutionParam is not None:
        resolutionValue = int(resolutionParam)

    args = {
        "basePath": basePath,
        "igxcContent": igxcContent,
        "resolution": resolutionValue
    }
    # print(args)

    jobId = bakingMan.addJob(args)
    response.content_type = "application/json"
    return {"jobId": jobId}


@routeWithOptions(path='/pullState/<jobId>', method="GET")
def pullState(jobId: str):
    global bakingMan
    colorprint("pullState id {}".format(jobId), 33)

    result = {"state": "undefined"}
    if bakingMan.hasJob(jobId):
        result = bakingMan.getJob(jobId)

    # print(result)
    jsonResult = json.dumps(result,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '))
    response.content_type = "application/json"
    return jsonResult


@routeWithOptions(path='/pullAll/', method="GET")
def pullAll():
    global bakingMan
    colorprint("pullAll", 33)
    result = bakingMan.getAllJobs()
    # print(result)
    jsonResult = json.dumps(result,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '))
    response.content_type = "application/json"
    return jsonResult


@routeWithOptions(path='/getImage/<jobId>', method="GET")
def getImage(jobId: str):
    global bakingMan
    absPath = os.path.join(os.path.abspath("."), default_out_dir)
    print(absPath)
    if bakingMan.isJobFinished(jobId):
        job = bakingMan.getJob(jobId)
        fileName = job["jobArgs"]["out"] + ".png"
        return staticFileWithCors(fileName, absPath)


serverConfig = {"port": 8080, "host": "0.0.0.0"}

try:
    with open("config.json", "r") as f:
        configContent = json.load(f)
        if "port" in configContent:
            serverConfig["port"] = configContent["port"]
        if "host" in configContent:
            serverConfig["host"] = configContent["host"]
        if "resolution" in configContent:
            aoConfig["resolution"] = configContent["resolution"]
        print(serverConfig)
        print(aoConfig)
except FileNotFoundError:
    print("Config file not found, using standard port", serverConfig["port"])

try:
    app.run(host=serverConfig["host"],
            port=serverConfig["port"],
            debug=True,
            server=PasteServer)
except KeyboardInterrupt:
    pass
finally:
    bakingMan.stop()
