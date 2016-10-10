'''
SUMMARY:  prepareData, some functions copy from py_sceneClassification2
AUTHOR:   Qiuqiang Kong
Created:  2016.05.11
Modified: 2016.10.09 modify variable name
--------------------------------------
'''
import numpy as np
from scipy import signal
import cPickle
import os
import matplotlib.pyplot as plt
from scipy import signal
import librosa
import config as cfg
import csv
import wavio
from hat.preprocessing import mat_2d_to_3d

### readwav
def readwav( path ):
    Struct = wavio.read( path )
    wav = Struct.data.astype(float) / np.power(2, Struct.sampwidth*8-1)
    fs = Struct.rate
    return wav, fs

### calculate features
# extract mel feature
# Use preemphasis, the same as matlab
def GetMel( wav_fd, fe_fd, n_delete ):
    names = [ na for na in os.listdir(wav_fd) if na.endswith('.wav') ]
    names = sorted(names)
    for na in names:
        print na
        path = wav_fd + '/' + na
        wav, fs = readwav( path )
        if ( wav.ndim==2 ): 
            wav = np.mean( wav, axis=-1 )
        assert fs==44100
        ham_win = np.hamming(1024)
        [f, t, X] = signal.spectral.spectrogram( wav, window=ham_win, nperseg=1024, noverlap=0, detrend=False, return_onesided=True, mode='magnitude' ) 
        X = X.T
        
        # define global melW, avoid init melW every time, to speed up. 
        if globals().get('melW') is None:
            global melW
            melW = librosa.filters.mel( fs, n_fft=1024, n_mels=40, fmin=0., fmax=22100 )
            melW /= np.max(melW, axis=-1)[:,None]
            
        X = np.dot( X, melW.T )
        X = X[:, n_delete:]
        
        # DEBUG. print mel-spectrogram
        #plt.matshow(np.log(X.T), origin='lower', aspect='auto')
        #plt.show()
        #pause
        
        out_path = fe_fd + '/' + na[0:-4] + '.f'
        cPickle.dump( X, open(out_path, 'wb'), protocol=cPickle.HIGHEST_PROTOCOL )

# Get Scaler from traing fold
def Scaler( fe_fd, csv_file ):
    # read csv
    with open( csv_file, 'rb') as f:
        reader = csv.reader(f)
        lis = list(reader)
    
    Xall = []
    for li in lis:
        # load data
        try:
            [na, lb] = li[0].split('\t')
        except:
            na = li[0]
        na = na.split('/')[1][0:-4]
        path = fe_fd + '/' + na + '.f'
        X = cPickle.load( open( path, 'rb' ) )
        
        # reshape data to (n_block, n_time, n_freq)
        Xall.append( X )
    
    Xall = np.concatenate( Xall, axis=0 )
    from sklearn import preprocessing
    scaler = preprocessing.StandardScaler().fit(Xall)
    return scaler
    
# Load training fold or testing fold data and scaler them
def GetAllData( fe_fd, csv_file, agg_num, hop, scaler ):
    # read csv
    with open( csv_file, 'rb') as f:
        reader = csv.reader(f)
        lis = list(reader)
    
    # init list
    X3d_all = []
    y_all = []
    
    for li in lis:
        # load data
        [na, lb] = li[0].split('\t')
        na = na.split('/')[1][0:-4]
        path = fe_fd + '/' + na + '.f'
        X = cPickle.load( open( path, 'rb' ) )
        
        X = scaler.transform( X )
        
        # reshape data to (n_block, n_time, n_freq)
        X3d = mat_2d_to_3d( X, agg_num, hop )
        X3d_all.append( X3d )
        y_all += [ cfg.lb_to_id[lb] ] * len( X3d )
    
    # concatenate list to array
    X3d_all = np.concatenate( X3d_all )
    y_all = np.array( y_all )
    
    return X3d_all, y_all

# create an empty folder
def CreateFolder( fd ):
    if not os.path.exists(fd):
        os.makedirs(fd)
        
if __name__ == "__main__":
    CreateFolder( cfg.dev_fe_fd )
    CreateFolder( cfg.dev_fe_mel_fd )
    
    # calculate mel feature
    GetMel( cfg.dev_wav_fd, cfg.dev_fe_mel_fd, n_delete=0 )