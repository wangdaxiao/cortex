'''Module for basic datasets.

'''

import logging


__all__ = ['twodimage']

from twodimage import *

logger = logging.getLogger(__name__)
from . import mnist
_modules = [mnist]
_classes = {}
for module in _modules:
    if not hasattr(module, '_classes'):
        logger.warn('Module %s does not specify `_classes`. Module classes '
                    'will not be accessible from higher level resolve '
                    'functions' % (module.__name__))
    else:
        _classes.update(**module._classes)