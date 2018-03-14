"""
Custom sequential neural network framework

@author: apatgao
"""
# imports for system library
from __future__ import print_function

import math
import pickle
import sys
import torch
from matplotlib.pyplot import ylabel, imshow, plot, show, xlabel
from numpy import nan

# Custom imports
import Dataset as dset
import init_setup as hw


def normalize(data, data_size):
    """ Normalizes the given data with mean and standard deviation """
    data = data.view(data_size, -1)  # flatten
    mean = torch.mean(data, 1, keepdim=True)
    std_deviation = torch.std(data, 1, keepdim=True)  # print mean, std_deviation
    data = data - mean
    data = data / std_deviation
    return data


def batch_norm():
    pass


def save_model(filename, nn_model):
    
    print('\nSaving ...', end=" ")
    f = open(filename, 'wb')
    pickle.dump(nn_model.optimum, f)
    print('model saved as %s' % filename)
    f.close()

def load_model(filename):
    print('\nChecking saved models ...')
    print('\nLoading model from %s ...' % filename)
    t = pickle.load(open(filename, 'rb'))
    i = 0
    nn_model.optimum = t
    nn_model.get_logs()    
    for layer in nn_model.layers:
        if layer.LayerName == 'Linear':
            layer.w = t['Weights'][i]
            layer.b = t['Biases'][i]
            i += 1
    return nn_model


