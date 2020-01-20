#!/bin/bash


#introduction: Run the whole process of pixel-based Change detection using Siamese Neural Network
#
#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 20 January, 2020



# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

eo_dir=~/codes/PycharmProjects/Landuse_DL
cd_dir=~/codes/PycharmProjects/ChangeDet_DL
cd ${eo_dir}
git pull
cd -

## modify according to test requirement or environment
## comment these out on ITSC GPU server
#set GPU on Cryo06
export CUDA_VISIBLE_DEVICES=1
#set GPU on Cryo03
export CUDA_VISIBLE_DEVICES=0,1
gpu_num=2
para_file=para.ini

################################################
SECONDS=0
# remove previous data or results if necessary
rm -r img_pairs change_maps pair_images_changemap_list.txt || true

#extract sub_image pairs based on the training polygons
${cd_dir}/thawSlumpChangeDet/bash_get_cd_training_images.py ${para_file}

duration=$SECONDS
echo "$(date): time cost of preparing training data: ${duration} seconds">>"time_cost.txt"
SECONDS=0
################################################
## training

${cd_dir}/thawSlumpChangeDet/bash_train_siamese_cd.py ${para_file}

duration=$SECONDS
echo "$(date): time cost of training: ${duration} seconds">>"time_cost.txt"
SECONDS=0
################################################

#exit

#export model



################################################
## inference and post processing, including output "time_cost.txt"
${cd_dir}/thawSlumpChangeDet/bash_prediction_cd.py ${para_file}


#${eo_dir}/thawslumpScripts/postProc.sh ${para_file}
#
#${eo_dir}/thawslumpScripts/accuracies_assess.sh ${para_file}

################################################
## backup results
${eo_dir}/thawslumpScripts/backup_results.sh ${para_file} 1