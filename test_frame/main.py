from __future__ import print_function

import torch

import cutorch.nn as nn
import cutorch.nn.functionals as f
import cutorch.datasets as dsets
import cutorch.vision.transforms as vision


__dlevel__ = 0


class FCM(nn.Module):

    def __init__(self):
        super(FCM, self).__init__()

        self.fc = nn.Sequential(
            nn.Linear(32 * 32 * 3, 2048),
            nn.ReLU(),
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Linear(512, 10),
            nn.Softmax()
        )

        self.fc.see_modules()

    def forward(self, inputs):
        if __debug__:
            if __dlevel__ == 2:
                print("Input:{}".format(inputs))
                
        # Standardize
        inputs = f.standardize(inputs)

        # Fprop
        out = self.fc(inputs)
        #out = self.layer2(out)

        if __debug__:
            if __dlevel__ == 1:
                print("Output:{}".format(out))
            if __dlevel__ == 2:
                pass
            if __dlevel__ == 3:
                print("Stdized input:{}".format(inputs))
            if __dlevel__ == 4:
                print(self.fc['module', 0])
                print(self.fc['parameters', 0])
        return out


def main():

    # Get train data for training and cross validation
    train_dataset = dsets.CIFAR10(directory='cutorch/data',
                                 download=True,
                                 train=True)
    # Data augmentation
    # train_dataset = vision.Transforms(dataset=train_dataset,
    #                           lr_flip=True)

    # Get validation data
    # val_dataset = dsets.CIFAR10(directory='cutorch/data',
    #                            download=True,
    #                            test=True)

    train_loader = dsets.data_loader(data=train_dataset.data,
                                    batch_size=1,
                                    shuffled=True)

    # Fully connected layer model
    model = FCM()
    criterion = nn.CrossEntropyLoss()

    for images, ground_truths in train_loader[0:1]:
        # Apply the n/w on the image
        outputs = model(images)
        loss = criterion(outputs, ground_truths)
        print(loss)

if __name__ == '__main__':
    main()
