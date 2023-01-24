"""
   Copyright (C) 2017 Autodesk, Inc.
   All rights reserved.

   Use of this software is subject to the terms of the Autodesk license agreement
   provided at the time of installation or download, or which otherwise accompanies
   this software in either electronic or hard copy form.

"""

from FbxReadWriter import FbxReadWrite
from SmplObject import SmplObjects
import argparse
import tqdm
import os


def get_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_pkl_base', type=str, required=True)
    parser.add_argument('--fbx_source_path', type=str, required=True)
    parser.add_argument('--output_base', type=str, required=True)
    parser.add_argument('--fps', type=int, required=False)

    return parser.parse_args()


if __name__ == "__main__":
    args = get_arg()
    input_pkl_base = args.input_pkl_base
    fbx_source_path = args.fbx_source_path
    output_base = args.output_base
    fps = args.fps

    smplObjects = SmplObjects(input_pkl_base)
    for pkl_name, smpl_params in tqdm.tqdm(smplObjects):
        pkl_name = os.path.basename(pkl_name).split('/')[-1]
        try:
            fbxReadWrite = FbxReadWrite(fbx_source_path)
            fbxReadWrite.add_animation(pkl_name, fps, smpl_params)
            fbxReadWrite.write_fbx(output_base, pkl_name)
        except Exception as e:
            fbxReadWrite.destroy()
            print("- - Destroy")
            raise e
        finally:
            fbxReadWrite.destroy()
