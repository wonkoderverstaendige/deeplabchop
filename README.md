Experimental rebuild of the DeepLabCut toolbox.

Please refer to the original [DeepLabCut](https://github.com/AlexEMG/DeepLabCut) repository.

# Installation guide
git clone https://github.com/wonkoderverstaendige/deeplabchop
cd deeplabchop
conda env create -n dlc -f dlcdependencieswTF1.2.yml 
conda install -c anaconda tensorflow-gpu # If not gpu, remove " -gpu" 
python setup.py install

### to download the pre-trained DeepLabCut (ResNet) model, run:
cd pose_tensorflow/models/pretrained/
bash download.sh 
cd ../../..

python dlc.py #to see options
python dlc.py new projects/PROJECT_NAME EXPERIMENTER_NAME #to create new project


### now call the following line multiple times
### after 1st wizard: check cropped frame in project_folder/data/, then delete all folders inside data
python dlc.py wizard projects/PROJECT_NAME_WITH_DATE # yes with date! tab it
