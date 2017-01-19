#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - wx frontend components

"""
from __future__ import division, print_function, unicode_literals

import chaco.api as ca
import cv2
import dclab
from distutils.version import LooseVersion
from enable.api import Window

import numpy as np
import os

from PIL import Image
import warnings

import wx
from wx.lib.scrolledpanel import ScrolledPanel

# Constants in OpenCV moved from "cv2.cv" to "cv2"
if LooseVersion(cv2.__version__) < LooseVersion("3.0.0"):
    cv_const = cv2.cv
    cv_version3 = False
else:
    cv_const = cv2
    cv_version3 = True


class ImagePanel(ScrolledPanel):
    def __init__(self, parent, frame):
        ScrolledPanel.__init__(self, parent, -1)
        self.frame = frame
        self.parent = parent

        self.SetupScrolling(scroll_y=True, scroll_x=True)

        ## draw event selection tools
        # dropdown for plot selection
        self.WXCB_plot = wx.ComboBox(self,
                                     style=wx.CB_DROPDOWN|wx.CB_READONLY,
                                     size=(250,-1))
        # spin control for event selection
        self.WXSP_plot = wx.SpinCtrl(self, min=1, max=10000000)
        
        ctrlsizer = wx.BoxSizer(wx.HORIZONTAL)
        ctrlsizer.Add(wx.StaticText(self, label=_("Event:")),0, wx.ALIGN_CENTER)
        ctrlsizer.Add(self.WXCB_plot)
        ctrlsizer.Add(self.WXSP_plot)

        # Bindings
        self.Bind(wx.EVT_COMBOBOX, self.OnShowEvent, self.WXCB_plot)
        self.Bind(wx.EVT_SPINCTRL, self.OnShowEvent, self.WXSP_plot)
        
        ## Image panel with chaco don't work. I get a segmentation fault
        ## with Ubuntu 14.04
        ##
        ## See the bug at launchpad
        ## https://bugs.launchpad.net/ubuntu/+source/python-chaco/+bug/1145575
        #self.plot_window = ea.Window(self)
        #self.vbox = wx.BoxSizer(wx.VERTICAL)
        #self.vbox.Add(self.plot_window.control, 1, wx.EXPAND)
        #self.SetSizer(self.vbox)
        #self.vbox.Fit(self)
        #self.pd = ca.ArrayPlotData()
        #x = np.arange(100).reshape(10,10)
        #a = ca.ImageData()
        #a.set_data(x)
        #self.pd.set_data("cellimg", a)
        #implot = ca.Plot(self.pd)
        #implot.img_plot("cellimg")
        #container = ca.GridPlotContainer(
        #                              shape = (1,1),
        #                              spacing = (0,0),
        #                              padding = (0,0,0,0),
        #                              valign = 'top',
        #                              bgcolor = 'white',
        #                              fill_padding = True,
        #                              use_backbuffer = True)
        #container.add(implot)
        # CAUSE SEGMENTATION FAULT
        #self.plot_window.component = container
        #self.plot_window.redraw()

        # Draw image with wxPython instead
        self.startSizeX = 250
        self.startSizeY = 77
        self.img = wx.EmptyImage(self.startSizeX, self.startSizeY)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, 
                                         wx.BitmapFromImage(self.img))
        #self.mainSizer = wx.BoxSizer(wx.VERTICAL|wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.mainSizer.Add(self.imageCtrl, 1, wx.ALIGN_TOP|wx.ALIGN_LEFT)
        #self.SetSizer(self.mainSizer)
        #self.mainSizer.Fit(self)
        self.PlotImage()

        ## draw manual filtering options
        self.WXChB_exclude = wx.CheckBox(self, label=_("Exclude event"))
        exclsizer = wx.BoxSizer(wx.HORIZONTAL)
        exclsizer.Add(self.WXChB_exclude, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_CHECKBOX, self.OnChBoxExclude, self.WXChB_exclude)

        # Update Plot button
        updbutton = wx.Button(self, label=_("Update plot"))
        self.Bind(wx.EVT_BUTTON, self.OnUpdatePlot, updbutton)

        #exclsizer.AddSpacer(self.imageCtrl.GetSize()[0]-updbutton.GetSize()[0]-self.WXChB_exclude.GetSize()[0])        
        exclsizer.Add(updbutton, 0, wx.ALIGN_RIGHT)
        
        ## Add traces plot
        x = np.linspace(-np.pi, np.pi, 50)
        y = np.cos(x)+1
        plotkwargs = {}
        for key in dclab.dfn.tr_data:
            plotkwargs[key[1]] = y
        
        self.trace_data = ca.ArrayPlotData(x=x, **plotkwargs)

        self.trace_plot = ca.Plot(self.trace_data,
                                  padding=0,
                                  spacing=0)

        for key in list(plotkwargs.keys()):
            if key.count("raw"):
                color = "gray"
            elif key == "FL1med":
                color = "green"
            elif key == "FL2med":
                color = "orange"
            elif key == "FL3med":
                color = "red"
            self.trace_plot.plot(("x", key), type="line", color=color)

        container = ca.HPlotContainer(spacing=70,
                                      padding=50,
                                      bgcolor=self.GetBackgroundColour(),
                                      fill_padding=True,)#)
        container.add(self.trace_plot)
        
        self.plot_window = Window(self, component=container)

        sizer = wx.GridBagSizer(5,5)
        sizer.Add(ctrlsizer, (0,0))
        sizer.Add(self.imageCtrl, (1,0))
        sizer.Add(exclsizer, (2,0))
        self.plot_window.control.SetMinSize((300, 300))
        sizer.Add(self.plot_window.control, (3,0), span=(2,2), flag=wx.EXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.sizer = sizer


    def OnChBoxExclude(self, e=None):
        """ If the exclude-check box is triggered, change the
        corresponding value in the measurement."""
        mm_id = self.WXCB_plot.GetSelection()
        evt_id = self.WXSP_plot.GetValue() - 1
        mm = self.analysis.measurements[mm_id]
        mm._filter_manual[evt_id] = not self.WXChB_exclude.GetValue()


    def OnUpdatePlot(self, e=None):
        """ Update the entire plot with filters
        """
        self.frame.PanelTop.OnChangeFilter()
        
    
    def OnShowEvent(self, e=None):
        """ Called when self.WXCB_plot and self.WXSP_plot are selected """
        mm_id = self.WXCB_plot.GetSelection()
        evt_id = self.WXSP_plot.GetValue() - 1

        if mm_id == -1:
            return
        
        if evt_id == -1:
            evt_id = 0

        self.ShowEvent(mm_id, evt_id)


    def ShowEvent(self, mm_id, evt_id):
        """
        Parameters
        ----------
        
        mm_id : int
            measurement identifier (index in self.analysis.measurements)
        evt_id : int
            frame identifier, starts at 0
        
        """
        self.UpdateSelections(mm_id=mm_id, evt_id=evt_id)
        mm = self.analysis.measurements[mm_id]
        # Check if video file exists
        if mm.video is None or not os.path.isfile(os.path.join(mm.fdir, mm.video)):
            # abort
            self.PlotImage(None)
            return
        # Taking the abspath of the video does not always work with OpenCV?
        #vfile = os.path.join(dataset.fdir, dataset.video)
        # Instead, go to the directory and open the video there.
        old_dir = os.getcwd()
        os.chdir(mm.fdir)
        video = cv2.VideoCapture(mm.video)
        os.chdir(old_dir)
        if cv_version3:
            totframes = video.get(cv_const.CAP_PROP_FRAME_COUNT)
        else:
            totframes = video.get(cv_const.CV_CAP_PROP_FRAME_COUNT)
        
        # determine video file offset. Some RTDC setups
        # do not record the first image of a video.
        frames_skipped = mm.Configuration["General"]["Video Frame Offset"]
        actual_sel_offset = evt_id - frames_skipped
        if actual_sel_offset < 0:
            # Display an empty image if there is no image for the event
            warnings.warn("No image for event {}.".format(evt_id))
            self.PlotImage(None)
        else:
            if cv_version3:
                video.set(cv_const.CAP_PROP_POS_FRAMES, actual_sel_offset)
            else:
                video.set(cv_const.CV_CAP_PROP_POS_FRAMES, actual_sel_offset)
            
            flag, cellimg = video.read()

            if flag:
                # add contour in red
                if len(cellimg.shape) == 2:
                    # convert grayscale to color
                    cellimg = np.tile(cellimg, [3,1,1]).transpose(1,2,0)
                
                
                r = cellimg[:,:,0]
                b = cellimg[:,:,1]
                g = cellimg[:,:,2]
                
                # only do this if there was a contour file loaded
                if len(mm.contours) > 0:
                    contours = mm.contours[evt_id]
                    if contours is not None:
                        r[contours[:,1], contours[:,0]] = 255
                        b[contours[:,1], contours[:,0]] = 0
                        g[contours[:,1], contours[:,0]] = 0
                
                self.frame.ImageArea.PlotImage(cellimg)

        video.release()
        print("Frame {} / {}".format(evt_id, totframes))

        # Update exclude check-box
        self.WXChB_exclude.SetValue(not mm._filter_manual[evt_id])

        # Set max value for spin control
        max_evt = self.analysis.measurements[mm_id].time.shape[0]
        self.WXSP_plot.SetRange(1, max_evt)

        # Plot traces
        if len(list(mm.traces)) != 0:
            self.plot_window.control.Show(True)
            empty_traces = []
            for key in mm.traces:
                data = mm.traces[key][evt_id]
                if data.size == 0:
                    empty_traces.append(key)
                else:
                    # Set y values for present traces
                    self.trace_data.set_data(key, data)
                    dshape = data.shape

            # Set x-values for all plots
            self.trace_data.set_data("x", np.arange(dshape[0]))
            # Set other trace data to zero if event does not have it
            zerodata = np.zeros(dshape[0])
            for ekey in empty_traces:
                self.trace_data.set_data(ekey, zerodata)

        else:
            self.plot_window.control.Show(False)
           
        self.Layout()
        self.GetParent().Layout()
       

    def PlotImage(self, image=None):
        def pil_to_wx_bmp(image):
            width, height = image.size
            mybuffer = image.convert('RGB').tobytes()
            bitmap = wx.BitmapFromBuffer(width, height, mybuffer)
            return bitmap
        
        def pil_to_wx_img(image):
            width, height = image.size
            mybuffer = image.convert('RGB').tobytes()
            bitmap = wx.ImageFromBuffer(width, height, mybuffer)
            return bitmap

        if image is None:
            x = np.linspace(0, 255, self.startSizeX*self.startSizeY)
            image = np.array(x.reshape(self.startSizeY,self.startSizeX),
                             dtype=np.uint8)
        
        os = image.shape
        newx = os[1] * 2
        newy = os[0] * 2
        image = Image.fromarray(image)
        
        #wxbmp = pil_to_wx_bmp(image)
        wximg = pil_to_wx_img(image)
        
        # Image scaling
        wximg = wximg.Scale(newx, newy)
        self.img.Destroy()
        self.img = wx.BitmapFromImage(wximg)
        self.imageCtrl.SetBitmap(self.img)
        # Redraw the panel to prevent artifact images on Windows
        #self.Layout()


    def UpdateAnalysis(self, analysis):
        """ Update the choices of the dopdown list with a new analysis """
        self.analysis = analysis
        self.UpdateSelections()


    def UpdateSelections(self, mm_id=None, evt_id=None):
        # Determine plot titles and set selection
        sel = self.WXCB_plot.GetSelection()
        choices = [ mm.title for mm in self.analysis.measurements ]
        self.WXCB_plot.SetItems(choices)
        
        if mm_id is not None:
            self.WXCB_plot.SetSelection(mm_id)
        elif sel != -1:
            self.WXCB_plot.SetSelection(sel)
        else:
            self.WXCB_plot.SetValue("--")

        if evt_id is not None:
            # Sanity check:
            self.WXSP_plot.SetValue(evt_id+1)


