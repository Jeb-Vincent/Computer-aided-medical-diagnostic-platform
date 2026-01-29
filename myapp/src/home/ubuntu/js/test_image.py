#!/usr/bin/env python
# coding: utf-8
from tkinter import Image

from django.core.files import images
# In[ ]:


from keras.layers import Layer, Input, Dropout, Conv2D, Activation, add, UpSampling2D,     Conv2DTranspose, Flatten, Reshape
#from keras_contrib.layers.normalization.instancenormalization import InstanceNormalization, InputSpec
import tensorflow_addons as tfa
from tensorflow.keras.layers import InputSpec
from tensorflow_addons.layers import InstanceNormalization

from keras.layers.advanced_activations import LeakyReLU
from keras.models import Model
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time
import os
import keras.backend as K
import tensorflow as tf
from skimage.transform import resize
from skimage import color
from skimage import io as sk_io
from myapp.src.home.ubuntu.js.helper_funcs import ReflectionPadding2D

#from helper_funcs import *

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="0"

# ### Model parameters
# 
# This CycleGAN implementation allows a lot of freedom on both the training parameters and the network architecture.

opt = {}

# Data
opt['channels'] = 1
opt['img_shape'] = (512,512,1)

# Architecture parameters
opt['use_dropout'] = False  # Dropout in residual blocks
opt['use_bias'] = True  # Use bias
opt['use_resize_convolution'] = True  # Resize convolution - instead of transpose convolution in deconvolution layers (uk) - can reduce checkerboard artifacts but the blurring might affect the cycle-consistency

# Tweaks
opt['REAL_LABEL'] = 1.0  # Use e.g. 0.9 to avoid training the discriminators to zero loss

# ### Model architecture
# 
# #### Layer blocks
# These are the individual layer blocks that are used to build the generators and discriminator. More information can be found in the appendix of the [CycleGAN paper](https://arxiv.org/abs/1703.10593).

# Discriminator layers
def ck(model, opt, x, k, use_normalization, use_bias):
    x = Conv2D(filters=k, kernel_size=4, strides=2, padding='same', use_bias=use_bias)(x)
    if use_normalization:
        x = model['normalization'](axis=3, center=True, epsilon=1e-5)(x, training=True)
    x = LeakyReLU(alpha=0.2)(x)
    return x

# First generator layer
def c7Ak(model, opt, x, k):
    x = Conv2D(filters=k, kernel_size=7, strides=1, padding='valid', use_bias=opt['use_bias'])(x)
    x = model['normalization'](axis=3, center=True, epsilon=1e-5)(x, training=True)
    x = Activation('relu')(x)
    return x

# Downsampling
def dk(model, opt, x, k):  # Should have reflection padding
    x = Conv2D(filters=k, kernel_size=3, strides=2, padding='same', use_bias=opt['use_bias'])(x)
    x = model['normalization'](axis=3, center=True, epsilon=1e-5)(x, training=True)
    x = Activation('relu')(x)
    return x

# Residual block
def Rk(model, opt, x0):
    k = int(x0.shape[-1])

    # First layer
    x = ReflectionPadding2D((1,1))(x0)
    x = Conv2D(filters=k, kernel_size=3, strides=1, padding='valid', use_bias=opt['use_bias'])(x)
    x = model['normalization'](axis=3, center=True, epsilon=1e-5)(x, training=True)
    x = Activation('relu')(x)

    if opt['use_dropout']:
        x = Dropout(0.5)(x)

    # Second layer
    x = ReflectionPadding2D((1, 1))(x)
    x = Conv2D(filters=k, kernel_size=3, strides=1, padding='valid', use_bias=opt['use_bias'])(x)
    x = model['normalization'](axis=3, center=True, epsilon=1e-5)(x, training=True)
    # Merge
    x = add([x, x0])

    return x

# Upsampling
def uk(model, opt, x, k):
    # (up sampling followed by 1x1 convolution <=> fractional-strided 1/2)
    if opt['use_resize_convolution']:
        x = UpSampling2D(size=(2, 2))(x)  # Nearest neighbor upsampling
        x = ReflectionPadding2D((1, 1))(x)
        x = Conv2D(filters=k, kernel_size=3, strides=1, padding='valid', use_bias=opt['use_bias'])(x)
    else:
        x = Conv2DTranspose(filters=k, kernel_size=3, strides=2, padding='same', use_bias=opt['use_bias'])(x)  # this matches fractionally stided with stride 1/2
    x = model['normalization'](axis=3, center=True, epsilon=1e-5)(x, training=True)
    x = Activation('relu')(x)
    return x

# #### Architecture functions

def build_generator(model, opt, name=None):
    # Layer 1: Input

    input_img = Input(shape=opt['img_shape'])
    x = ReflectionPadding2D((3, 3))(input_img)
    x = c7Ak(model, opt, x, 32)

    # Layer 2-3: Downsampling
    x = dk(model, opt, x, 64)
    x = dk(model, opt, x, 128)

    # Layers 4-12: Residual blocks
    for _ in range(4, 13):
        x = Rk(model, opt, x)

    # Layer 13:14: Upsampling
    x = uk(model, opt, x, 64)
    x = uk(model, opt, x, 32)

    # Layer 15: Output
    x = ReflectionPadding2D((3, 3))(x)
    x = Conv2D(opt['channels'], kernel_size=7, strides=1, padding='valid', use_bias=True)(x)
    x = Activation('tanh')(x)
    # x = Reshape((217,181,1))(x)
    # print("Generator Model:")
    # print(Model(inputs=input_img, outputs=x, name=name).summary())
    return Model(inputs=input_img, outputs=x, name=name)



# In[ ]:


def generate_image(image):
    # Load Model

    model = {}
    # Normalization
    model['normalization'] = InstanceNormalization
    model['G_A2B'] = build_generator(model, opt, name='G_A2B_model')
    model['G_B2A'] = build_generator(model, opt, name='G_B2A_model')

    weight_path = 'D:/PyCharm/djangoProject/myapp/src/home/ubuntu/js/saved_models/'

    GA2B = model['G_A2B']

    files_name = os.listdir(weight_path)

    for name in files_name:
        if 'trip-ce-ssimG_rate1False10.0100datasettime1' in name: # You need to change this.
         b = name.split('10.0') # Change here
         c = b[0].split('False') # Change here
         file_name = c[0]+c[1]
         a=b[1].split('time1') # Change here
         weight_file = os.path.join(weight_path,name)
         for weight in os.listdir(weight_file):
            if 'A2B' in weight and '.hdf5' in weight:
                print(os.path.join(weight_file,weight))
                GA2B.load_weights(os.path.join(weight_file,weight))

                #image = mpimg.imread(os.path.join(image_path,images))
                image = resize(image,(512,512))
                image = image[:, :, np.newaxis]
                image = image * 2 - 1
                real_image = image
                image = np.reshape(image,(1, 512,512,1))
                im = GA2B.predict(image)
                im = np.reshape(im,(512,512))
                im = im[:, :, np.newaxis]
                return im;





