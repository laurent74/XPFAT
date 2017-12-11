#!/usr/bin/env python

import os, argparse, subprocess, plistlib
from shutil import copyfile


##################################################
# FUNCTIONS
##################################################


def targetsFrom(objects, ignoreTestTargets, withPrefix = None):
    targets = dict()
    
    for key in objects:
        object = objects[key]
        if isObjectType(object, "PBXNativeTarget") and "dependencies" in object.keys():
            if len(object["dependencies"]) == 0:
                continue
            if ignoreTestTargets and objectNameHasSuffix(object, "Tests"):
                continue
            if withPrefix:
                if objectNameHasPrefix(object, withPrefix):
                    targets[key] = object
            else:
                targets[key] = object

    return targets

def isObjectType(object, type):
    if "isa" in object.keys():
        return object["isa"] == type
    return False

def objectNameHasPrefix(object, prefix):
    if "name" in object.keys():
        return object["name"].startswith(prefix)
    return False

def objectNameHasSuffix(object, suffix):
    if "name" in object.keys():
        return object["name"].endswith(suffix)
    return False

def logTargetsForFilesAmong(objects, supportedFileTypes, ignoreTestFiles):
    targets = targetsFrom(objects, ignoreTestFiles, None)
    ignoredUnsupportedFilesCount = 0
    ignoredTestFilesCount = 0
    
    # find the files
    for fileUid in objects:
        file = objects[fileUid]
        if isObjectType(file, "PBXFileReference") and "path" in file.keys():
            fileName = file["path"]
            
            # ignore unsupported files if requested
            if len(supportedFileTypes) > 0 and not fileName.endswith(tuple(supportedFileTypes)):
                ignoredUnsupportedFilesCount += 1
                continue
            
            # ignore test files if requested
            if ignoreTestFiles and (os.path.splitext(fileName)[0]).endswith("Tests"):
                ignoredTestFilesCount += 1
                continue
            
            print("---------------------")
            print("file: " + fileName)

            # find the buildFiles for this file
            buildFiles = dict()
            for buildFileUid in objects:
                buildFile = objects[buildFileUid]
                if isObjectType(buildFile, "PBXBuildFile") and "fileRef" in buildFile.keys():
                    if buildFile["fileRef"] == fileUid:
                        buildFiles[buildFileUid] = buildFile

            # find the buildPhase for each buildFile
            buildPhaseType = "PBXSourcesBuildPhase" if fileName.endswith(tuple([".m", ".swift"])) else "PBXResourcesBuildPhase"
            
            buildPhases = dict()
            for buildPhaseUid in objects:
                buildPhase = objects[buildPhaseUid]
                if isObjectType(buildPhase, buildPhaseType) and "files" in buildPhase.keys():
                    buildPhaseFiles = buildPhase["files"]
                    for buildFileUid in buildFiles:
                        if buildFileUid in buildPhaseFiles:
                            buildPhases[buildPhaseUid] = buildPhase

            fileTargets = dict()
            # find targets for each buildPhase
            for targetUid in targets:
                target = targets[targetUid]
                if "buildPhases" in target.keys() and "name" in target.keys():
                    targetBuildPhases = target["buildPhases"]
                    targetName = target["name"]
                    for buildPhaseUid in buildPhases:
                        if buildPhaseUid in targetBuildPhases:
                            fileTargets[targetUid] = target
                            print("target: " + targetName)

    print("--- found targets ---")
    for targetUid in targets:
        target = targets[targetUid]
        print(targetUid + " " + target["name"])
    print("--- ignored files ---")
    print("ignored " + str(ignoredUnsupportedFilesCount) + " unsupported files and " + str(ignoredTestFilesCount) + " test files, as requested")


##################################################
# RUN
##################################################


parser = argparse.ArgumentParser(description="list the files of an Xcode project and the targets they are included in")
parser.add_argument("--pbxproj", dest="projectFilePath", help="the path to the .pbxproj file to inspect")
parser.add_argument("--supported-file-types", dest="supportedFileTypes", help="the file types to list (comma-separated). E.g.: m,swift,xib,storyboard. Leave empty to list them all")
parser.add_argument("--ignore-test-files", dest="ignoreTestFiles", help="if set, do not list the unit test files", action="store_true")
args = parser.parse_args()
projectFilePath = args.projectFilePath
ignoreTestFiles = args.ignoreTestFiles

# validate arguments
if not projectFilePath:
    print("missing path to the .pbxproj file in the arguments. Use --pbxproj")
    sys.exit(1)

supportedFileTypes = []
if args.supportedFileTypes:
    for fileType in args.supportedFileTypes.split(','):
        extension = fileType if fileType.startswith(".") else "." + fileType
        supportedFileTypes.append(extension)

# create an xml version of the .pbxproj, as a temporary file
xmlProjectFilePath = os.path.splitext(projectFilePath)[0] + ".xml"
copyfile(projectFilePath, xmlProjectFilePath)
subprocess.call(["plutil", "-convert", "xml1", xmlProjectFilePath])

with open(xmlProjectFilePath, 'rb') as fp:
    plist = plistlib.load(fp)
    objects = plist["objects"]
    logTargetsForFilesAmong(objects, supportedFileTypes, ignoreTestFiles)

# delete the temporary xml project file
os.remove(xmlProjectFilePath)

