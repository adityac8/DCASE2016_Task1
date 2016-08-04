'''
SUMMARY:  Dcase 2016 Task 1. Scene classification
          Training time: 12 s/epoch. (Tesla M2090)
          test acc: 75.2% +- ?, train frame acc: 89.4%, test frame acc: 63.1% +- ? after 10 epoches on fold 1
          Try adjusting hyper-params, optimizer, longer epoches to get better results. 
AUTHOR:   Qiuqiang Kong
Created:  2016.05.11
Modified: 2016.05.29
          2016.06.24
--------------------------------------
'''
import sys
sys.path.append('/user/HS229/qk00006/my_code2015.5-/python/Hat')
import pickle
import numpy as np
np.random.seed(1515)
from Hat.models import Sequential
from Hat.layers.core import InputLayer, Flatten, Dense, Dropout
from Hat.layers.rnn import SimpleRnn, LSTM, GRU
from Hat.layers.pool import GlobalMeanTimePool
from Hat.callbacks import SaveModel, Validation
from Hat.preprocessing import sparse_to_categorical
from Hat.optimizers import Rmsprop, Adam
from Hat import serializations
import Hat.backend as K
import config as cfg
import prepareData as ppData


# hyper-params
fe_fd = cfg.fe_mel_fd
agg_num = 10        # concatenate frames
hop = 10            # step_len
n_hid = 500
n_out = len( cfg.labels )
fold = 0            # can be 0, 1, 2, 3

# prepare data
scaler = ppData.Scaler( fe_fd, cfg.tr_csv[fold] )
tr_X, tr_y = ppData.GetAllData( fe_fd, cfg.tr_csv[fold], agg_num, hop, scaler )
te_X, te_y = ppData.GetAllData( fe_fd, cfg.te_csv[fold], agg_num, hop, scaler )
tr_y = sparse_to_categorical( tr_y, n_out )
te_y = sparse_to_categorical( te_y, n_out )

[batch_num, n_time, n_freq] = tr_X.shape
print 'tr_X.shape:', tr_X.shape     # (batch_num, n_time, n_freq)
print 'tr_y.shape:', tr_y.shape     # (batch_num, n_labels )


# build model
seq = Sequential()
seq.add( InputLayer( (n_time, n_freq) ) )
seq.add( LSTM( n_out=100, act='tanh' ) )       # output size: (batch_num, n_time, n_freq). Try SimpleRnn, LSTM, GRU instead. 
seq.add( GlobalMeanTimePool( masking=None ) )  # mean along time axis, output shape: (batch_num, n_freq)
seq.add( Flatten() )
seq.add( Dense( n_hid, act='relu' ) )
seq.add( Dropout( 0.1 ) )
seq.add( Dense( n_out, act='softmax' ) )
md = seq.combine()
md.summary()

# callbacks
# tr_err, te_err are frame based. To get event based err, run recognize.py
validation = Validation( tr_x=tr_X, tr_y=tr_y, va_x=None, va_y=None, te_x=te_X, te_y=te_y, call_freq=1, dump_path='Results/validation.p' )
save_model = SaveModel( dump_fd='Md', call_freq=1 )
callbacks = [ validation, save_model ]

# optimizer
optimizer = Adam(1e-3)

# fit model
md.fit( x=tr_X, y=tr_y, batch_size=500, n_epoch=100, loss_type='categorical_crossentropy', optimizer=optimizer, callbacks=callbacks )

# run recognize.py to get results. 