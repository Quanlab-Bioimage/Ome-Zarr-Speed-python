'''Zarr大数据制作'''
import datetime
import os, psutil, json
import shutil
import time
from os.path import join
import numpy as np
from PIL import Image
import subprocess as sp

'''Zarr配置文件生成'''


def GenerateZarrBaseInfo(root, bigSize, smallSize, dtype, level=1):
    bigSize2 = bigSize.copy()
    # zattrs生成
    zattrs = {
        'multiscales': [
            {
                'axes': [
                    {
                        'name': 'z',
                        'type': 'space',
                    },
                    {
                        'name': 'y',
                        'type': 'space',
                    },
                    {
                        'name': 'x',
                        'type': 'space',
                    },
                ],
                'datasets': [],
                'name': '/',
                'version': '0.4',
            }
        ]
    }
    for _level in range(level):
        scale = 2 ** _level
        zattrs['multiscales'][0]['datasets'].append(
            {
                "coordinateTransformations": [
                    {
                        "scale": [
                            scale,
                            scale,
                            scale,
                        ],
                        "type": "scale",
                    },
                ],
                "path": str(_level),
            },
        )
        curPath = join(root, str(_level))
        os.makedirs(curPath, exist_ok=True)
        zarryInfo = {
            'chunks': smallSize.tolist(),
            'compressor': {
                'blocksize': 0,
                'clevel': 5,
                'cname': 'zlib',
                'id': 'blosc',
                'shuffle': 1,
            },
            "dimension_separator": "/",
            "dtype": dtype.descr[0][1],
            "fill_value": 0,
            "filters": None,
            "order": "C",
            "shape": bigSize2.tolist(),
            "zarr_format": 2,
        }
        with open(join(curPath, '.zarray'), 'w') as f:
            f.write(json.dumps(zarryInfo))
        bigSize2 = (bigSize2 // 2).astype(np.int32)
    zattrsPath = join(root, '.zattrs')
    with open(zattrsPath, 'w') as f:
        f.write(json.dumps(zattrs))
    # zgroup生成
    zgroup = {
        "zarr_format": 2
    }
    zgroupPath = join(root, '.zgroup')
    with open(zgroupPath, 'w') as f:
        f.write(json.dumps(zgroup))


# 获取图像尺寸以及类型
def GetImgBaseInfo(add):
    # 获取图像
    f = Image.open(add)
    if f.mode == 'L':
        dtype = np.dtype(np.uint8)
        pixSpace = 1
    elif f.mode == 'I;16':
        dtype = np.dtype(np.uint16)
        pixSpace = 2
    else:
        print('Error: 文件格式错误，目前仅支持uint8和uint16')
        return False, []
    f.close()
    return True, [f.height, f.width, dtype, pixSpace]


# 计算总金字塔等级
def ComputeLevelFun1(bigSize, smallSize):
    bigSize2 = bigSize.copy()
    level = 1
    while (bigSize2 - smallSize).min() > 0:
        level += 1
        bigSize2 = bigSize2 // 2
    return level


# 预估内存占用
def EstilmatUseMem(bigSize, smallSize, totalLevel, pixSpace, noUseCpuNumber=1):
    Ncpu = psutil.cpu_count() - noUseCpuNumber
    readNumber = 2 * Ncpu
    smallMem = smallSize.prod() * pixSpace  # 一个小块占用内存
    bigMem = bigSize[1] * bigSize[2] * pixSpace  # 一张大图占用内存
    # 大图内存占用，生数据+编码空间数据
    bigImgLsMem = bigMem * readNumber + bigMem * 1.4 * readNumber
    # 多分辨大图内存占用
    bigLevImgLsMem = 0
    bigSize2 = bigSize.copy()[1:]
    smallSize2 = smallSize[1:]
    for level in range(totalLevel):
        bigSize3 = np.ceil(bigSize2 / smallSize2) * smallSize2
        tMem = bigSize3.prod() * pixSpace
        bigLevImgLsMem += tMem * readNumber
        bigSize2 = bigSize2 // 2
    # 编码小块的内存占用
    smallDataLevelLsMem = 0
    bigSize2 = bigSize.copy()[1:]
    for level in range(totalLevel):
        sliceNumber = np.ceil(bigSize2 / smallSize2)
        smallNumber = sliceNumber.prod()
        smallDataLevelLsMem += smallMem * smallNumber + smallMem * 1.2 * smallNumber
        bigSize2 = bigSize2 // 2
    useMem = bigImgLsMem + bigLevImgLsMem + smallDataLevelLsMem
    return useMem


'''根据内存自动调整金字塔级别'''


def AutoLevelFromMem(bigSize, smallSize, totalLevel, pixSpace, noUseCpuNumber):
    oriTotalLevel = totalLevel
    bigSize2 = bigSize.copy()
    yLen = bigSize2[1]
    while True:
        needUseMem = EstilmatUseMem(np.array(bigSize2, dtype=np.int32), smallSize, totalLevel, pixSpace, noUseCpuNumber)
        freeUseMem = psutil.virtual_memory().free
        if needUseMem > freeUseMem * 0.98:
            # yLen //= 2
            t = np.log2(yLen)
            if t == int(t):
                t = int(t - 1)
            else:
                t = int(t)
            yLen = int(2 ** t)
            bigSize2 = np.array([bigSize2[0], yLen, bigSize2[2]], dtype=np.int32)
            totalLevel = ComputeLevelFun1(bigSize2, smallSize)
            if totalLevel < oriTotalLevel and totalLevel < 2:
                return False, 'Error, 内存不足, 需要内存%.2fGB' % (needUseMem / 1024 ** 3), ''
        else:
            break
    print('需要%.2fGB' % (needUseMem / 1024 ** 3))
    return True, yLen, totalLevel


# def QuickMakeZarr():
#     # path = r'O:\BigDataTestDataSet\Bit8\DataSet11'
#     # savePath = r'O:\BigDataTestDataSet\Bit8\DataSet11-BV'
#     path = r'O:\BigDataTestDataSet\Bit16\TDIA1302b002_DataSet11'
#     savePath = r'O:\BigDataTestDataSet\Bit16\TDIA1302b002_DataSet11-BV'
#     smallSize = np.array([512, 512, 512], dtype=np.int32)
#     noUseCpuNumber = 1          # 空闲CPU数量
#     sampleType = 0              # 投影方式 0--最大值投影 1--均值投影
#     if os.path.isdir(savePath): shutil.rmtree(savePath)
#     os.makedirs(savePath, exist_ok=True)
#     exePath = join(os.getcwd(), 'QuickMakeZarr.exe')
#     ls = os.listdir(path)
#     lsLen = len(ls)
#     # lsLen = 99
#     res, tInfo = GetImgBaseInfo(join(path, ls[0]))
#     if not res: return
#     bigSize = np.array([lsLen, tInfo[0], tInfo[1]], dtype=np.int32)
#     dtype, pixSpace = tInfo[2], tInfo[3]
#     totalLevel = ComputeLevelFun1(bigSize, smallSize)
#     # 判断内存是否够用
#     res, yLen, newLevel = AutoLevelFromMem(bigSize, smallSize, totalLevel, pixSpace, noUseCpuNumber)
#     if not res:
#         print(yLen)
#         return
#     # 生成配置文件
#     GenerateZarrBaseInfo(savePath, bigSize, smallSize, dtype, level=totalLevel)
#     # 制作
#     s1 = time.time()
#     totalCount = np.ceil(bigSize[1] / yLen)
#     curStep = 0
#     for yStart in range(0, bigSize[1], yLen):
#         print('[%d | %d]' % (curStep, totalCount))
#         ySize = min(yLen, bigSize[1] - yStart)
#         # exe
#         command = '%s %d %d %d %d %d %d %d %d %d %d %s %s %d %d %f %d' % (exePath, curStep,
#             0 if dtype == np.uint8 else 1, 0, yStart, bigSize[2], ySize, smallSize[2], smallSize[1], smallSize[0],
#             newLevel, path, savePath, sampleType, lsLen, 0.9, noUseCpuNumber)
#         print(command)
#         # os.system(command)
#         p = sp.Popen(command)
#         p.wait()
#         curStep += 1
#         userTime = time.time() - s1
#         surpluTime = userTime / curStep * (totalCount - curStep)
#         print('[%d | %d] userTime: %.4fs\tSurplusTime: %.4fS' % (curStep, totalCount, userTime, surpluTime))

class LogProvider:
    def __init__(self):
        self.infoSignal = None

    def log(self, logPath, msg):
        with open(logPath, 'a+') as f:
            f.write(msg + '\n')

    def log_and_show(self, logPath, msg):
        with open(logPath, 'a+') as f:
            f.write(msg + '\n')
        if self.infoSignal is not None:
            self.infoSignal.emit(msg)


logProvider = LogProvider()


def getTime(format_str='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时间
    :param format_str: 格式字符串,默认%Y-%m-%d %H:%M:%S
    :return:str 当前时间
    """
    return datetime.datetime.now().strftime(format_str)


def QuickMakeZarr(config):
    path = config['imgPath']
    savePath = config['savePath']
    batch = config['smallSize']
    smallSize = np.array([batch[0], batch[1], batch[2]], dtype=np.int32)  # zyx
    noUseCpuNumber = config['noUseCpuNumber']  # 空闲CPU数量
    sampleType = config['sampleType']  # 投影方式 0--最大值投影 1--均值投影

    startEpoch = config['startEpoch']
    # 回馈信号
    # progressSignal = config['progressSignal']
    # infoSignal = config['infoSignal']
    # logProvider.infoSignal = infoSignal
    # doneSignal = config['doneSignal']
    # 判断保存文件夹是否存在
    if not os.path.exists(savePath):
        os.makedirs(savePath)
    # 日志文件位置
    baseLog = join(savePath, 'log.txt')
    epochPath = join(savePath, 'startEpoch.txt')
    # 制作软件位置
    exePath = join(os.getcwd(), 'libs', 'QuickMakeZarr.exe')
    # exePath = join(os.getcwd(), 'QuickMakeZarr.exe')
    ls = os.listdir(path)
    lsLen = len(ls)
    # lsLen = 1600
    res, tInfo = GetImgBaseInfo(join(path, ls[0]))
    if not res:
        logProvider.log_and_show(baseLog, 'Error: 文件格式错误，目前仅支持uint8和uint16')
        # doneSignal.emit('error')
        return
    bigSize = np.array([lsLen, tInfo[0], tInfo[1]], dtype=np.int32)
    dtype, pixSpace = tInfo[2], tInfo[3]
    totalLevel = ComputeLevelFun1(bigSize, smallSize)
    # 判断内存是否够用
    res, yLen, newLevel = AutoLevelFromMem(bigSize, smallSize, totalLevel, pixSpace, noUseCpuNumber)
    if not res:
        print(yLen)
        logProvider.log_and_show(baseLog, yLen)
        # doneSignal.emit('error')
        return
    # 生成配置文件
    GenerateZarrBaseInfo(savePath, bigSize, smallSize, dtype, level=newLevel)
    # 制作
    s1 = time.time()
    totalCount = np.ceil(bigSize[1] / yLen)
    curStep = 0
    curEpoll = 0
    for yStart in range(0, bigSize[1], yLen):
        # if threadStatus.stop:
        #     return
        print('[%d | %d]' % (curStep, totalCount))
        # progressSignal.emit((curStep, totalCount))
        logProvider.log_and_show(baseLog, '[%d | %d]' % (curStep, totalCount))
        ySize = min(yLen, bigSize[1] - yStart)
        # exe
        command = '%s %d %d %d %d %d %d %d %d %d %d %s %s %d %d %f %d' % (exePath, curStep,
                                                                          0 if dtype == np.uint8 else 1, 0, yStart,
                                                                          bigSize[2], ySize, smallSize[2], smallSize[1],
                                                                          smallSize[0],
                                                                          newLevel, path, savePath, sampleType, lsLen,
                                                                          0.9, noUseCpuNumber)
        print(command)

        logProvider.log(epochPath, str(curEpoll))
        if curEpoll >= startEpoch:
            while True:
                # if threadStatus.stop:
                #     return
                # 尝试制作
                log = "{} Epoch {} started.".format(getTime(), curEpoll)
                logProvider.log_and_show(baseLog, log)
                # 调用制作
                p = sp.Popen(command, creationflags=sp.CREATE_NEW_CONSOLE)
                p.wait()
                # 一轮调用完毕, 检测是否制作成功
                statusPath = join(savePath, '{}.txt'.format(curStep))
                if not os.path.exists(statusPath):
                    # 制作失败，写日志
                    log = "{} Epoch {} error,we will continue after 60 seconds.".format(getTime(), curEpoll)
                    logProvider.log_and_show(baseLog, log)
                    # 等待60秒继续
                    # if threadStatus.stop:
                    #     return
                    time.sleep(60)
                    continue
                else:
                    # 制作成功,跳出并记录
                    log = "{} Epoch {} success.".format(getTime(), curEpoll)
                    logProvider.log_and_show(baseLog, log)
                    curStep += 1
                    userTime = time.time() - s1
                    surpluTime = userTime / curStep * (totalCount - curStep)
                    info = '[%d | %d] userTime: %.4fs\tSurplusTime: %.4fS' % (
                        curStep - 1, totalCount, userTime, surpluTime)
                    print(info)
                    logProvider.log_and_show(baseLog, info)
                    break
        else:
            curStep += 1
        curEpoll += 1
    # 制作结束
    logProvider.log(epochPath, str(curEpoll))
    # logProvider.log(epochPath, str(curEpoll))
    # progressSignal.emit((curStep, totalCount))
    # doneSignal.emit('success')


if __name__ == '__main__':
    QuickMakeZarr({})
