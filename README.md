Experimental rebuild of the DeepLabCut toolbox.

Please refer to the original [DeepLabCut](https://github.com/AlexEMG/DeepLabCut) repository.

Installation guide for linux
======

Open the terminal (ctrl + alt + t) for the following commands.

1. First we install the deeplabchop repository.
```
 git clone https://github.com/wonkoderverstaendige/deeplabchop
 cd deeplabchop
 conda env create -n dlc -f dlcdependencieswTF1.2.yml
 conda install -c anaconda tensorflow-gpu
 python setup.py install
```
If your system does not support GPU in python, then replace ``` conda install -c anaconda tensorflow-gpu``` with ``` conda install -c anaconda tensorflow```.


2. Next, we download the pre-trained DeepLabCut (ResNet) model.
 ```
cd pose_tensorflow/models/pretrained/
bash download.sh
cd ../../..
````

User Guide (Linux tested)
======

Here we provide a generic guide on how to create a project. These command ought to be executed in the terminal.

First, go to your deeplabchop folder and activate the (by installation) automatically generated virtual environment:
```
cd ~/deeplabchop
source activate dlc
```

To see deeplabchop's options type ```python dlc.py```.

#### 1. Creating a new project

To create a project from scratch and then use it, go through the following steps.

To create the project, type:
```
python dlc.py new projects/PROJECT_NAME EXPERIMENTER_NAME
```
where you should replace ```PROJECT_NAME``` and ```EXPERIMENTER_NAME``` to your personal project name and name.

A new project folder is now created, now you have to add your videos to the ```config.yaml``` file in the main project folder. This is where you show deeplabchop where to look for videos. You will need to add to add *every single video* to the list of the argument ```image_sets```. A specific example is the following:
```yaml
image_sets:
  /home/iglohut/deeplabchop/projects/PROJECT_NAME-EXPERIMENTER_NAME-2018-10-09/videos/test.mp4:
    crop: 0,0,-1,-1
    img_path: data/testvid1
  ```
Here you first give it the video path, followed by two arguments. The ```crop``` argument crops the video from (x1, y1) to (x2, y2) size. The current arguments (0,0) and (-1, -1) tells it not to crop anything.Next, the ``img_path`` argument is where the video frames for training should be stored.


#### 2. Training the network
it is easiest to use the wizard command. This will go through the steps to label your video data and train the network.
Your first call of the wizard will crop images from your videos.
```
python dlc.py wizard projects/PROJECT_NAME_WITH_DATE
```

After this step you should check the ```data``` sub-folder in your project to ensure that the videos are cropped correctly.  Next, remove all folders in the ```data``` folder.

You can now call the wizard again to automatically go through the steps to finally train the model.
```
python dlc.py wizard projects/PROJECT_NAME_WITH_DATE
```
Currently the steps are: CropAdjust, FrameExtraction, Annotated, TrainLabelsDrawn,Shuffled, DeepCutReady, Training, Evaluated, Inference. Where Training is the last step where actual work is done.

###### 2.1. Storing the model
The model is by default saved every 10000 iterations of training. You can change this by going to the config file of your model. This is located in the folder ```~\projects/YOUR_PROJECT/shuffles/shuffle_MODEL_NR/train``` and the config file to edit is `pose_cfg.yaml` where you should set the following to your favourite number:
```yaml
save_iters: 10000
```

  #### 3. Making your first predictions
  We are ultimately interested in predicting limbs on new video data.
 To make predictions you use the ```predict``` command in ```dlc.py```. Predictions are made for specific videos (so no batches). The predict command takes two arguments: ```MODEL_CONFIG``` and ```VIDEO_PATH```. An example use would be:
  ```
  python dlc.py predict /home/iglohut/deeplabchop/projects/PROJECT_NAME-EXPERIMENTER_NAME-2018-10-09/shuffles/shuffle001_95pct-EXPERIMENTER_NAME/train/pose_cfg.yaml /home/iglohut/deeplabchop/projects/PROJECT_NAME-EXPERIMENTER_NAME-2018-10-09/videos/test.mp4
  ```

  To maximize your fun, you can draw the predictions on your videos by using the ```draw``` command. This takes two arguments: ```PATH_/*.h5``` prediction file and ```VIDEO_PATH``` with specific example:
  ```
  python dlc.py draw /home/iglohut/deeplabchop/projects/PROJECT_NAME-EXPERIMENTER_NAME-2018-10-09/videos/test.h5 /home/iglohut/deeplabchop/projects/PROJECT_NAME-EXPERIMENTER_NAME-2018-10-09/videos/test.mp4
  ```
Your limb-labeled videos will be stored in the ```VIDEO_PATH``` folder with extension of the original video name with ```VIDEO_NAME.labeled.*```.
