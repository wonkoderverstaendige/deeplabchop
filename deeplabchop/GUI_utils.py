#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  8 00:55:37 2018

@author: sebastian
"""
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.widgets import  RadioButtons

import numpy as np
import imageio
import os  
import pickle

class Controller_crop_GUI():
    def __init__(self):
        self.pos1 = None
        self.pos2 = None
        self.click = False
                
    def crop_GUI(self, frame):
        
        fig, ax = plt.subplots()
        plt.title('Select area, press c to crop')
        
        ax.imshow(frame)
        
        self.finished=False
        
        def onclick(event):
            
            if event.button==1:
                self.pos1 = [event.xdata,event.ydata]
                self.click=True
                   
        def onrelease(event):
            if event.button==1:
                self.click=False
                self.pos2 = [event.xdata,event.ydata]
                ax.imshow(frame)
                rect = patches.Rectangle((self.pos1[0],self.pos1[1]),self.pos2[0]-self.pos1[0],self.pos2[1]-self.pos1[1],linewidth=1,edgecolor='r',facecolor='none')            
                ax.add_patch(rect)
                plt.draw()    
                
        def mouse_move(event):
            if self.click:
                ax.clear()
                ax.imshow(frame) 
                rect = patches.Rectangle((self.pos1[0],self.pos1[1]),event.xdata-self.pos1[0],event.ydata-self.pos1[1],linewidth=1,edgecolor='r',facecolor='none')            
                ax.add_patch(rect)
                              
                
        def keypress(event):
            if event.key == 'c':
                plt.close(fig)
            self.finished = True 
            
        cid1 = fig.canvas.mpl_connect('button_press_event', onclick)
        cid2 = fig.canvas.mpl_connect('key_press_event', keypress)
        cid4 = fig.canvas.mpl_connect('motion_notify_event', mouse_move)
        cid3 = fig.canvas.mpl_connect('button_release_event', onrelease)
        
        while not self.finished:
            plt.pause(0.01)
        
        return(np.array([self.pos1, self.pos2],dtype = np.int32))
        

class Controller_label_GUI():
    def __init__(self, categories = [], frames=[]):

        self.frames = frames
        self.current_frame=0
        self.category = 0
        self.category_names = categories
        self.categories = dict(zip(categories, range(len(categories))))
        self.labels = [dict(zip(categories,[[[],[]] for i in range(len(categories))])) for j in range(len(self.frames)) ]
        
    def label_GUI(self, preview_next=True):
        
        self.finished = False
        self.shift = False
        
        fig, ax = plt.subplots()
        plt.title('Label images, navigate with arrow keys. backspace to remove label, q to exit.')
        ax.imshow(self.frames[self.current_frame])

        def switchfun(label):
            self.category = self.categories[label]
            plt.draw()
        
        rax = plt.axes([0.05, 0.7, 0.15, 0.15])
        radio = RadioButtons(rax, self.categories)
        radio.on_clicked(switchfun)

        def draw_screen():
            ax.clear()
            if preview_next and self.category == len(self.category_names)-1:
                ax.imshow(self.frames[self.current_frame]//4*3+self.frames[(self.current_frame+1)%len(self.frames)]//4)
            else:
                ax.imshow(self.frames[self.current_frame]) 
            for l in self.labels[self.current_frame].values(): ax.scatter(l[0],l[1])
            plt.title('frame '+str(self.current_frame+1))

        def onclick(event):
            nonlocal radio
            if event.button==1 and not event.xdata is None and not event.ydata>0 is None:
                if self.shift:
                    #print(self.labels[self.current_frame][self.category_names[self.category]])
                    (self.labels[self.current_frame][self.category_names[self.category]])[0].append(event.xdata)
                    (self.labels[self.current_frame][self.category_names[self.category]])[1].append(event.ydata) 
                else:   
                    self.labels[self.current_frame][self.category_names[self.category]] = [[event.xdata],[event.ydata]]           
                    if self.category == len(self.categories)-1:
                        self.category = 0
                        self.current_frame= (self.current_frame+1)%(len(self.frames))
                        radio.set_active(self.category)
                    else:
                        self.category+=1
                        radio.set_active(self.category)        
                draw_screen()     
                
        def keypress(event):
            nonlocal radio
            if event.key == 'down':
                self.category = min(len(self.categories)-1,self.category+1)
                radio.set_active(self.category)
            if event.key == 'up':
                self.category = max(0,self.category-1)
                radio.set_active(self.category)
            if event.key == 'right':
                self.current_frame = (self.current_frame+1)%(len(self.frames))
                draw_screen()
            if event.key == 'left':
                self.current_frame = (self.current_frame-1)%(len(self.frames))          
                draw_screen()                        
            if event.key == 'q':
                plt.close()
                self.finished=True
            if event.key == 'shift':
                self.shift = True
            if event.key == 'backspace':
                self.labels[self.current_frame][self.category_names[self.category]] = [[],[]]
                draw_screen()
                
        def keyrelease(event):
            if event.key == 'shift':
                self.shift = False
                if self.category == len(self.categories)-1:
                    self.category = 0
                    self.current_frame= (self.current_frame+1)%(len(self.frames))
                    radio.set_active(self.category)
                else:
                    self.category+=1
                    radio.set_active(self.category) 
                
            
        cid1 = fig.canvas.mpl_connect('button_press_event', onclick)
        cid2 = fig.canvas.mpl_connect('key_press_event', keypress)
        cid2 = fig.canvas.mpl_connect('key_release_event', keyrelease)

        while not self.finished:
            plt.pause(0.01)
        
        return(self.labels)



def run_labeler(cfg,root='.'):


    labels = cfg['joints']
    experimenter = cfg['experimenter']
    frames = []
    names = []

    for image_set in cfg['image_sets'].items():
        for image in [f for f in os.listdir(os.path.join(root,image_set[1]['img_path'])) if '.png' in f]:
            print('loading '+image)
            names.append(os.path.join(root,image_set[1]['img_path'],image))
            frames.append(imageio.imread(os.path.join(root,image_set[1]['img_path'],image)))

    l = Controller_label_GUI(labels,frames)
    labels_out= l.label_GUI()

    #print(labels_out)
    #img4680.png,sebastian,head,130,247
    for i,name in enumerate(names):
        file_name=os.path.join(os.path.dirname(name),'multijoint.csv')
        print(file_name)
        with open(file_name, 'a') as f:
            for label in labels_out[i].keys():
                print(labels_out[i][label][0])
                #line = ','.join([file_name,experimenter,label,str(int(labels_out[i][label][0][0])),str(int(labels_out[i][label][1][0]))]+'\n')
                if labels_out[i][label][0]:
                    f.write(','.join([os.path.basename(name),experimenter,label,str(int(labels_out[i][label][0][0])),str(int(labels_out[i][label][1][0]))])+'\n')



