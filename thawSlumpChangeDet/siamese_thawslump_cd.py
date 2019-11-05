#!/usr/bin/env python
# Filename: siamese_thawslump_cd 
"""
introduction: conduct change detection using siamese neural network

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 05 November, 2019
"""

import sys,os
from optparse import OptionParser

import torch
from torch import nn
import torch.nn.functional as F
from torchvision import transforms
from torch import optim
import random

import rasterio
import numpy as np


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
            raise ValueError('error, %s and %s do not have the band counts')
    if len(image_pair) > 2:
        label_path = image_pair[2]
        with rasterio.open(label_path) as src:
            if height != src.height or width != src.width:
                raise ValueError('error, %s and %s do not have the same size')


def read_image():
    pass

class two_images_pixel_pair(torch.utils.data.Dataset):

    def __init__(self, root, changedet_pair_txt, win_size, train=True, transform=None, target_transform=None):
        # super().__init__() need this one?
        '''
        read images for change detections
        :param root: a directory, support ~/
        :param changedet_pair_txt: a txt file store image name in format: old_image_path:new_image_path: label_path(if available)
        :param win_size: window size of the patches, default is 28 by 28, the same as MNIST dataset. (height, width)
        :param train: indicate it is for training
        :param transform: apply training transform to original images
        :param target_transform: apply tarnsform to target images
        '''

        self.root = os.path.expanduser(root)
        self.transform = transform
        self.imgs_path_txt = changedet_pair_txt
        self.win_size = win_size
        self.img_pair_list = [] # image list, each one is (old_image, new_image, label_path)
        self.target_transform = target_transform
        self.train = train  # True for training and validation (also need label), False for prediction

        # for each element: [old_image, new_image, label_path (if available)]
        self.img_pair_list = read_img_pair_paths(self.root, changedet_pair_txt)

        self.pixel_index_pairs = []  # each one: (image_id, row_index, col_index, label) # label for change or no-change

        if self.train:
            # get pairs for training
            for idx, image_pair in enumerate(self.img_pair_list):

                check_image_pairs(image_pair)
                # old_img_path = image_pair[0]  # an old image
                # new_img_path = image_pair[1]  # a new image
                change_map_path = image_pair[2] # label
                with rasterio.open(change_map_path) as src:
                    indexes = src.indexes
                    if len(indexes) != 1:
                        raise ValueError('error, the label should only have one band')
                    label_data = src.read(indexes)
                    height, width = label_data.shape
                    for row in range(height):
                        for col in range(width):
                            self.pixel_index_pairs.append((idx, row, col, label_data[row, col]))

                #TODO: remove some no-change pixel because the number of them is too large

            pass
        else:
            # read all pixels, and be ready for testing
            for idx, image_pair in enumerate(self.img_pair_list):

                check_image_pairs(image_pair)
                old_img_path = image_pair[0]  # an old image
                # new_img_path = image_pair[1]  # a new image
                # change_map_path = image_pair[2] # label
                with rasterio.open(old_img_path) as src:
                    label_data = src.read([1]) # read the first band
                    height, width = label_data.shape
                    for row in range(height):
                        for col in range(width):
                            self.pixel_index_pairs.append((idx, row, col, None))   #label_data[row, col]

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

        new_image = np.zeros((self.win_size[0],self.win_size[1],image_array.shape[2]),
                             dtype=image_array.dtype)

        new_image[0:image_array.shape[0], 0:image_array.shape[1],:] = image_array

        return new_image

    def __getitem__(self, index):

        # read old and new image, as well as label
        pair_id, row_index, col_index, label = self.pixel_index_pairs[index]
        old_img_path, new_img_path = self.img_pair_list[pair_id][:2]

        # read old image
        with rasterio.open(old_img_path) as old_src:
            indexes = old_src.indexes
            height = old_src.height
            width = old_src.width

            window  = self._get_window(row_index, col_index, width, height)
            old_img_patch = old_src.read(indexes, window=window)

            ####################################################
            # then, red a patch in new image
            with rasterio.open(new_img_path) as new_src:
                new_img_patch = new_src.read(indexes, window=window)

        # crop and padding to win_size
        old_patch = self._crop_padding(old_img_patch)
        new_patch = self._crop_padding(new_img_patch)

        if self.train:
            return old_patch, new_patch, label

        else:
            # only read old and new image, no label (None)
            return old_patch, new_patch


    def __len__(self):
        return len(self.pixel_index_pairs)




