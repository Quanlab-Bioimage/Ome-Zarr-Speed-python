入口：ZarrMaker.py
调用方式：
config = {
        'imgPath': r'E:\imgslice',  # imgPath
        'savePath': r'H:\omeZarr',  # savePath
        'sampleType': 0,  # 0:max 1:mean
        'startEpoch': 0,
        'noUseCpuNumber': 1,  # noUseCpuNumber
        'smallSize': [512, 512, 512]
    }
createZarrData(config)
参数解释：
    imgPath:图像序列文件夹路径，
    savePath:数据保存文件夹路径，
    sampleType：采样方式，0：最大值采样，1：均值采样
    startEpoch：开始轮次，从0开始，用于异常中断后，从指定轮次继续制作
    noUseCpuNumber：保留的cpu核心数量，
    smallSize：小块尺寸，[x,y,z]