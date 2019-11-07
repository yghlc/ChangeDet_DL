#!/usr/bin/env bash

## Introduction:  run training and test

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 06 November, 2019


co_dir=~/codes/PycharmProjects/ChangeDet_DL

#run training on Cryo Station
root=~/Data/experiment/Onera_S2_Change_Detection_dataset
img_pair_txt=${root}/changeDet_test.txt

batch_size=256
learning_rate=0.001
weight_decay=0.0001
num_epochs=20
num_workers=16
# for how often save the model
save_frequency=2

# trianing and validation
#python ${co_dir}/thawSlumpChangeDet/siamese_thawslump_cd.py ${root} ${img_pair_txt} --dotrain \
#-b ${batch_size} -l ${learning_rate} -w ${weight_decay} -e ${num_epochs} -s ${save_frequency} -n ${num_workers}



# prediction:
batch_size=1
num_workers=1
python ${co_dir}/thawSlumpChangeDet/siamese_thawslump_cd.py ${root} ${img_pair_txt} \
-b ${batch_size} -n ${num_workers}
