#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - plot export

"""
from __future__ import division, print_function

import chaco
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from chaco.api import PlotGraphicsContext
import os
import warnings
import wx


def export_plot_pdf(parent):
    dlg = wx.FileDialog(parent, _("Export plot as PDF"), 
                        parent.config.GetWorkingDirectory("PDF"), "",
                        _("PDF file")+" (*.pdf)|*.pdf",
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        if not path.endswith(".pdf"):
            path += ".pdf"
        parent.config.SetWorkingDirectory(os.path.dirname(path), "PDF")
        container = parent.PlotArea.mainplot.container
        
        #old_height = container.height
        #old_width = container.width
        
        
        
        #a4_factor = 297/210
        ## Segmentation-faults:
        #from chaco.api import PlotGraphicsContext
        #gc = PlotGraphicsContext((int(container.outer_width), int(container.outer_height)))
        #container.draw(gc, mode="normal")
        #gc.save(path)

        #container.auto_size=True
        #container.auto_center=True
        
        # get inner_boundary
        (bx, by) = container.outer_bounds
        
        #(x, y) = (bx, by) = container.outer_bounds
        #x2 = 0,
        #y2 = 0
        #for c in container.components:
        #    x = min(c.x, x)
        #    y = min(c.y, y)
        #    x2 = max(c.x2, x2)
        #    y2 = max(c.y2, y2)
        #container.set_outer_bounds(0, (x2-x))
        #container.set_outer_bounds(1, (y2-y))

        # Correction factor 0.9 wih size of plots yields
        # approximately the right size for all kinds of container
        # shapes.
        container.set_outer_bounds(0, (300)*container.shape[1]**.9)
        container.set_outer_bounds(1, (300)*container.shape[0]**.9)
        
        # scatter plot classes
        class_sp = (chaco.colormapped_scatterplot.ColormappedScatterPlot,
                   chaco.scatterplot.ScatterPlot)
        
        for c in container.components:
            for comp in c.components:
                if isinstance(comp, class_sp):
                    comp.marker_size /= 2
        
        
        dest_box = (.01, .01, -.01, -.01)
        try:
            gc = PdfPlotGraphicsContext(filename=path,
                                dest_box = dest_box,
                                pagesize="landscape_A4")
        except KeyError:
            warnings.warn("'landscape_A4' not defined for pdf "+\
                          "export. Please update `chaco`.")
            gc = PdfPlotGraphicsContext(filename=path,
                                dest_box = dest_box,
                                pagesize="A4")
        # draw the plot
        gc.render_component(container, halign="center",
                            valign="top")
        #Start a new page for subsequent draw commands.
        gc.save()
        container.set_outer_bounds(0, bx)
        container.set_outer_bounds(1, by)

        for c in container.components:
            for comp in c.components:
                if isinstance(comp, class_sp):
                    comp.marker_size *= 2

        #container.height = old_height
        #container.width = old_width
        #container.auto_size = True
        #container.auto_size = False

        ## TODO:
        ## Put this into a differnt function in PlotArea
        ## -> call it after each plot?
        
        ## Solves font Error after saving PDF:
        # /usr/lib/python2.7/dist-packages/kiva/fonttools/font_manag
        # er.py:1303: UserWarning: findfont: Could not match 
        # (['Bitstream Vera Sans'], 'normal', None, 'normal', 500, 
        # 12.0). Returning /usr/share/fonts/truetype/lato/
        # Lato-Hairline.ttf UserWarning)
        for aplot in container.plot_components:
            for item in aplot.overlays:
                if isinstance(item, chaco.plot_label.PlotLabel):
                    item.font = "modern 12"
                elif isinstance(item, chaco.legend.Legend):
                    item.font = "modern 10"
                elif isinstance(item, chaco.axis.PlotAxis):
                    item.title_font = "modern 12"
                    item.tick_label_font = "modern 10"
                elif isinstance(item, chaco.data_label.DataLabel):
                    item.font = "modern 9"
                else:
                    warnings.warn("Not resetting plot fonts for"+\
                                  "plot component class {}.".format(
                                  item.__class__))


def export_plot_png(parent):
    dlg = wx.FileDialog(parent, "Export plot as PNG", 
                        parent.config.GetWorkingDirectory("PNG"), "",
                        "PDF file (*.png)|*.png",
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        if not path.endswith(".png"):
            path += ".png"
        parent.config.SetWorkingDirectory(os.path.dirname(path), "PNG")
        container = parent.PlotArea.mainplot.container
        
        # get inner_boundary
        p = container

        dpi=600
        p.do_layout(force=True)
        gc = PlotGraphicsContext(tuple(p.outer_bounds), dpi=dpi)

        # temporarily turn off the backbuffer for offscreen rendering
        use_backbuffer = p.use_backbuffer
        p.use_backbuffer = False
        p.draw(gc)
        #gc.render_component(p)

        gc.save(path)

        p.use_backbuffer = use_backbuffer