# modified network define from
# https://becominghuman.ai/siamese-networks-algorithm-applications-and-pytorch-implementation-4ffa3304c18
class Net(nn.Module):
    def __init__(self):
        super().__init__()

        self.conv1 = nn.Conv2d(1, 64, 7)        #input is 1 channel, 28 by 28 (MNIST), output height by width 22 by 22
        self.pool1 = nn.MaxPool2d(2)            # output height by : 11 by 11
        self.conv2 = nn.Conv2d(64, 128, 5)      # output height by : 7 by 7
        self.conv3 = nn.Conv2d(128, 256, 5)     # output height by : 3 by 3, therefore, 2304 =  256*3*3
        self.linear1 = nn.Linear(2304, 512)

        self.linear2 = nn.Linear(512, 2)

    def forward(self, data):
        res = []
        for i in range(2):  # Siamese nets; sharing weights
            x = data[i]
            x = self.conv1(x)
            x = F.relu(x)
            x = self.pool1(x)
            x = self.conv2(x)
            x = F.relu(x)
            x = self.conv3(x)
            x = F.relu(x)

            x = x.view(x.shape[0], -1)
            x = self.linear1(x)
            res.append(F.relu(x))

        # The crucial step of the whole procedure is the next one:
        # we calculate the squared distance of the feature vectors.
        # In principle, to train the network, we could use the triplet loss with the outputs
        # of this squared differences. However, I obtained better results
        # (faster convergence) using binary cross entropy loss. Therefore,
        # we attach one more linear layer with 2 output features (equal number,
        # different number) to the network to obtain the logits.

        res = torch.abs(res[1] - res[0])
        res = self.linear2(res)
        return res


def train(model, device, train_loader, epoch, optimizer, batch_size):
    model.train()

    for batch_idx, (data, target) in enumerate(train_loader):
        for i in range(len(data)):
            data[i] = data[i].to(device)

        optimizer.zero_grad()
        output_positive = model(data[:2])
        output_negative = model(data[0:3:2])

        target = target.type(torch.LongTensor).to(device)
        target_positive = torch.squeeze(target[:, 0])
        target_negative = torch.squeeze(target[:, 1])

        loss_positive = F.cross_entropy(output_positive, target_positive)
        loss_negative = F.cross_entropy(output_negative, target_negative)

        loss = loss_positive + loss_negative
        loss.backward()

        optimizer.step()
        if batch_idx % 10 == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * batch_size, len(train_loader.dataset),
                       100. * batch_idx * batch_size / len(train_loader.dataset),
                loss.item()))


def test(model, device, test_loader):
    model.eval()

    with torch.no_grad():
        accurate_labels = 0
        all_labels = 0
        loss = 0
        for batch_idx, (data, target) in enumerate(test_loader):
            for i in range(len(data)):
                data[i] = data[i].to(device)

            output_positive = model(data[:2])
            output_negative = model(data[0:3:2])

            target = target.type(torch.LongTensor).to(device)
            target_positive = torch.squeeze(target[:, 0])
            target_negative = torch.squeeze(target[:, 1])

            loss_positive = F.cross_entropy(output_positive, target_positive)
            loss_negative = F.cross_entropy(output_negative, target_negative)

            loss = loss + loss_positive + loss_negative

            accurate_labels_positive = torch.sum(torch.argmax(output_positive, dim=1) == target_positive).cpu()
            accurate_labels_negative = torch.sum(torch.argmax(output_negative, dim=1) == target_negative).cpu()

            accurate_labels = accurate_labels + accurate_labels_positive + accurate_labels_negative
            all_labels = all_labels + len(target_positive) + len(target_negative)

        accuracy = 100. * accurate_labels / all_labels
        print('Test accuracy: {}/{} ({:.3f}%)\tLoss: {:.6f}'.format(accurate_labels, all_labels, accuracy, loss))