class ModelNN(object):
    """model class encapsulating torche all layers, functions, hyper parameters etc."""

    def __init__(self):
        # Model status
        self.model_fitted = self.model_trained = self.model_tested = self.model_infered = False
        # Model type
        self.model_type = ""
        # Net structure
        self.net, self.layers, self.loss_history = "", [], []
        self.num_layers = 0
        # Parameters
        self.weights, self.biases, self.output, self.loss = [], [], [], 0
        self.grad_weights, self.grad_biases, self.grad_output = [], [], []
        # Hyper parameters
        self.lr_policy = ""
        self.weights_decay = self.epochs = self.lr = self.decay_rate = 1
        self.reg = 1e-3  # regularization strength
        # Results
        self.predictions = self.train_acc = self.test_acc = 0
        self.optimum = {'Fitting tested': self.model_fitted, 'Trained': self.model_trained, 'Tested': self.model_tested, 'Inferenced': self.model_infered, 
                        'Model type': self.model_type, 'Net': self.net, 'Num layers': self.num_layers,'Layer objs': self.layers,  
                        'Weights': 0, 'Biases': 0, 
                        'Max epochs': self.epochs, 'Epoch': 0, 'Learning rate': self.lr, 'L.R. policy': self.lr_policy,
                        'Weights decay': self.weights_decay, 'L.R. decay': self.decay_rate, 'Reg': self.reg,
                        'Loss': float("inf"), 'TrainAcc': self.train_acc, 'TestAcc': self.test_acc}
        # Model status
        self.isTrain = False

    def add(self, layer_obj):
        """ Add layers, activations to the nn architecture """
        self.layers.append(layer_obj)
        if layer_obj.LayerName == 'Linear':
            layer_obj.w *= self.weights_decay
            self.weights.append(layer_obj.w)
            self.biases.append(layer_obj.b)
            self.grad_weights.append(0)
            self.grad_biases.append(0)
        self.output.append(0)
        self.grad_output.append(0)
        self.num_layers += 1

    def show_net(self):
        print('\nNet arch:', end=" ")
        self.net += '{\n'
        for i, l in enumerate(self.layers):
            self.net += str(i) + ': ' + l.LayerName
            if l.LayerName == 'Linear':
                self.net += '(' + str(l.ipt_neurons) + 'x' + str(l.opt_neurons) + ')'
            elif l.LayerName == 'Activation':
                self.net += '(' + l.activation + ')'
            elif l.LayerName == 'Criterion':
                self.net += '(' + l.classifier + ')'
            self.net += '-->\n'
        self.net += '}'
        self.optimum['Net'] += self.net

        print(self.net)

    def train(self, ipt, label):
        """ Fprop and Backprop to train """
        self.isTrain = True
        ipt = normalize(ipt, ipt.size(0))
        #print(type(ipt))
        #print(hw.dtype)
        self.forward(ipt, label)
        self.backward(ipt, label)

    def test(self, ipt, target):
        """ Fprop to test torche model """
        self.isTrain = False
        self.forward(normalize(ipt, ipt.size(0)), target)

    def forward(self, ipt, label):
        """ Fprop for sequential NN layers """
        for lth in range(self.num_layers):
            if lth == 0:  # Input layer
                if self.layers[lth].LayerName == 'Linear':
                    self.output[lth] = self.layers[lth].forward(ipt)
            elif lth < self.num_layers - 1:  # Hidden layers
                if self.layers[lth].LayerName == 'Linear':
                    self.output[lth] = self.layers[lth].forward(self.output[lth - 1])
                elif self.layers[lth].LayerName == 'Activation':
                    if self.layers[lth].activation == 'ReLU':
                        self.output[lth] = self.layers[lth].relu(self.output[lth - 1])
            else:  # Last layer
                if self.isTrain:
                    if self.layers[lth].LayerName == 'Criterion':
                        if self.layers[lth].classifier == 'Softmax':
                            _, _, self.output[lth] = self.layers[lth].softmax(self.output[lth - 1])
                else:
                    if self.layers[lth].LayerName == 'Criterion':
                        self.output[lth], self.predictions, _ = \
                            (self.layers[lth].softmax(self.output[lth - 1]))
                self.cross_entropy_loss(self.output[lth], label)

    def backward(self, ipts, targets):
        """ Backprop for sequential NN layers """
        param = len(self.weights) - 1
        for lth in range(self.num_layers - 1, -1, -1):
            if lth == self.num_layers - 1:  # Last layer
                if self.layers[lth].LayerName == 'Criterion':
                    if self.layers[lth].classifier == 'Softmax':
                        self.grad_output[lth] = self.layers[lth].backward_softmax(self.output[lth], targets)
            elif self.num_layers - 1 > lth > 0:  # Hidden layers
                if self.layers[lth].LayerName == 'Linear':
                    self.grad_weights[param], self.grad_biases[param] = (
                        self.layers[lth].backward(self.output[lth - 1], self.grad_output[lth + 1]))
                    self.grad_output[lth] = \
                        (self.layers[lth].backward(self.weights[param], self.grad_output[lth + 1], 1))
                    param -= 1
                elif self.layers[lth].LayerName == 'Activation':
                    if self.layers[lth].activation == 'ReLU':
                        self.grad_output[lth] = \
                            (self.layers[lth].backward_relu(self.output[lth], self.grad_output[lth + 1]))
            else:
                self.grad_weights[0], self.grad_biases[0] = \
                    (self.layers[0].backward(ipts, self.grad_output[1]))
        self.update_parameters()

    def cross_entropy_loss(self, softmax, targets):
        if self.isTrain:
            correct_log_probs = (-(torch.log(softmax[range(dset.CIFAR10.batch_size), targets])
                                   / torch.log(torch.Tensor([10]).type(hw.dtype))))
            # print correct_log_probs
            self.loss = torch.sum(correct_log_probs) / dset.CIFAR10.batch_size
            weights = self.parameters()
            reg_loss = 0
            for w in weights[0]:
                reg_loss += 0.5 * self.reg * torch.sum(w * w)
            self.loss += reg_loss
        else:
            probs = -(torch.log(softmax) / torch.log(torch.Tensor([10]).type(hw.dtype)))
            self.loss = torch.sum(probs) / dset.CIFAR10.test_size
        if math.isnan(self.loss):
            print('Loss is NaN\nExiting ...\n')
            sys.exit(1)

    def update_parameters(self):
        """ Bias and weight updates """
        for i, (grad_ws, grad_bs) in enumerate(zip(self.grad_weights, self.grad_biases)):
            grad_ws += self.reg * self.weights[i]
            self.weights[i] += (-self.lr * grad_ws)
            self.biases[i] += (-self.lr * grad_bs)

    def parameters(self):
        return [self.weights, self.biases]

    def set_logs(self):
        # Save other model params too
        self.optimum['Model type'], self.optimum['Num layers'], self.optimum['Layer objs'], \
        self.optimum['Max epochs'], self.optimum['L.R. policy'], self.optimum['Weights decay'], \
        self.optimum['L.R. decay'], self.optimum['Reg'] = \
        self.model_type, self.num_layers, self.layers, \
        self.epochs, self.lr_policy, self.weights_decay, \
        self.decay_rate, self.reg
                
    def get_logs(self):
        self.model_type, self.num_layers, self.layers, \
        self.epochs, self.lr_policy, self.weights_decay, \
        self.decay_rate, self.reg = \
        self.optimum['Model type'], self.optimum['Num layers'], self.optimum['Layer objs'], \
        self.optimum['Max epochs'], self.optimum['L.R. policy'], self.optimum['Weights decay'], \
        self.optimum['L.R. decay'], self.optimum['Reg']            
        
    def plot_loss(self, to_show=False):
        """ Plot gradient descent curve """
        plot(range(len(self.loss_history)), self.loss_history, linewidth=2.1)
        xlabel('Epochs')
        ylabel('Loss')
        show()

    def inferences(self, target, test_set=None, all_exp=False):
        """ Display model results i.e. predictions on test set """
        if all_exp:
            for example in range(dset.CIFAR10.test_size):
                print('Ground truth: (%d) %s || Predecition: (%d) %s || Confidence: %.2f %' %
                      (target[example], dset.CIFAR10.classes[int(target[example])],
                       int(self.predictions[example]),
                       dset.CIFAR10.classes[int(self.predictions[example])],
                       self.output[-1][example] * 100))
        else:
            test_set = test_set.cpu()
            test_set = \
                (test_set.numpy().reshape(dset.CIFAR10.test_size, 3, 32, 32).transpose(0, 2, 3, 1).astype("uint8"))
            while True:
                example = input("Which test example? (0-9999): ")
                if example < 0 or example >= dset.CIFAR10.test_size:
                    return
                print('Ground truth: (%d) %s' % (int(target[example]),
                                                 dset.CIFAR10.classes[int(target[example])]))
                imshow(test_set[example])
                xlabel(str(int(self.predictions[example])) + ' : ' +
                       dset.CIFAR10.classes[int(self.predictions[example])])
                ylabel('Confidence: ' + str(format(self.output[-1][example] * 100, '.2f')) + '%')

