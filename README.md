# Ome-Zarr-Speed-python
This is the Python interface for ome-zarr's rapid big data production. This interface can directly call the big data production program with Python and is also easy to extend to other languages for calling the ome-zarr rapid big data production program.

## Program entry
[ZarrMaker.py](https://github.com/Quanlab-Bioimage/Ome-Zarr-Speed-python/tree/main/ZarrCreator)

## Program call mode
```
config = {
        'imgPath': r'E:\imgslice',  # imgPath
        'savePath': r'H:\omeZarr',  # savePath
        'sampleType': 0,  # 0:max 1:mean
        'startEpoch': 0,
        'noUseCpuNumber': 1,  # noUseCpuNumber
        'smallSize': [512, 512, 512]
    }
```
## Install
```
pip install psutil
pip install pillow
```

## Test data
https://zenodo.org/record/8385040


## Parameter description

* imgPath: indicates the folder path of the image sequence.
* savePath: indicates the path of the data saving folder.
* sampleType: Sampling mode. 0: maximum sampling, 1: average sampling.
* startEpoch: Start round, starting from 0, used to continue production from the specified round after an abnormal interruption.
* noUseCpuNumber: Number of cpu cores retained.
* smallSize: Small block size, [x,y,z].