def oneshot(model, device, data):
    model.eval()

    with torch.no_grad():
        for i in range(len(data)):
            data[i] = data[i].to(device)

        output = model(data)
        return torch.squeeze(torch.argmax(output, dim=1)).cpu().item()


def main(options, args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    normalize = transforms.Normalize((128,128, 128), (128, 128, 128)) # mean, std # for 3 band images with 0-255 grey
    trans = transforms.Compose([transforms.ToTensor(), normalize])

    data_root = args[0]
    image_paths_txt = args[1]

    model = Net().to(device)

    do_learn = options.train
    batch_size = options.batch_size
    lr = options.learning_rate
    weight_decay = options.weight_decay
    num_epochs = options.num_epochs
    save_frequency = options.save_frequency


    if do_learn:  # training mode
        train_loader = torch.utils.data.DataLoader(
            two_images_pixel_pair(data_root, image_paths_txt, train=True, transform=trans),
            batch_size=batch_size, shuffle=True)

        test_loader = torch.utils.data.DataLoader(
            two_images_pixel_pair(data_root, image_paths_txt, train=False, transform=trans),
            batch_size=batch_size, shuffle=False)

        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
        for epoch in range(num_epochs):
            train(model, device, train_loader, epoch, optimizer)
            test(model, device, test_loader)
            if epoch & save_frequency == 0:
                # torch.save(model, 'siamese_{:03}.pt'.format(epoch))             # save the entire model
                torch.save(model.state_dict(),
                           'siamese_{:03}.pt'.format(epoch))  # save only the state dict, i.e. the weight
    else:  # prediction
        prediction_loader = torch.utils.data.DataLoader(
            two_images_pixel_pair(data_root, image_paths_txt, train=False, transform=trans), batch_size=1, shuffle=True)

        model.load_state_dict(torch.load(load_model_path))
        data = []
        data.extend(next(iter(prediction_loader))[0][:3:2])
        target = []
        target.extend(next(iter(prediction_loader))[1][:3:2])
        for i in range(random.randint(1, 100)):
            print(i)
            print(next(iter(prediction_loader))[1])
            # data = next(iter(prediction_loader))[0][:3:2]
            # target = next(iter(prediction_loader))[1][:3:2]
            # print(data)
            # print(target)
        same = oneshot(model, device, data)
        if same > 0:
            print('These two images are of the same number')
        else:
            print('These two images are not of the same number')



if __name__ == "__main__":
    usage = "usage: %prog [options] root_dir images_paths_txt"
    parser = OptionParser(usage=usage, version="1.0 2019-11-05")
    parser.description = 'Introduction: conduct change detection using siamese neural network '

    parser.add_option("-t", "--dotrain",
                      action="store_true", dest="dotrain", default=False,
                      help="set this flag for training")

    parser.add_option("-b", "--batch_size", type=int, default=32,
                      action="store", dest="batch_size",
                      help="the batch size")

    parser.add_option('-l', '--learning_rate', type = float, default = 0.001,
                      action="store", dest='learning_rate',
                      help='the learning rate for training')

    parser.add_option('-w', '--weight_decay', type = float, default = 0.0001,
                      action="store", dest='weight_decay',
                      help='the weight decay for training')

    parser.add_option('-e', '--num_epochs', type = int, default = 20,
                      action="store", dest='num_epochs',
                      help='the number of epochs for training')

    parser.add_option('-s', '--save_frequency', type = int, default = 5,
                      action="store", dest = 'save_frequency',
                      help='the frequency for saving traned model')

    # parser.add_option("-p", "--para",

    #                   action="store", dest="para_file",
    #                   help="the parameters file")

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    ## set parameters files
    # if options.para_file is None:
    #     print('error, no parameters file')
    #     parser.print_help()
    #     sys.exit(2)
    # else:
    #     parameters.set_saved_parafile_path(options.para_file)

    main(options, args)