class LinearLayer(ModelNN):
    """Linear Layer class"""

    LayerName = 'Linear'

    def __init__(self, num_ipt_neurons, num_opt_neurons):
        # print 'Linear layer created'
        # allocate size for torche state variables appropriately
        super(LinearLayer, self).__init__()
        self.ipt_neurons = num_ipt_neurons
        self.opt_neurons = num_opt_neurons
        self.w = torch.rand(num_ipt_neurons, num_opt_neurons).type(hw.dtype)
        self.b = torch.zeros(1, num_opt_neurons).type(hw.dtype)

    def forward(self, ipt, target=None):
        #  if not dset.isTrain:
        #    print('w & b @ Linear layer: ', self.w)
        # print 'I/P @ Linear layer:', ipt.size()
        output = torch.mm(ipt, self.w) + self.b
        return output

    def backward(self, ipt, grad_output, i=-1):
        if i == -1:
            grad_w = torch.mm(ipt.t(), grad_output)
            grad_b = torch.sum(grad_output, dim=0, keepdim=True)
            return [grad_w, grad_b]
        grad_output = torch.mm(grad_output, ipt.t())
        return grad_output


class Activation(ModelNN):
    """ReLU Activation layer class"""

    LayerName = 'Activation'

    def __init__(self, activate_func=None):
        super(Activation, self).__init__()
        self.activation = activate_func

    @staticmethod
    def relu(ipt):
        # print ipt
        activation_relu = torch.clamp(ipt, min=0)
        # print activation_relu
        return activation_relu

    @staticmethod
    def backward_relu(ipt, grad_output):
        grad_output[ipt <= 0] = 0
        return grad_output


class CeCriterion(ModelNN):
    """Cross-entropy criterion"""

    LayerName = 'Criterion'

    def __init__(self, classifier=None):
        super(CeCriterion, self).__init__()
        self.classifier = classifier

    @staticmethod
    def softmax(opt):
        opexp = torch.exp(opt)
        softmax_func = opexp / torch.sum(opexp, dim=1, keepdim=True)
        value, index = torch.max(softmax_func, 1)
        # print value, index
        return [value, index.cpu(), softmax_func]

    def linear(self, opt, target):
        pass

    @staticmethod
    def backward_softmax(softmax, target):
        # computes and returns the gradient of the Loss with
        # respect to the input to this layer.
        d_probs = softmax
        d_probs[range(dset.CIFAR10.batch_size), target] -= 1  # Derivation of gradient of loss
        d_probs /= dset.CIFAR10.batch_size
        return d_probs


class Optimize:
    """Schedules learning rate and saves the optimum paramters"""

    def __init__(self, nn_obj):
        self.nn_alias = nn_obj
        self.lr0 = nn_obj.lr

    def constant(self):
        pass

    def time_decay(self, epoch, decay=0):
        self.nn_alias.lr = self.lr0 / (1 + decay * epoch)

    def step_decay(self, epoch, decay_after=5, drop=0.5):
        if decay_after is epoch:
            self.nn_alias.lr *= drop

    def exp_decay(self, decay, epoch):
        self.nn_alias.lr = (self.lr0 * math.exp(-decay * epoch))

    def set_optim_param(self, epoch=-1):
        if self.nn_alias.loss < self.nn_alias.optimum['Loss']:
            self.nn_alias.optimum['Loss'], self.nn_alias.optimum['Epoch'], self.nn_alias.optimum['Learning rate'] = \
                (self.nn_alias.loss, epoch, self.nn_alias.lr)
            self.nn_alias.optimum['Weights'], self.nn_alias.optimum['Biases'] = \
                (self.nn_alias.weights, self.nn_alias.biases)
        if epoch == self.nn_alias.epochs - 1:
            # Set optimum parameters
            self.nn_alias.weights, self.nn_alias.biases = \
                (self.nn_alias.optimum['Weights'], self.nn_alias.optimum['Biases'])

            '''
            self.optimum = {'Trained': False, 'Fitting tested': False, 'Tested': False, 'Inferenced': False, 
                        'Model type': self.model_type, 'Net': self.net, 'Num layers': self.num_layers,'Layer objs': self.layers,  
                        'Weights': 0, 'Biases': 0, 
                        'Max epochs': self.epochs, 'Epoch': 0, 'Learning rate': self.lr, 'L.R. policy': self.lr_policy,
                        'Weights decay': self.weights_decay, 'L.R. decay': self.decay_rate, 'Reg': self.reg,
                        'Loss': float("inf"), 'TrainAcc': self.train_acc, 'TestAcc': self.test_acc}
            '''
            # Print least loss
            print("\nOptimum loss in %d epochs is: %f" %
                  (self.nn_alias.epochs, self.nn_alias.optimum['Loss']))

    def clear_gradients(self):
        pass
