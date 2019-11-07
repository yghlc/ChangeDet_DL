#!/usr/bin/env python
# Filename: img_pairs 
"""
introduction: read pixels for pytorch Dataloader

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 07 November, 2019
"""

import rasterio
import os

import torch
import numpy as np
import random

def read_img_pair_paths(dir, imgs_path_txt):
    '''
    get path list for image pair
    :param dir:
    :param imgs_path_txt:
    :return:
    '''
    img_pair_path = []
    dir = os.path.expanduser(dir)
    with open(imgs_path_txt) as f_obj:
        lines = f_obj.readlines()
        for str_line in lines:
            #path_str [old_image, new_image, label_path (if available)]
            path_str = [os.path.join(dir, item.strip()) for item in str_line.split(':')]
            img_pair_path.append(path_str)

    return img_pair_path

def check_image_pairs(image_pair):
    '''
    check image pair for change detections
    :param image_pair:
    :return:
    '''
    # these images should have the same width and height.
    old_img_path = image_pair[0]  # an old image
    new_img_path = image_pair[1]  # a new image

    with rasterio.open(old_img_path) as src:
        height = src.height
        width = src.width
        band_count = src.count

    with rasterio.open(new_img_path) as src:
        if height != src.height or width != src.width:
            raise ValueError('error, %s and %s do not have the same size')
        if band_count != src.count:
            raise ValueError('error, %s and %s do not have the same band count')
    if len(image_pair) > 2:
        label_path = image_pair[2]
        with rasterio.open(label_path) as src:
            if height != src.height or width != src.width:
                raise ValueError('error, %s and %s do not have the same size')

def read_image_to_array(img_path):
    # read  image
    with rasterio.open(img_path) as src:
        indexes = src.indexes
        # height = old_src.height
        # width = old_src.width
        image_array = src.read(indexes)  # shape (ncount, height, width)
        return image_array

def save_image_oneband_8bit(ref_image_path,img_data,save_path):
    """
    save image: oneband with 8bit
    :param ref_image: the image, have the same extent
    :param img_data: numpy array of a new image, could be one band or multi band
    :param save_path: Save file path
    :return: True if sucessufully, False otherwise
    """
    # reference image path
    with rasterio.open(ref_image_path) as src:
        profile = src.profile
        profile.update(dtype=rasterio.uint8, count=1)
        with rasterio.open(save_path, "w", **profile) as dst:
            dst.write(img_data, 1)
    return True

def get_image_height_width(image_path):
    with rasterio.open(image_path) as src:
        return src.height, src.width

