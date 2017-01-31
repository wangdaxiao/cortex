'''A NLP dataset.

'''

import numpy as np
import progressbar
import re

from .. import BasicDataset, make_one_hot
from ...utils import floatX, intX, pi, _rng
from ...utils.tools import resolve_path


class WMT(BasicDataset):
    sp_map = dict(
        amp='%',
        apos='\'',
        gt='>',
        lt='<',
        quot='"'
    )
    
    omit = []#[' ', '', '.', ',', '!', ':', ';', ')', '(', '<', '>', '"', '%', '&quot;', '&apos;s', '&apos;', '&apos;d', '-', '&apos;m', '&apos;t', '&quot']
    
    def __init__(self, tokens=None, source=None, character_level=False,
                 name='WMT', max_words=1000, max_length=20, **kwargs):
        self.source = source
        self.max_length = max_length
        self.character_level = character_level
    
        source = resolve_path(source)
        if tokens is None:
            tokens = self.tokenize(source)
        self.tokens = tokens
        self.process_tokens(max_words)
        
        X, M, M_p = self.get_data(source)
        
        data = {'input': X, 'mask': M, 'mask_padded': M_p}
        distributions = {'input': 'multinomial', 'mask': 'binomial',
                         'mask_padded': 'binomial'}
        transpose = {'input': (1, 0, 2), 'mask': (1, 0), 'mask_padded': (1, 0)}

        super(WMT, self).__init__(data, distributions=distributions,
                                  process_centered=False, name=name,
                                  transpose=transpose, **kwargs)
        
    def process_tokens(self, max_words):
        word_list = sorted(self.tokens, key=self.tokens.get, reverse=True)
        self.token_map = {'<bos>': 0, '<eos>': 1, '<UNK>': 2}
        self.r_token_map = {0: '<bos>', 1: '<eos>', 2: '<UNK>'}
        for i, word in enumerate(word_list[:max_words]):
            self.token_map[word] = i + 3
            self.r_token_map[i + 3] = word
        
    def tokenize(self, source):
        max_length = self.max_length
        tokens = {}
        lines = 0
        with open(source) as f:
            for line in f:
                lines += 1
        
        with open(source) as f:
            widgets = ['Tokenizing', progressbar.Bar()]
            pbar = progressbar.ProgressBar(widgets=widgets, maxval=lines).start()
            i = 0
            for line in f:
                if self.character_level:
                    words = list(line[:-1])
                else:
                    words = line[:-1].split(' ')
                words = [w for w in words if w not in self.omit]
                if len(words) > max_length:
                    continue
                else:
                    for word in words:
                        if not self.character_level:
                            word = word.lower()
                        if word in tokens:
                            tokens[word] += 1
                        else:
                            tokens[word] = 1
                i += 1
                pbar.update(i)
            print
                
        return tokens
    
    def string_to_ints(self, s):
        if self.character_level:
            words = list(s)
            words = [w for w in words if w not in self.omit]
        else:
            words = s.split(' ')
            words = [w.lower() for w in words if w not in self.omit]
        tokens = [0] + [self.token_map.get(w, 2) for w in words] + [1]
        return tokens
    
    def ints_to_string(self, tokens, remove_pads=True, axis=0):
        if tokens.ndim > 1:
            t_idx = range(tokens.ndim)
            t_idx = t_idx + [t_idx.pop(axis)]
            r_idx = [t_idx[:len(t_idx)-1].index(i)
                     for i in range(len(t_idx))
                     if i in t_idx[:len(t_idx)-1]]
            tokens = tokens.transpose(t_idx)
            shape = tokens.shape
            tokens = tokens.reshape(
                (reduce(lambda x, y: x * y, shape[:-1])), shape[-1])
        else:
            shape = None
            
        sentences = []
        for i in xrange(tokens.shape[0]):
            t_ = tokens[i].tolist()
            try:
                bos_idx = t_.index(0)
            except ValueError:
                bos_idx = 0
            try:
                eos_idx = t_.index(1) + 1
            except ValueError:
                try:
                    eos_idx = t_.index(-1)
                except ValueError:
                    eos_idx = len(t_)
                    
            t_ = t_[bos_idx:eos_idx]
            words = [self.r_token_map[t] for t in t_]
            if self.character_level:
                sentences.append(''.join(words))
            else:
                sentences.append(' '.join(words))
        sentences = np.array(sentences)
        
        if shape is not None:
            sentences = sentences.reshape((shape[:-1]))
            sentences = sentences.transpose(r_idx)
        
        return sentences
    
    def get_data(self, source):
        max_length = self.max_length
        max_length_ = 0
        lines = 0
        with open(source) as f:
            for line in f:
                lines += 1
                
        X = np.zeros((lines, max_length+2)).astype(intX) + 2# - 1
        M = np.zeros_like(X)
        M_p = np.zeros_like(X)
        
        with open(source) as f:
            widgets = ['Processing', progressbar.Bar()]
            pbar = progressbar.ProgressBar(widgets=widgets, maxval=lines).start()
            i = 0
            for line in f:
                tokenized_line = self.string_to_ints(line[:-1])
                max_length_ = max(max_length_, len(tokenized_line))
                l = len(tokenized_line)
                if l > max_length + 2:
                    continue
                else:                    
                    X[i, :l] = tokenized_line[:l]
                    M[i, :l] = np.ones(l)
                    M_p[i, 1:l-1] = np.ones(l-2)
                    i += 1
                    pbar.update(i)
            print
        print('Found {} sentences'.format(i))
        X = X[:i, :max_length_]
        M = M[:i, :max_length_]
        M_p = M_p[:i, :max_length_]
            
        return X.astype(intX), M.astype(floatX), M_p.astype(floatX)
    
    def viz(self, X=None, X_s=None, P=None, M=None, X_t=None, P_t=None):
        #print X.shape
        X = np.argmax(X, axis=-1)[:, :20]
        X_s = np.argmax(X_s, axis=-1)
        M = M[:, :20]
        #print X.shape
        #print P[:, :, 0]
        #print P.shape
        #print P[:, :, 0].sum(axis=-1)
        #print M.shape
        #print M[:, 0]
        #print P[0, -1, 0]
        #print P_t[:, 0, :]
        #print np.argmax(X_t[:, 0], axis=-1)
        #print X_t.shape
        #print P_t.shape
        #print X
        lines = self.ints_to_string(X, axis=0)
        print 'Sampled:'
        print lines
        lines_s = self.ints_to_string(X_s, axis=0)
        print 'Real:'
        print lines_s
    
_classes = {'WMT': WMT}
