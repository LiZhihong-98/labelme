"""
Descripttion: 
Author: Zhihong Li
version: 
Date: 2024-07-31 14:46:32
LastEditors: Zhihong Li
LastEditTime: 2024-08-07 23:54:22
"""

from osgeo import gdal
import os


def clip_image(
    input_file, output_prefix, block_width, block_height, overlap_percentage
):
    if not os.path.exists(output_prefix):
        os.makedirs(output_prefix)
    in_ds = gdal.Open(input_file)
    width = in_ds.RasterXSize
    height = in_ds.RasterYSize
    num_bands = in_ds.RasterCount
    num = 0

    overlap_width = int(block_width * overlap_percentage / 100)
    overlap_height = int(block_height * overlap_percentage / 100)

    num_cols = width // (block_width - overlap_width)
    num_rows = height // (block_height - overlap_height)

    for i in range(num_cols):
        for j in range(num_rows):

            offset_x = i * (block_width - overlap_width)
            offset_y = j * (block_height - overlap_height)

            out_filename = output_prefix + f"./{num:04d}.tiff"

            gdal.Translate(
                out_filename,
                in_ds,
                srcWin=[offset_x, offset_y, block_width, block_height],
            )
            num += 1

    in_ds = None
