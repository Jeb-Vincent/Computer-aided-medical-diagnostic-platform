# -*- coding: utf-8 -*-

import os
from PIL import Image

def split_image_horizontally(image_path, target_dirs):
    with Image.open(image_path) as img:
        width, height = img.size
        # 计算每部分的宽度
        part_width = width // 3

        # 分割并保存每一部分
        for i in range(3):
            left = i * part_width
            right = (i + 1) * part_width if i != 2 else width
            part_img = img.crop((left, 0, right, height))
            part_img.save(os.path.join(target_dirs[i], os.path.basename(image_path)))

def main(source_dir, target_base_dir):
    # 创建保存分割图片的三个目录
    target_dirs = [os.path.join(target_base_dir, f'part_{i+1}') for i in range(3)]
    for dir in target_dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
    
    # 遍历原始图片文件夹
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(source_dir, filename)
            # 分割图片并保存到三个不同的文件夹中
            split_image_horizontally(image_path, target_dirs)

# 指定源图片文件夹和目标文件夹基路径
source_dir = '/home/ubuntu/js/SaveTestImage/trip-ce-ssimG_rate1/100datasettime1/a2b/200/'
target_base_dir = '/home/ubuntu/js/split_image3/'

if __name__ == '__main__':
    main(source_dir, target_base_dir)
