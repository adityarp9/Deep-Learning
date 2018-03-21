""" 
Flip the given data (training)
Return appended (augmented dataset)
"""
from __future__ import print_function
import torch
import numpy as np
import copy
from matplotlib.pyplot import imshow, show


class TransformData:

    def __init__(self, orig_dataset, transform, times=1):
        self.transform = transform
        if transform == 'flipLR':
            self.data = self.flipLR(orig_dataset)
        if transform == 'flipUD':
            self.data = self.flipUD(orig_dataset)
        if transform == 'crop':
            self.data = self.crop(orig_dataset)
        if transform == 'rotate90':
            self.data = self.rotate90(orig_dataset, times)

    @staticmethod
    def flipLR(orig_dataset):
        """ Flips horizontally """
        data_aug = copy.deepcopy(orig_dataset)
        data_aug.data = orig_dataset.data[:]
        print("Flipping training examples horizontally ...", end=" ")
        for image, label in orig_dataset.data:
            t_image = np.flip(image.numpy(), 2)
            t_image = torch.from_numpy(t_image.copy()).type(torch.FloatTensor)
            data_aug.data.append((t_image, label))
        print("done.")
        return data_aug.data

    @staticmethod
    def flipUD(orig_dataset):
        """ Flips upside-down """
        data_aug = copy.deepcopy(orig_dataset)
        data_aug.data = orig_dataset.data[:]
        print("Flipping training examples upside down ...", end=" ")
        for image, label in orig_dataset.data:
            # For 3 channels np.fliplr works as 
            # putting the image as upside down
            t_image = np.fliplr(image.numpy())
            t_image = torch.from_numpy(t_image.copy()).type(torch.FloatTensor)
            data_aug.data.append((t_image, label))
        print("done.")
        return data_aug.data

    @staticmethod
    def crop(orig_dataset):
        """ Crop 1 pixel boundary of image """
        data_aug = copy.deepcopy(orig_dataset)
        data_aug.data = orig_dataset.data[:]
        print("Cropping training examples ...", end=" ")
        for image, label in orig_dataset.data:
            image[:, 0] = image[0, :] = image[:, -1] = image[-1, :] = 0
            data_aug.data.append((image, label))
        print("done.")
        return data_aug.data

    @staticmethod
    def rotate90(orig_dataset, times=1):
        """ Rotate image anti/clockwise by 90*times """
        data_aug = copy.deepcopy(orig_dataset)
        data_aug.data = orig_dataset.data[:]
        print("Rotating images by %d degrees ..." % 90 * times, end=" ")
        for image, label in orig_dataset.data:
            t_image = np.rot90(image.numpy(), k=1, axes=(1, 2))
            t_image = torch.from_numpy(t_image.copy()).type(torch.FloatTensor)
            data_aug.data.append((t_image, label))
        print("done.")
        return data_aug.data

def see(image):
    """ Use the vision """
    image = image.cpu()
    image = image.numpy().reshape(3, 32, 32).transpose(1, 2, 0).astype("uint8")
    imshow(image)
    show()