class two_images_pixel_pair(torch.utils.data.Dataset):

    def __init__(self, root, changedet_pair_txt, win_size, train=True, transform=None, target_transform=None, predict_pair_id=0):
        # super().__init__() need this one?
        '''
        read images for change detections
        :param root: a directory, support ~/
        :param changedet_pair_txt: a txt file store image name in format: old_image_path:new_image_path: label_path(if available)
        :param win_size: window size of the patches, default is 28 by 28, the same as MNIST dataset. (height, width)
        :param train: indicate it is for training
        :param transform: apply training transform to original images
        :param target_transform: apply tarnsform to target images
        :param predict_pair_id: the pair for predicting (prediction only load data from one pair)
        '''

        self.root = os.path.expanduser(root)
        self.transform = transform
        self.imgs_path_txt = changedet_pair_txt
        self.win_size = win_size
        self.img_pair_list = []         # image list, each one is (old_image, new_image, label_path)
        self.img_array_pair_list = []   # image array list, each one is (old_image array, new_image array, label array)
        self.target_transform = target_transform
        self.train = train  # True for training and validation (also need label), False for prediction

        # for each element: [old_image, new_image, label_path (if available)]
        self.img_pair_list = read_img_pair_paths(self.root, changedet_pair_txt)

        self.pixel_index_pairs = []  # each one: (image_id, row_index, col_index, label) # label for change or no-change


        if self.train:
            no_change_idx = []
            change_idx = []
            idx = 0
            # get pairs for training
            for pair_id, image_pair in enumerate(self.img_pair_list):

                check_image_pairs(image_pair)
                old_img_path = image_pair[0]  # an old image
                new_img_path = image_pair[1]  # a new image
                change_map_path = image_pair[2] # label

                # read image to memory
                old_image_array = read_image_to_array(old_img_path)
                new_image_array = read_image_to_array(new_img_path)
                change_map_array = read_image_to_array(change_map_path)

                if change_map_array.shape[0] != 1:
                    raise ValueError('error, the label should only have one band')
                self.img_array_pair_list.append([old_image_array, new_image_array, change_map_array])

                label_data = np.squeeze(change_map_array)
                height, width = label_data.shape # nband, height, width
                for row in range(height):
                    for col in range(width):
                        self.pixel_index_pairs.append((pair_id, row, col, label_data[row, col]))
                        if label_data[row, col] == 2:       # change pixel
                            change_idx.append(idx)
                        elif label_data[row, col] == 1:     # no-change pixel
                            no_change_idx.append(idx)
                        else:
                            raise ValueError('Error: unknow label: %d at row: %d, col: %d'
                                             %(label_data[row, col],row, col))
                        idx += 1

            #remove some no-change pixel because the number of them is too large
            # or maybe we manually selected some non-change areas
            if len(no_change_idx) > len(change_idx)*3:
                keep_count = len(change_idx)*3
                keep_idx_list = random.sample(range(len(no_change_idx)), keep_count)

                keep_pixel_index_pairs = [self.pixel_index_pairs[item] for item in change_idx]
                keep_pixel_index_pairs.extend([self.pixel_index_pairs[no_change_idx[keep_idx]] for keep_idx in keep_idx_list ])
                self.pixel_index_pairs = keep_pixel_index_pairs

            pass
        else:
            # read all pixels, and be ready for prediction
            image_pair = self.img_pair_list[predict_pair_id]
            # for pair_id, image_pair in enumerate(self.img_pair_list):

            check_image_pairs(image_pair)
            old_img_path = image_pair[0]  # an old image
            new_img_path = image_pair[1]  # a new image

            # read image to memory
            old_image_array = read_image_to_array(old_img_path)
            new_image_array = read_image_to_array(new_img_path)

            self.img_array_pair_list.append([old_image_array, new_image_array])

            ncount, height, width = old_image_array.shape
            for row in range(height):
                for col in range(width):
                    self.pixel_index_pairs.append((predict_pair_id, row, col, None))   #label_data[row, col]

            pass

    def _get_window(self, row_index, col_index, width, height):
        # set window (row_start, row_stop), (col_start, col_stop)
        row_start = row_index - self.win_size[0] / 2  # win_size: (height, width)
        row_stop = row_index + self.win_size[0] / 2
        col_start = col_index - self.win_size[1] / 2
        col_stop = col_index + self.win_size[1] / 2

        if row_start < 0: row_start = 0
        if row_stop > height: row_stop = height
        if col_start < 0: col_start = 0
        if col_stop > width: col_stop = width

        window = ((row_start, row_stop), (col_start, col_stop))
        return window

    def _crop_padding(self, image_array):

        new_image = np.zeros((image_array.shape[0], self.win_size[0],self.win_size[1]),
                             dtype=image_array.dtype)

        new_image[:, 0:image_array.shape[1], 0:image_array.shape[2]] = image_array

        return new_image

    def _get_sub_image(self,row_index, col_index, image_array):
        '''
        get a subset from a image array, padding if the window be is out of the image
        :param row_index:
        :param col_index:
        :param image_array:
        :return:
        '''
        nband, height,width = image_array.shape

        # set window (row_start, row_stop), (col_start, col_stop)
        row_start = row_index - int(self.win_size[0] / 2)  # win_size: (height, width)
        row_stop = row_index + int(self.win_size[0] / 2)
        col_start = col_index - int(self.win_size[1] / 2)
        col_stop = col_index + int(self.win_size[1] / 2)

        # adjust the boundary
        adj_row_start = 0 if row_start < 0 else row_start
        adj_row_stop = height if row_stop > height else row_stop
        adj_col_start = 0 if col_start < 0 else  col_start
        adj_col_stop = width if col_stop > width else col_stop

        if (adj_row_stop - adj_row_start ) != self.win_size[0] or (adj_col_stop - adj_col_start ) != self.win_size[1]:
            new_image = np.zeros((image_array.shape[0], self.win_size[0], self.win_size[1]),
                                 dtype=image_array.dtype)

            new_image[:, (adj_row_start-row_start):(self.win_size[0]-(row_stop-adj_row_stop)),
            (adj_col_start - col_start):(self.win_size[1] - (col_stop - adj_col_stop))] = \
                image_array[:, adj_row_start:adj_row_stop, adj_col_start: adj_col_stop]

        else:
            new_image = image_array[:, row_start:row_stop, col_start: col_stop]
        # print(new_image.shape)
        # if new_image.shape != (3,28,28):
        #     raise ValueError('error, it is not (3,28,28)')
        return new_image

    def __getitem__(self, index):

        # read old and new image, as well as label
        pair_id, row_index, col_index, label = self.pixel_index_pairs[index]
        # old_img_path, new_img_path = self.img_pair_list[pair_id][:2]
        if self.train:
            old_img_array, new_img_array = self.img_array_pair_list[pair_id][:2]
        else:
            old_img_array, new_img_array = self.img_array_pair_list[0][:2]      # for prediction, only read one pair

        # # read old image
        # with rasterio.open(old_img_path) as old_src:       # every pixel, read image from disk is very time consuming
        #     indexes = old_src.indexes
        #     height = old_src.height
        #     width = old_src.width
        #
        #     window  = self._get_window(row_index, col_index, width, height)
        #     old_img_patch = old_src.read(indexes, window=window)    # shape (ncount, height, width)
        #
        #     ####################################################
        #     # then, red a patch in new image
        #     with rasterio.open(new_img_path) as new_src:
        #         new_img_patch = new_src.read(indexes, window=window)

        # # crop and padding to win_size
        # if old_img_patch.shape[1] != self.win_size[0] or old_img_patch.shape[2] != self.win_size[1]:
        #     old_img_patch = self._crop_padding(old_img_patch)
        #     new_img_patch = self._crop_padding(new_img_patch)

        # ncount, height, width = old_img_array.shape
        old_img_patch = self._get_sub_image(row_index,col_index,old_img_array)
        new_img_patch = self._get_sub_image(row_index,col_index,new_img_array)

        if self.transform is not None:
            old_img_patch = self.transform(old_img_patch)
            new_img_patch = self.transform(new_img_patch)

        if label == 1: # no change
            label_target = torch.tensor([0])    #torch.tensor([1, 0])
        elif label == 2:   # change
            label_target = torch.tensor([1])    #torch.tensor([0, 1])
        else:
            label_target = None

        # return [old_img_patch, new_img_patch], label_target
        if self.train:
            return [old_img_patch, new_img_patch], label_target

        else:
            # only read old and new image, no label (None)
            return [old_img_patch, new_img_patch], [pair_id, row_index, col_index]


    def __len__(self):
        return len(self.pixel_index_pairs)



if __name__ == "__main__":
    pass