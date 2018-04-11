"""
Activations class
1. ReLU
"""

from __future__ import print_function

from collections import OrderedDict

import torch

from .module import Module
from .. import functionals as f

__dlevel__ = 0


class ReLU(Module):
    """ReLU Activation layer class"""

    def __init__(self):
        super(ReLU, self).__init__()
        self.idx = 0
        self.inputs = 0
        self.output = 0
        self.grad = OrderedDict()
        self.grad['output'] = 0

    def forward(self, in_features):
        self.inputs = in_features
        self.output = f.relu(in_features)
        if __debug__:
            if __dlevel__ == 4:
                print(self.output)
        return self.output

    def backward(self, gradients):
        """
        :param gradients: gradients from the last 
                          back-propagated layer
        """
        self.grad['output'] = f.gradient_relu(self.output, gradients['output'])
        return self.grad


class Softmax(Module):
    """
    Classifier
    Softmax class
    """

    def __init__(self):
        super(Softmax, self).__init__()
        self.idx = 0
        self.inputs = 0
        self.output = 0
        self.confidence = 0
        self.prediction = 0
        self.grad = OrderedDict()

    def forward(self, in_features):
        # Compute softmax probabilities
        self.inputs = in_features
        self.output = f.softmax(in_features)
        if self.is_train:
            return self.output
        elif self.is_eval:
            return self.predict()

    def backward(self, targets):
        # Gradient of softmax outputs @ fprop
        self.grad['output'] = f.gradient_softmax(self.output, targets)
        return self.grad

    def predict(self):
        # Return predictions in evaluation mode
        self.confidence, self.predicted = torch.max(self.output, 1)
        return (self.confidence, self.predicted)