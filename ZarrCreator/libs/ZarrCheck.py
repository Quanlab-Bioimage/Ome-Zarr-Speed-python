'''Zarr检查'''
import os
from os.path import join

import blosc
import numpy as np
import tifffile
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader

def ReadTSInd(tifPath, level, ind):
    ls = os.listdir(tifPath)
    lsLen = len(ls)
    scale = 2 ** level
    z0 = ind * scale
    z1 = min(z0 + scale, lsLen)
    tImg = None
    for z in range(z0, z1):
        img = tifffile.imread(join(tifPath, ls[z]))
        for l in range(0, level):
            tLs = []
            for ny in range(2):
                for nx in range(2):
                    tLs.append(img[nx::2, ny::2])
            img = np.max(tLs, axis=0)
        if tImg is None: tImg = img
        else: tImg = np.max([tImg, img], axis=0)
    return tImg

def CheackZarr():
    # tifPath = r'O:\BigDataTestDataSet\Bit8\DataSet11'
    # zarrPath = r'O:\BigDataTestDataSet\Bit8\DataSet11-BV'

    tifPath = r'H:\DataSet11'
    zarrPath = r'H:\omezarrtest'

    # tifPath = r'H:\imgslice'
    # zarrPath = r'H:\zarrtest2'
    reader = Reader(parse_url(zarrPath))
    nodes = list(reader())
    zarr_node = nodes[0]
    totalLevel = len(zarr_node.data)
    for level in range(totalLevel):
        zarrImgHand = zarr_node.data[level]
        if level == 0:
            ind = zarrImgHand.shape[0] - 1
        else: ind = zarrImgHand.shape[0] - 2
        # ind = 0
        zarrImg = np.asarray(zarrImgHand[ind])
        tifImg = ReadTSInd(tifPath, level, ind)
        img = zarrImg - tifImg
        if img.max() != 0:
            print('Error', level)
            return
        else:
            print(level, 'Ok')

def BloscRead():
    path = r'O:\BigDataTestDataSet\Bit8\DataSet11-BV\2\2\0\0'
    with open(path, 'rb') as f:
        cdata = f.read()
        raw = blosc.decompress(cdata)
        img = np.frombuffer(raw, dtype=np.uint8).reshape([12, 280, 138])
        print(img.min(), img.max(), img.mean(), img.shape)

if __name__ == '__main__':
    CheackZarr()
    # BloscRead()
