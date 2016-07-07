'''
Caltech 101 Silhouettes dataset
'''

from scipy import io

from . import mnist
from ...utils import floatX


class Caltech(mnist.MNIST):
    def __init__(self, name='caltech', **kwargs):
        super(Caltech, self).__init__(name=name, **kwargs)

    def get_data(self, source, mode):
        data_dict = io.loadmat(source)

        if mode == 'train':
            X = data_dict['train_data']
            Y = data_dict['train_labels']
        elif mode == 'valid':
            X = data_dict['val_data']
            Y = data_dict['val_labels']
        elif mode == 'test':
            X = data_dict['test_data']
            Y = data_dict['test_labels']
        else:
            raise ValueError()

        return X.astype(floatX), Y

_classes = {'caltech': Caltech}