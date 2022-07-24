import os
import glob
import json
import importlib

import cv2
import torch
import numpy as np
import matplotlib.pyplot as plt


def get_img_names(folder, img_format='png'):
    img_paths = glob.glob(os.path.join(folder, f'*.{img_format}'))
    img_names = [os.path.basename(x) for x in img_paths]
    return img_names

def preprocess_image(image, img_w=None, img_h=None, mean=np.array([0, 0, 0]), std=np.array([1, 1, 1])):
    img = image.copy()
    if img_w and img_h:
        img = cv2.resize(img, (img_w, img_h))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = ((img.astype(np.float32) / 255.0 - mean) / std).astype(np.float32)
    img = torch.from_numpy(img).permute(2, 0, 1)
    return img

def preprocess_mask2onehot(image, labels, img_w=None, img_h=None):
    input_img = image.copy()
    if img_w and img_h:
        img = cv2.resize(input_img, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
    img = np.array([(img == x) for x in labels])
    img = np.stack(img, axis=-1).astype(np.float32)
    img = torch.from_numpy(img).permute(2, 0, 1)
    return img

def preprocess_single_mask(image, labels, img_w=None, img_h=None):
    img = image.copy()
    if img_w and img_h:
        img = cv2.resize(img, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
    for index, label in enumerate(labels):
        img[img == label] = index
    img = torch.from_numpy(img)
    return img

def process_img2np(image):
    img = image.cpu().clone()
    img = img.permute(1, 2, 0).numpy() * 255
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img

def process_multimask2np(image, labels):
    img = image.cpu().clone()
    img = img.permute(1, 2, 0).numpy().astype(bool)
    h, w, c = img.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    for c_index in range(c):
        mask[img[:, :, c_index]] = labels[c_index]
    return mask

def get_obj_from_str(string, reload=False):
    module, cls = string.rsplit('.', 1)
    if reload:
        module_imp = importlib.import_module(module)
        importlib.reload(module_imp)
    return getattr(importlib.import_module(module, package=None), cls)

def instantiate_from_config(config):
    return get_obj_from_str(config['target'])(**config.get('params', dict()))

def show_image(image, figsize=(5, 5), cmap=None, title='', xlabel=None, ylabel=None, axis=False):
    plt.figure(figsize=figsize)
    plt.imshow(image, cmap=cmap)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.axis(axis)
    plt.show();
    
def show_images(images, figsize=(5, 5), title='', cmap=None, xlabel=None, ylabel=None, axis=False):
    fig, axes = plt.subplots(1, len(images), figsize=figsize)
    for ax, img in zip(axes, images):
        ax.imshow(img, cmap=cmap)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.axis(axis)
    plt.show();
    
def mask2rle(img):
    '''https://www.kaggle.com/paulorzp/rle-functions-run-length-encode-decode'''
    pixels= img.T.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return ' '.join(str(x) for x in runs)

def rle2mask(mask_rle, shape):
    '''https://www.kaggle.com/paulorzp/rle-functions-run-length-encode-decode'''
    s = mask_rle.split()
    starts, lengths = [np.asarray(x, dtype=int) for x in (s[0:][::2], s[1:][::2])]
    starts -= 1
    ends = starts + lengths
    img = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for lo, hi in zip(starts, ends):
        img[lo : hi] = 1
    return img.reshape(shape).T

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def inverse_normalize(tensor, mean, std):
    for t, m, s in zip(tensor, mean, std):
        t.mul_(s).add_(m)
    return tensor

def normalized_image_to_numpy(image, mean=np.array([0, 0, 0]), std=np.array([1, 1, 1])):
    '''
    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    '''
    img = image.cpu()
    img = inverse_normalize(img, mean=mean, std=std)
    img = img.permute(1, 2, 0).numpy()*255
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img