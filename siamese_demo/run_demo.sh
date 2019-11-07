#!/usr/bin/env bash

# set GPU on Cryo06
export CUDA_VISIBLE_DEVICES=1

./siamese_demo2.py train
