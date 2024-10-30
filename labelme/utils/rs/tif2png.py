"""
Descripttion: 
Author: Zhihong Li
version: 
Date: 2024-07-26 16:43:19
LastEditors: Zhihong Li
LastEditTime: 2024-07-29 13:53:10
"""

import numpy as np
import os
from PIL import Image
from osgeo import gdal

# Stop GDAL printing both warnings and errors to STDERR
gdal.PushErrorHandler("CPLQuietErrorHandler")

# Make GDAL raise python exceptions for errors (warnings won't raise an exception)
gdal.UseExceptions()


def readTif(imgPath, bandsOrder=[3, 2, 1]):
    dataset = gdal.Open(imgPath, gdal.GA_ReadOnly)  # 返回一个gdal.Dataset类型的对象
    cols = dataset.RasterXSize  # tif图像的宽度
    rows = dataset.RasterYSize  # tif图像的高度
    data = np.empty([rows, cols, 3], dtype=float)  # 定义结果数组，将RGB三波段的矩阵存储

    for i in range(3):
        band = dataset.GetRasterBand(bandsOrder[i])  # 读取波段数值
        oneband_data = band.ReadAsArray()  # 读取波段数值读为numpy数组
        # print(oneband_data)
        data[:, :, i] = oneband_data  # 将读取的结果存放在三维数组的一页三

    return data


def getExtremum(original_image):
    extremum = []
    origin_tif = readTif(original_image)
    band_Num = origin_tif.shape[2]  # 数组第三维度的大小，在这里是图像的通道数
    for i in range(band_Num):
        oneband_data = origin_tif[:, :, i]
        # 获取数组oneband_data某个百分比分位上的值
        extremum.append(
            [
                np.percentile(oneband_data, 2),
                np.percentile(oneband_data, 98),
            ]
        )
    return extremum


def stretchImg(imgPath, resultPath, extremum):
    RGB_Array = readTif(imgPath)
    band_Num = RGB_Array.shape[2]  # 数组第三维度的大小，在这里是图像的通道数
    PNG_Array = np.zeros_like(RGB_Array, dtype=np.uint8)
    minValue = 0
    maxValue = 255
    for i in range(band_Num):
        # 获取数组RGB_Array某个百分比分位上的值
        extremum_value = extremum[i]
        temp_value = (
            (RGB_Array[:, :, i] - extremum_value[0])
            * (maxValue - minValue)
            / (extremum_value[1] - extremum_value[0])
        ) + minValue
        temp_value[temp_value < minValue] = minValue
        temp_value[temp_value > maxValue] = maxValue
        PNG_Array[:, :, i] = temp_value

    outputImg = Image.fromarray(np.uint8(PNG_Array))
    outputImg.save(resultPath)


def Batch_Convert_tif_to_png(original_image, imgdir, savedir):
    # 获取文件夹下所有tif文件名称，并存入列表
    file_name_list = os.listdir(imgdir)
    extremum = getExtremum(original_image)

    if not os.path.exists(savedir):
        os.makedirs(savedir)

    for name in file_name_list:
        # 获取图片文件全路径
        img_path = os.path.join(imgdir, name)
        # 获取文件名，不包含扩展名
        filename = os.path.splitext(name)[0]
        savefilename = filename + ".png"
        # 文件存储全路径
        savepath = os.path.join(savedir, savefilename)
        # img_path为tif文件的完全路径
        # savepath为tif文件对应的jpg文件的完全路径
        stretchImg(img_path, savepath, extremum)


# if __name__ == "__main__":
#     imgdir = "./testData/tifTiles/"  # tif文件所在的【文件夹】
#     savedir = "./testData/GPCPNG/"  # 转为png后存储的【文件夹】
#     Batch_Convert_tif_to_jpg(imgdir, savedir)
