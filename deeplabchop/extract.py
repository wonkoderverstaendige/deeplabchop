import os
import math
import sys
from pathlib import Path

import numpy as np
from moviepy.editor import VideoFileClip
from skimage import io
from skimage.util import img_as_ubyte
from tqdm import tqdm

import imageio

# Is there a way to check if that's needed?
imageio.plugins.ffmpeg.download()


def crop_frame(image, x1, y1, x2, y2):
    x2 = image.shape[1] - 1 if x2 < 0 else x2
    y2 = image.shape[0] - 1 if y2 < 0 else y2

    x_bad = any([0 > x >= image.shape[0] for x in [x1, x2]])
    y_bad = any([0 > y >= image.shape[1] for y in [y1, y2]])
    if x_bad or y_bad:
        raise ValueError('Crop bounding box exceeds image dimensions.')

    cropped = image[y1:y2, x1:x2]
    return cropped


def get_frame(video, t_frame=0.0):
    """Crop a single frame from the video to check cropping result. Stored alongside video.

    :param video: Path to video
    :param t_frame: position to extract example frame from, in seconds. Default: 0
    :return: image

    """
    with VideoFileClip(str(video)) as clip:
        image = clip.get_frame(t_frame)

    return image


def crop_examples(video, crop, destination=None):
    video_path = Path(video)
    dst_path = Path(video_path.parent if destination is None else destination).resolve()

    image_original = get_frame(video)
    image_cropped = crop_frame(image_original, *crop)

    io.imsave(dst_path / video_path.with_suffix('.original.png').name, image_original)
    io.imsave(dst_path / video_path.with_suffix('.cropped.png').name, image_cropped)


def extract_frames(video, destination, num_frames, crop=None, seed=0):
    """Extracts [num_frames] images from a video and stores """
    np.random.seed(seed)

    video_path = Path(video).resolve()
    if not video_path.exists():
        raise FileNotFoundError('Video "{}" not found.'.format(video_path))

    img_path = Path(destination).absolute()

    # TODO: Exception handling for faulty videos
    # Warning: Handles to VideoClip object are fickle, and getting them stuck is pretty easy.
    # Best always handle them with a context manager.
    with VideoFileClip(str(video_path)) as clip:
        print('Video duration: {} s, {} fps, uncropped frame size: {}'.format(clip.duration, clip.fps, clip.size))

        # Crop frames
        if clip is not None:
            x1, y1, x2, y2 = crop
            print('Cropping box {}->{}'.format((x1, y1), (x2, y2)))
            clip = clip.crop(x1, y1, x2, y2)

        num_frames_clip = int(clip.duration * clip.fps)
        padding = int(math.ceil(math.log10(num_frames_clip)))  # file name padding

        print('Storing images in {}'.format(img_path))

        # Grab frames from video and store as png file
        frame_indices = sorted(np.random.randint(0, num_frames_clip, num_frames))

        for idx in tqdm(frame_indices):
            image = img_as_ubyte(clip.get_frame(idx / clip.fps))
            fname = 'img{idx:0{pad}d}.png'.format(idx=idx, pad=padding)

            try:
                io.imsave(img_path / fname, image)
            except FileExistsError:
                print('{} exists already. Skipping.'.format(fname))




