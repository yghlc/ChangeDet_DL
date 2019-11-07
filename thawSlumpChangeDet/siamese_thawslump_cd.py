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

from dataTools.img_pairs import two_images_pixel_pair

class ToTensor(object):
    """Convert ndarrays read by rasterio to Tensors."""

    def __call__(self, image):
        # swap color axis because
        # rasterio numpy image: C X H X W
        # torch image: C X H X W
        # image = image.transpose((2, 0, 1))
        return torch.from_numpy(image).float() # from Byte to float

# modified network define from
# https://becominghuman.ai/siamese-networks-algorithm-applications-and-pytorch-implementation-4ffa3304c18
class Net(nn.Module):
    def __init__(self):
        super().__init__()

        self.conv1 = nn.Conv2d(3, 64, 7)        #input is 3 channel, 28 by 28 (MNIST), output height by width 22 by 22
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
    total_loss = 0
    iter_count = 0
    for batch_idx, (data, target) in enumerate(train_loader):
        for i in range(len(data)):
            data[i] = data[i].to(device)

        optimizer.zero_grad()
        out_target = model(data[:2])

        # target = target.type(torch.LongTensor).to(device)
        # label_target = torch.squeeze(target)
        label_target = target.type(torch.LongTensor).to(device)
        label_target = torch.squeeze(label_target)

        # https://pytorch.org/docs/stable/nn.html#torch.nn.CrossEntropyLoss
        loss = F.cross_entropy(out_target, label_target)

        loss.backward()

        optimizer.step()
        if batch_idx % 10 == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * batch_size, len(train_loader.dataset),
                       100. * batch_idx * batch_size / len(train_loader.dataset),
                loss.item()))

        total_loss += loss.item()
        iter_count += 1
    return total_loss/iter_count

def test(model, device, test_loader):
    model.eval()
    with torch.no_grad():
        accurate_labels = 0
        all_labels = 0
        loss = 0
        for batch_idx, (data, target) in enumerate(test_loader):
            for i in range(len(data)):
                data[i] = data[i].to(device)

            output_target = model(data[:2])

            label_target = target.type(torch.LongTensor).to(device)
            label_target = torch.squeeze(label_target)

            # https://pytorch.org/docs/stable/nn.html#torch.nn.CrossEntropyLoss
            loss = F.cross_entropy(output_target, label_target)

            loss_test = F.cross_entropy(output_target, label_target)

            loss = loss + loss_test

            accurate_labels_pre = torch.sum(torch.argmax(output_target, dim=1) == label_target).cpu()


            accurate_labels = accurate_labels + accurate_labels_pre
            all_labels = all_labels + len(label_target)

        accuracy = 100. * accurate_labels / all_labels
        print('Test accuracy: {}/{} ({:.3f}%)\tLoss: {:.6f}'.format(accurate_labels, all_labels, accuracy, loss))
        return accuracy, loss


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
    trans = transforms.Compose([ToTensor(), normalize])

    data_root = os.path.expanduser(args[0])
    image_paths_txt = os.path.expanduser(args[1])

    model = Net().to(device)   #Net().double().to(device)
    # print(model)

    do_learn = options.dotrain
    batch_size = options.batch_size
    lr = options.learning_rate
    weight_decay = options.weight_decay
    num_epochs = options.num_epochs
    save_frequency = options.save_frequency
    num_workers = options.num_workers

    train_loss_list = []
    evl_loss_list = []
    evl_acc_list = []

    if do_learn:  # training mode
        train_loader = torch.utils.data.DataLoader(
            two_images_pixel_pair(data_root, image_paths_txt, (28,28), train=True, transform=trans),
            batch_size=batch_size, num_workers=num_workers,  shuffle=True)

        test_loader = torch.utils.data.DataLoader(
            two_images_pixel_pair(data_root, image_paths_txt, (28,28), train=True, transform=trans),
            batch_size=batch_size, num_workers=num_workers, shuffle=False)

        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
        for epoch in range(num_epochs):
            t_loss = train(model, device, train_loader, epoch, optimizer,batch_size)
            eval_acc, eval_loss =  test(model, device, test_loader)

            train_loss_list.append(t_loss)
            evl_loss_list.append(eval_acc)
            evl_acc_list.append(eval_loss)

            if epoch % save_frequency == 0:
                # torch.save(model, 'siamese_{:03}.pt'.format(epoch))             # save the entire model
                torch.save(model.state_dict(),
                           'siamese_{:03}.pt'.format(epoch))  # save only the state dict, i.e. the weight
    else:  # prediction
        prediction_loader = torch.utils.data.DataLoader(
            two_images_pixel_pair(data_root, image_paths_txt, (28,28), train=False, transform=trans),
            batch_size=batch_size, num_workers=num_workers, shuffle=False)

        # loading data
        for batch_idx, (data, _) in enumerate(prediction_loader):
            for i in range(len(data)):
                data[i] = data[i].to(device)

            out_target = model(data[:2])



        # loading model
        load_model_path = 'siamese_017.pt'
        model.load_state_dict(torch.load(load_model_path))

        same = oneshot(model, device, data)
        if same > 0:
            print('These two pixels the same')
        else:
            print('These two pixels are not the same')



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

    parser.add_option('-n', '--num_workers', type = int, default = 4,
                      action="store", dest='num_workers',
                      help='the number of workers for loading images')

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