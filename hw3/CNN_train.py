import pandas as pd 
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Input
from keras.layers import LSTM
from keras.layers import GRU
from keras.layers import Dropout
from keras.layers import TimeDistributed
from keras.callbacks import EarlyStopping
from keras.layers import Conv1D, Conv2D
from keras.layers import MaxPooling2D,GlobalAveragePooling1D
from keras.layers import Flatten
from keras.models import load_model
from keras.layers import Bidirectional
from keras.layers.normalization import BatchNormalization
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import History ,ModelCheckpoint
from keras.layers import Activation, LeakyReLU
import collections
import sys
import pickle
import os
os.environ['CUDA_VISIBLE_DEVICES'] = "0"

train_path = sys.argv[1]

## load data
def normalize_1(x):
    x = (x - x.mean())/x.std()
    return x
def normalize_2(x):
    x = x/255.
    return x
train = pd.read_csv(train_path)
X = np.array([row.split(" ") for row in train["feature"].tolist()],dtype=np.float32)
y = train["label"].tolist()

with open('encoder.pkl', 'rb') as f:
    encoder = pickle.load(f)

y = encoder.transform(y)

def shuffle_split_data(X, y, percent):
    arr_rand = np.random.rand(X.shape[0])
    split = arr_rand < np.percentile(arr_rand, percent)
    X_train = X[split]
    y_train = y[split]
    X_test =  X[~split]
    y_test = y[~split]

    print len(X_Train), len(y_Train), len(X_Test), len(y_Test)
    return X_train, y_train, X_test, y_test

train_X, valid_X, train_y, valid_y = shuffle_split_data(X, y, percent=0.9)

filter_vis_input = train_X[10].reshape(48,48,1)
output_index = train_y[10]
train_X = normalize_2(train_X.reshape(-1,48,48,1))
valid_X = normalize_2(valid_X.reshape(-1,48,48,1))


datagen = ImageDataGenerator(
            rotation_range=30,
            width_shift_range=0.2,
            height_shift_range=0.2,
            zoom_range=[0.8, 1.2],
            shear_range=0.2,
            horizontal_flip=True)
print("train_X shape", train_X.shape)
print("valid_X shape", valid_X.shape)


batch_size = 128
epochs = 400
input_shape = (48,48,1)
model = Sequential()
model.add(Conv2D(64,input_shape=input_shape, kernel_size=(5, 5), padding='same', kernel_initializer='glorot_normal'))
model.add(LeakyReLU(alpha=1./20))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
model.add(Dropout(0.25))

model.add(Conv2D(128, kernel_size=(3, 3), padding='same', kernel_initializer='glorot_normal'))
model.add(LeakyReLU(alpha=1./20))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
model.add(Dropout(0.3))

model.add(Conv2D(512, kernel_size=(3, 3), padding='same', kernel_initializer='glorot_normal'))
model.add(LeakyReLU(alpha=1./20))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
model.add(Dropout(0.35))

model.add(Conv2D(512, kernel_size=(3, 3), padding='same', kernel_initializer='glorot_normal'))
model.add(LeakyReLU(alpha=1./20))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
model.add(Dropout(0.35))

model.add(Flatten())

model.add(Dense(512, activation='relu', kernel_initializer='glorot_normal'))
model.add(BatchNormalization())
model.add(Dropout(0.5))
model.add(Dense(512, activation='relu', kernel_initializer='glorot_normal'))
model.add(BatchNormalization())
model.add(Dropout(0.5))
model.add(Dense(7, activation='softmax', kernel_initializer='glorot_normal'))

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
print(model.summary())
hist = History()
early_stop = EarlyStopping(monitor='val_acc', patience=7, verbose=1)
check_save  = ModelCheckpoint("model/model1-{epoch:05d}-{val_acc:.5f}.h5",monitor='val_acc',save_best_only=True)

model.fit_generator(
            datagen.flow(train_X, train_y, batch_size=batch_size), 
            steps_per_epoch=5*len(train_X)//batch_size,
            validation_data=(valid_X, valid_y),
            epochs=epochs, callbacks=[check_save,hist], workers = 10 )

model.save("model/model1.h5")
