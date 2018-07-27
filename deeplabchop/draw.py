from pathlib import Path
import math

import pandas as pd
import numpy as np
from tqdm import tqdm
from moviepy.editor import VideoFileClip
from skimage import draw
from skvideo import io
import matplotlib.pyplot as plt

PCUTOFF = .1
DEFAULT_COLORMAP = 'RdYlGn'


def draw_predictions_video(results, video):
    scorer = 'DeepCut_resnet50_social_interactionJan30shuffle1_200000'
    clip = VideoFileClip(video)
    ny, nx, fps = clip.h, clip.w, clip.fps

    df = pd.read_hdf(results)

    joints = list(np.unique(df.columns.get_level_values(1)))

    cmap = plt.cm.get_cmap(DEFAULT_COLORMAP, len(joints))
    print(cmap(1)[:3])
    # colors = (C[:, :3] * 255).astype(np.uint8)

    clip_out = io.FFmpegWriter('labeled.mp4', outputdict={'-r': str(15)})
    num_frames = math.ceil(clip.duration*clip.fps)

    for index, frame in enumerate(tqdm(clip.iter_frames(dtype='uint8'), total=num_frames)):
        for bpindex, bp in enumerate(joints):
            if df[scorer][bp]['likelihood'].values[index] > PCUTOFF:
                xc = int(df[scorer][bp]['x'].values[index])
                yc = int(df[scorer][bp]['y'].values[index])
                # rr, cc = circle_perimeter(yc,xc,radius)
                # if not index:
                #     print(xc, yc)
                rr, cc = draw.circle(yc, xc, 3, shape=(ny, nx))
                frame[rr, cc, :] = [c * 255 for c in cmap(bpindex)[:3]]
            clip_out.writeFrame(frame)
    clip.close()
    clip_out.close()


if __name__ == '__main__':
    pass