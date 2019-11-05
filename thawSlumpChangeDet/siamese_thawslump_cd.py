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


class two_images_pixel_Pair(torch.utils.data.Dataset):

    def __init__(self, root, train=True, transform=None, target_transform=None, download=False):
        # need super?

        pass

    def __getitem__(self, index):
        pass

    def __len__(self):
        pass




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


def main(options, args):


    pass


if __name__ == "__main__":
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage, version="1.0 2019-11-05")
    parser.description = 'Introduction: conduct change detection using siamese neural network '

    parser.add_option("-o", "--output",
                      action="store", dest="output",
                      help="the output file path")

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
