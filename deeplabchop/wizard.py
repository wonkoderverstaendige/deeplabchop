import yaml
from pathlib import Path
import pkg_resources

from tqdm import trange, tqdm
from deeplabchop import DEBUG, util, status, extract, label, shuffle, training, GUI_utils


def _echo(s):
    # poor man's module specific logging
    print('Wizard: ' + s)


class Gandalf():
    def __init__(self, project, step):
        self.project = Path(project)
        self.project_status = status.read_status(project)
        if DEBUG:
            status.show_status(self.project)
        self.cfg = util.read_yaml(self.project / 'config.yaml')
        self.auto = 1 # For a while loop with all the commands later
        self.step = step # Could be auto or any of the steps
        self.steps = ["Created", "CheckDirConfig", "CropAdjust", "FrameExtraction", "Annotated", "TrainingLabelsDrawn",
                      "LabelsCollected", "Shuffled", "DeepCutReady", "Training", "Evaluated", "Inference"]
        self.extracommands = ["GetImgSet"]


    def Created(self):
        # Control for successful project creation
        # -------------------------------------------------------------------------------------------
        if 'Created' not in self.project_status:  # sanity check
            _echo("Whoopsie, this ain't Kansas no more! Something went terribly wrong during project creation.")
            self.auto = 0 # To stop wizard

        else:
            _echo('Project creation OK')

    def CheckDirConfig(self):
        # Check that dataset list in config file and in data directory match
        # -------------------------------------------------------------------------------------------
        data_path = self.project / 'data'
        datasets = [d for d in data_path.glob('*') if d.is_dir() and 'labeled' not in d.name]
        if len(datasets) != len(self.cfg['image_sets']):
            Warning('Dataset directory not matching configuration file image set list.')
            # a lot of string wrangling just to have the output not be too confusing...
            print('Config:', ''.join(['\n\t' + k['img_path'] for k in self.cfg['image_sets'].values()]))
            print('data  :', ''.join(['\n\t' + '/'.join(k.parts[-2:]) for k in datasets]))
            print('')
            # TODO: Update command to add new image sets to existing project
        util.update_yaml(self.project / 'status.yaml', {'CheckDirConfig': True})


    def GetImgSet(self):
        videopath = Path(input("What is the absolute path to your videos?: "))
        if not videopath.exists():
            print("Input path path doesn't exist! Given path:")
            print("\n", videopath)

        else:
            xred = str(input("With how much pixels do you want to crop the x-axis?: "))
            yred = str(input("With how much pixels do you want to crop the y-axis?: "))
            vid_dict = {}
            for v in videopath.resolve().glob("*"): # To ensure any fvideo file format. If there are nonvideos, you have a problem. Extend to multiple
                vid_dict.update(self._video2imgset(v, xred, yred))

            util.update_yaml(self.project / 'config.yaml', {'image_sets': vid_dict})


    def _video2imgset(self, video, xred=0,yred=0):
        vidstr = str(video)
        vidname = vidstr.rsplit('/',1)[-1].rsplit(".",1)[0]
        vid = {vidstr: {'crop': xred + "," + yred + ", -1,-1",
                         'img_path': 'data/' + vidname}}
        return vid

    def CropAdjust(self):
        # Check cropping configuration for videos
        # -------------------------------------------------------------------------------------------
        # if 'CropAdjust' not in self.project_status or not self.project_status['CropAdjust']:
        if self._shouldo('CropAdjust'):
            _echo('Checking video cropping configuration...')

            # Create directory for image sets
            if not len(self.cfg['image_sets']):
                print('No videos given to create image sets. Stopping.')
                print("\n Try using the wizard command GetImgSet to set image set to your project video folder.")
                ## TODO for every video in /videos create img_sets .yaml file that has no crop and unique output -
                self.auto = 0  # To stop wizard
                return

            for video, metadata in self.cfg['image_sets'].items():
                video_path = self.project / video
                img_path = self.project / 'data' / video_path.with_suffix('').name
                img_path.mkdir(exist_ok=True)

                # check cropping
                crop = list(map(int, metadata['crop'].split(',')))
                extract.crop_examples(video_path, crop, img_path)
                _echo('Check cropping of "{}" in "{}"'.format(video, img_path))
            util.update_yaml(self.project / 'status.yaml', {'CropAdjust': True})
            _echo('Check image set directories for original and cropped example frames and '
                  'adjust as needed.\n---------------------------------------------------')
            ## TODO delete function OR print that it everything in data/ should be deleted

            self.auto = 0  # To stop wizard
            # return
        else:
            _echo('Crop adjustment OK')

    def FrameExtraction(self):
        # Extract images from all videos
        # -------------------------------------------------------------------------------------------
        if self._shouldo('FrameExtraction'):
            _echo('Next up: Creating image sets...')
            num_frames = max(2, int(self.cfg['num_frames']) // len(self.cfg['image_sets']))

            # Loop over all video files specified in the project configuration
            # Total number of frames is evenly divided between the videos.
            # Does not take length of the video into account... worse, a very short
            # video might have duplicates extracted!
            # TODO: Distribute extracted frames according to video length
            for n, (video, metadata) in enumerate(self.cfg['image_sets'].items()):
                Path.mkdir(self.project / metadata['img_path'])
                video_path = Path(video)
                crop = list(map(int, metadata['crop'].split(',')))
                seed = int(self.cfg['random_seed']) + n
                print('Extracting {} frames with seed {} from {}'.format(num_frames, seed, video_path.name))
                extract.extract_frames(self.project / video_path, num_frames=num_frames,
                                       destination=self.project / metadata['img_path'],
                                       crop=crop, seed=seed)

            util.update_yaml(self.project / 'status.yaml', {'FrameExtraction': True})
            print('\nYou can now annotate frames in e.g. ImageJ and store the results in the '
                  'image set directories as `Results.csv`.')
            self.auto = 0  # To stop wizard
            # return

        else:
            _echo('Frame Extraction OK')

    def Annotated(self):
        # User annotation of joint position in image set
        # -------------------------------------------------------------------------------------------
        if self._shouldo('Annotated'):
            do_labeling = input('Run labeling GUI? [Y/n]')
            if not do_labeling in ['N', 'n']:
                GUI_utils.run_labeler(self.cfg, root=self.project)
            else:
                _echo('Looking for joint annotation files...')
                for n, (video, metadata) in enumerate(self.cfg['image_sets'].items()):
                    img_path = (self.project / Path(metadata['img_path'])).resolve()
                    print(img_path)
                    if not img_path.joinpath('Results.csv').exists():
                        print('Missing `Results.csv` for {}'.format(img_path))
                        self.auto = 0  # To stop wizard
                        return

                    # Minimize ImageJ csv
                    joints = self.cfg['joints']
                    print(joints)
                    label.reduce_imagej_csv(img_path, self.cfg['joints'], self.cfg['experimenter'])

            util.update_yaml(self.project / 'status.yaml', {'Annotated': True})
            _echo('Minimized {} image set label file(s).'.format(len(self.cfg['image_sets'])))
        else:
            # TODO: Check existence of csv files
            _echo('Image set annotations OK')


    def TrainingLabelsDrawn(self):
        # Draw labels on images for verification
        # -------------------------------------------------------------------------------------------
        if self._shouldo('TrainingLabelsDrawn'):
            _echo('Drawing labels on images in data sets for verification...')
            for n, (video, metadata) in enumerate(self.cfg['image_sets'].items()):
                print(video, metadata)
                label.draw_image_labels(self.project / metadata['img_path'] / 'multijoint.csv', self.cfg['joints'],
                                        cmap_name=self.cfg['cmap'] if 'cmap' in self.cfg else None)
            util.update_yaml(self.project / 'status.yaml', {'TrainingLabelsDrawn': True})
            _echo('Labels drawn. Check labeled images in image set directories')
            self.auto = 0  # To stop wizard
            # return
        else:
            _echo('Drawing Labels OK')


    def LabelsCollected(self):
        # Join csv files of all image sets
        # -------------------------------------------------------------------------------------------
        if self._shouldo('LabelsCollected'):
            _echo('Preparing combined label file...')
            label.combine_labels(self.project / 'data')
            util.update_yaml(self.project / 'status.yaml', {'LabelsCollected': True})
            # Not stopping loop in this step
        else:
            _echo('Label Collection OK')


    def Shuffled(self):
        # Create shuffles
        # -------------------------------------------------------------------------------------------
        if self._shouldo('Shuffled'):
            _echo('Shuffling and splitting training set')
            for n in trange(self.cfg['num_shuffles'], leave=False):
                num_frames = int(self.cfg['num_frames'])
                f_train = float(self.cfg['train_fraction'])
                num_train = int(num_frames * f_train)
                num_testing = num_frames - num_train

                shuffle_name = 'shuffle{:03d}_{:.0f}pct-{}'.format(n, 100 * f_train, self.cfg['experimenter'])
                tqdm.write(shuffle_name)

                labels_csv = self.project / 'data' / 'joint_labels.csv'
                shuffle_path = self.project / 'shuffles' / shuffle_name

                # Create shuffle, training and test directories
                _ = [shuffle_path.joinpath(d).mkdir(exist_ok=True) for d in ['', 'train', 'test']]

                # Shuffle all images from the labeled example set with the specified fraction of training
                # to test images. The result is a list of labels for chosen images in a .mat or .csv file
                # to be used during training
                shuffle.shuffle(csv_file=labels_csv, train_fraction=f_train, destination=shuffle_path,
                                joints=self.cfg['joints'],
                                boundary=self.cfg['boundary'])

                tqdm.write('Shuffling #{} w/ {}:{} train and test images'.format(n, num_train, num_testing))

            util.update_yaml(self.project / 'status.yaml', {'Shuffled': True})
            # Not stopping loop in this step
        else:
            _echo('Shuffling OK')



    def DeepCutReady(self):
        # Create directories and configuration files for pose-tensorflow (DeeperCut)
        # -------------------------------------------------------------------------------------------
        if self._shouldo('DeepCutReady'):
            _echo('Training preparation...')
            # Create training and testing directories for each shuffle
            shuffles = [d.resolve() for d in self.project.joinpath('shuffles').glob('*') if d.is_dir()]
            if not len(shuffles):
                util.update_yaml(self.project / 'status.yaml', {'Shuffled': False})
                print('No training sets found. Rerun wizard!')

            for shuffle_path in shuffles:
                _echo(str(shuffle_path))
                # Create training yaml
                train_set_path = shuffle_path / 'training.mat'
                if not train_set_path.resolve().exists():
                    raise FileNotFoundError('Could not find "training.mat" file for shuffle "{}"'.format(shuffle_path))
                joints = self.cfg['joints']
                items2change = {'dataset': '../training.mat',
                                "num_joints": len(joints),
                                "all_joints": [[i] for i in range(len(joints))],
                                "all_joints_names": joints}

                resource_package = __name__  # Could be any module/package name
                resource_path = '/'.join(('..', 'resources', 'templates', 'training_pose_cfg.yaml'))

                pose_cfg_template = pkg_resources.resource_filename(resource_package, resource_path)

                # Create configuration yaml for training, and keep configuration data for the test configuration
                trainingdata = shuffle.training_pose_yaml(pose_cfg_template, items2change,
                                                          shuffle_path / 'train' / 'pose_cfg.yaml')

                # Keys to keep for the test configuration yaml
                keys2save = ['dataset', 'num_joints', 'all_joints', 'all_joints_names', 'net_type', 'init_weights',
                             'global_scale', 'location_refinement', 'locref_stdev']

                shuffle.test_pose_yaml(trainingdata, keys2save, shuffle_path / 'test/pose_cfg.yaml')
            util.update_yaml(self.project / 'status.yaml', {'DeepCutReady': True})
            # Not stopping while loop here
        else:
            _echo('Training prep OK')


    def Training(self):
        # Training
        # -------------------------------------------------------------------------------------------
        if self._shouldo('Trained') or self._shouldo('Training'):
            _echo('Start training...')
            shuffles = [d.resolve() for d in self.project.joinpath('shuffles').glob('*') if d.is_dir()]
            util.update_yaml(self.project / 'status.yaml', {'Trained': True})
            for shfl in shuffles:
                cfg_yaml_path = shfl / 'train/pose_cfg.yaml'
                _echo('Training starting for: {}'.format(cfg_yaml_path))
                training.train(cfg_yaml_path)
            self.auto = 0  # To stop wizard
            # return

        else:
            _echo('Training completed (to some degree)')


    def Evaluated(self):
        # Evaluation
        if self._shouldo('Evaluated'):
            _echo('Evaluation trained models')
            self.auto = 0  # To stop wizard
            # return
        else:
            _echo('Eavluation complete')


    def Inference(self):
        # Inference
        if self._shouldo('ReadyForUse') or self._shouldo('Inference'):
            _echo('What is left to do?')
            self.auto = 0  # To stop wizard
            # return
        else:
            _echo('Use me!')

    def _shouldo(self, step):
        if step not in self.project_status or not self.project_status[step] or step == self.step:
            return True
        else: return False


    def __call__(self):

        if self.step == "auto":
            self.auto = 1
            for idx, step in enumerate(self.steps):
                if not self.auto: break
                else:
                    exec("self." + step + "()")

        else: # If specific step is given
            if (self.step not in self.steps) and (self.step not in self.extracommands):
                print("The step", self.step, "does not exist!")

            else: ## TODO if command is too far, tell 'em to do previous
                print("Executing step:", self.step, "------------------------------------")
                exec("self." + self.step + "()")




def step(project, step):
    Wizard = Gandalf(project, step)
    Wizard() # Should just use __call__ automatically
