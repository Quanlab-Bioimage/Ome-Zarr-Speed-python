
from libs.QuickMakeZarrPy import QuickMakeZarr


def createZarrData(config):
    """
    创建zarr数据集
    :return:
    """
    QuickMakeZarr(config)


if __name__ == '__main__':
    config = {
        'imgPath': r'E:\imgslice',  # imgPath
        'savePath': r'H:\omeZarr',  # savePath
        'sampleType': 0,  # 0:max 1:mean
        'startEpoch': 0,
        'noUseCpuNumber': 1,  # noUseCpuNumber
        'smallSize': [512, 512, 512]
    }
    createZarrData(config)

