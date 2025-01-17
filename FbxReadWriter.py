import os
from typing import Dict

import numpy as np
from scipy.spatial.transform import Rotation as R

from SmplObject import SmplObjects

try:
    from FbxCommon import *
    from fbx import *
except ImportError:
    print("Error: module FbxCommon failed to import.\n")
    print("Copy the files located in the compatible sub-folder lib/python<version> into your python interpreter "
          "site-packages folder.")
    import platform

    if platform.system() == 'Windows' or platform.system() == 'Microsoft':
        print('For example: copy ..\\..\\lib\\Python37_x64\\* C:\\Python27\\Lib\\site-packages')
    elif platform.system() == 'Linux':
        print('For example: cp ../../lib/Python37_x64/* /usr/local/lib/python2.7/site-packages')
    elif platform.system() == 'Darwin':
        print('For example: cp ../../lib/Python37_x64/* '
              '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages')


def _write_curve(lCurve: FbxAnimCurve, data: np.ndarray, fbx_time: FbxTime):
    """
    data: np.ndarray of (N, )
    """
    lTime = FbxTime()
    lTime.SetGlobalTimeMode(fbx_time)  # Set to fps=60
    data = np.squeeze(data)

    lCurve.KeyModifyBegin()
    for i in range(data.shape[0]):
        lTime.SetFrame(i, fbx_time)
        lKeyIndex = lCurve.KeyAdd(lTime)[0]
        lCurve.KeySetValue(lKeyIndex, data[i])
        lCurve.KeySetInterpolation(lKeyIndex, FbxAnimCurveDef.eInterpolationCubic)
    lCurve.KeyModifyEnd()


class FbxReadWrite(object):
    def __init__(self, fbx_source_path):
        # Prepare the FBX SDK.
        lSdkManager, lScene = InitializeSdkObjects()
        self.lSdkManager = lSdkManager
        self.lScene = lScene

        # Load the scene.
        # The example can take a FBX file as an argument.
        print("\nLoading File: {}".format(fbx_source_path))
        lResult = LoadScene(self.lSdkManager, self.lScene, fbx_source_path)
        if not lResult:
            raise Exception("An error occured while loading the scene :(")

    def add_animation(self, pkl_filename: str, fps: int, smpl_params: Dict, verbose: bool = False):
        lScene = self.lScene

        if fps == 30:
            fbx_time = FbxTime.eFrames30
        else:
            fbx_time = FbxTime.eFrames60

        # 0 set fps
        lGlobalSettings = lScene.GetGlobalSettings()
        if verbose:
            print("Before time mode:{}".format(lGlobalSettings.GetTimeMode()))
        lGlobalSettings.SetTimeMode(fbx_time)
        if verbose:
            print("After time mode:{}".format(lScene.GetGlobalSettings().GetTimeMode()))

        self.destroy_all_animation()

        lAnimStackName = pkl_filename
        lAnimStack = FbxAnimStack.Create(lScene, lAnimStackName)
        lAnimLayer = FbxAnimLayer.Create(lScene, "Base Layer")
        lAnimStack.AddMember(lAnimLayer)
        lRootNode = lScene.GetRootNode()

        names = SmplObjects.joints

        # 1. Write smpl_poses
        smpl_poses = smpl_params["smpl_poses"]
        for idx, name in enumerate(names):
            node = lRootNode.FindChild(name)
            rotvec = smpl_poses[:, idx * 3:idx * 3 + 3]
            _euler = []
            for _f in range(rotvec.shape[0]):
                r = R.from_rotvec([rotvec[_f, 0], rotvec[_f, 1], rotvec[_f, 2]])
                euler = r.as_euler('xyz', degrees=True)
                _euler.append([euler[0], euler[1], euler[2]])
            euler = np.vstack(_euler)

            lCurve = node.LclRotation.GetCurve(lAnimLayer, "X", True)
            if lCurve:
                _write_curve(lCurve, euler[:, 0], fbx_time)
            else:
                print("Failed to write {}, {}".format(name, "x"))

            lCurve = node.LclRotation.GetCurve(lAnimLayer, "Y", True)
            if lCurve:
                _write_curve(lCurve, euler[:, 1], fbx_time)
            else:
                print("Failed to write {}, {}".format(name, "y"))

            lCurve = node.LclRotation.GetCurve(lAnimLayer, "Z", True)
            if lCurve:
                _write_curve(lCurve, euler[:, 2], fbx_time)
            else:
                print("Failed to write {}, {}".format(name, "z"))

        # 3. Write smpl_trans to f_avg_root
        smpl_trans = smpl_params["smpl_trans"]
        name = "m_avg_root"
        node = lRootNode.FindChild(name)
        lCurve = node.LclTranslation.GetCurve(lAnimLayer, "X", True)
        if lCurve:
            _write_curve(lCurve, smpl_trans[:, 0], fbx_time)
        else:
            print("Failed to write {}, {}".format(name, "x"))

        lCurve = node.LclTranslation.GetCurve(lAnimLayer, "Y", True)
        if lCurve:
            _write_curve(lCurve, smpl_trans[:, 1], fbx_time)
        else:
            print("Failed to write {}, {}".format(name, "y"))

        lCurve = node.LclTranslation.GetCurve(lAnimLayer, "Z", True)
        if lCurve:
            _write_curve(lCurve, smpl_trans[:, 2], fbx_time)
        else:
            print("Failed to write {}, {}".format(name, "z"))

    def write_fbx(self, write_base: str, filename: str):
        if not os.path.isdir(write_base):
            os.makedirs(write_base, exist_ok=True)
        write_path = os.path.join(write_base, filename.replace(".pkl", ""))
        print("Writing to {}".format(write_path))
        lResult = SaveScene(self.lSdkManager, self.lScene, write_path)

        if not lResult:
            raise Exception("Failed to write to {}".format(write_path))

    def destroy(self):
        self.lSdkManager.Destroy()

    def destroy_all_animation(self):
        lScene = self.lScene
        animStackCount = lScene.GetSrcObjectCount(FbxCriteria.ObjectType(FbxAnimStack.ClassId))
        for i in range(animStackCount):
            lAnimStack = lScene.GetSrcObject(FbxCriteria.ObjectType(FbxAnimStack.ClassId), i)
            lAnimStack.Destroy()
