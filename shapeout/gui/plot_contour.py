#!/usr/bin/python
# -*- coding: utf-8 -*-
""" ShapeOut - contour plot methods

"""
from __future__ import division, unicode_literals

import chaco.api as ca
import chaco.tools.api as cta
from dclab import definitions as dfn
import numpy as np
import time
import warnings

from ..tlabwrap import isoelastics
from . import plot_common


def contour_plot(measurements, levels=[0.5,0.95],
                 axContour=None, isoel=None,
                 wxtext=False, square=True):
    """ Plot contour for two axes of an RTDC measurement
    
    Parameters
    ----------
    measurement : instance of RTDS_DataSet
        Contains measurement data.
    levels : float or list of floats in interval (0,1)
        Plot the contour at that particular level from the maximum (1).
    axContour : instance of matplotlib `Axis`
        Plotting axis for the contour.
    isoel : list for line plot
        Manually selected isoelastics to plot. Defaults to None.
        If no isoelastics are found, then a warning is raised.
    square : bool
        The plot has square shape.
    """
    mm = measurements[0]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()

    # Commence plotting
    if axContour is not None:
        raise NotImplementedError("Tell Chaco to reuse plots?")

    pd = ca.ArrayPlotData()
    contour_plot = ca.Plot(pd)
    contour_plot.id = "ShapeOut_contour_plot"

    scalex = mm.config["plotting"]["scale x"].lower()
    scaley = mm.config["plotting"]["scale y"].lower()

    ## Add isoelastics
    if mm.config["plotting"]["isoelastics"]:
        if isoel is None:
            chansize = mm.config["general"]["channel width"]
            #plotdata = list()
            # look for isoelastics:
            for key in list(isoelastics.keys()):
                if float(key.split("um")[0]) == chansize > 0:
                    plotdict = isoelastics[key]
                    for key2 in list(plotdict.keys()):
                        if key2 == "{} {}".format(xax, yax):
                            isoel = plotdict[key2]
        if isoel is None:
            warnings.warn("Could not find matching isoelastics for"+
                          " Setting: x={} y={}, Channel width: {}".
                          format(xax, yax, chansize))
        else:
            for ii, data in enumerate(isoel):
                x_key = 'isoel_x'+str(ii)
                y_key = 'isoel_y'+str(ii)
                #
                # # Crop data events outside of the plotting area
                # #data = crop_linear_data(data, areamin, areamax, circmin, circmax)
                #
                pd.set_data(x_key, data[:,0])
                pd.set_data(y_key, data[:,1])
                contour_plot.plot((x_key, y_key), color="gray",
                                  index_scale=scalex, value_scale=scaley)


    #colors = [ "".join(map(chr, np.array(c[:3]*255,dtype=int))).encode('hex') for c in colors ]
    if not isinstance(levels, list):
        levels = [levels]

    set_contour_data(contour_plot, measurements, levels=levels)

    # Axes
    left_axis = ca.PlotAxis(contour_plot, orientation='left',
                            title=dfn.axlabels[yax],
                            tick_generator=plot_common.MyTickGenerator())
    
    bottom_axis = ca.PlotAxis(contour_plot, orientation='bottom',
                              title=dfn.axlabels[xax],
                              tick_generator=plot_common.MyTickGenerator())
    # Show log scale only with 10** values (#56)
    contour_plot.index_axis.tick_generator=plot_common.MyTickGenerator()
    contour_plot.value_axis.tick_generator=plot_common.MyTickGenerator()
    contour_plot.overlays.append(left_axis)
    contour_plot.overlays.append(bottom_axis)

    contour_plot.title = "Contours"

    contour_plot.title_font = "modern 12"

    # zoom tool
    zoom = cta.ZoomTool(contour_plot,
                        tool_mode="box",
                        color="beige",
                        minimum_screen_delta=50,
                        border_color="black",
                        border_size=1,
                        always_on=True,
                        drag_button="right",
                        enable_wheel=True,
                        zoom_factor=1.1)
    contour_plot.tools.append(zoom)
    contour_plot.aspect_ratio = 1
    contour_plot.use_downsampling = True
    
    # pan tool
    pan = cta.PanTool(contour_plot, drag_button="left")

    contour_plot.tools.append(pan)

    return contour_plot


def set_contour_data(plot, measurements, levels=[0.5,0.95]):
    pd = plot.data
    # Plotting area
    mm = measurements[0]
    xax = mm.config["plotting"]["axis x"].lower()
    yax = mm.config["plotting"]["axis y"].lower()

    if mm.config["filtering"]["enable filters"]:
        x0 = getattr(mm, dfn.cfgmaprev[xax])[mm._filter]
        y0 = getattr(mm, dfn.cfgmaprev[yax])[mm._filter]
    else:
        # filtering disabled
        x0 = getattr(mm, dfn.cfgmaprev[xax])
        y0 = getattr(mm, dfn.cfgmaprev[yax])

    for ii, mm in enumerate(measurements):
        cname = "con_{}_{}_{}".format(mm.name, mm.identifier, ii)
        if cname in plot.plots:
            plot.delplot(cname)

        # Check if there is data to compute a contour from
        if len(mm._filter)==0 or np.sum(mm._filter)==0:
            break

        kde_type = mm.config["plotting"]["kde"].lower()
        kde_kwargs = plot_common.get_kde_kwargs(x=x0, y=y0, kde_type=kde_type,
                                                xacc=mm.config["plotting"]["kde accuracy "+xax],
                                                yacc=mm.config["plotting"]["kde accuracy "+yax])
        xacc = mm.config["plotting"]["contour accuracy "+xax]
        yacc = mm.config["plotting"]["contour accuracy "+yax]

        a = time.time()
        (X,Y,density) = mm.get_kde_contour(xax=xax, yax=yax, xacc=xacc, yacc=yacc,
                                           kde_type=kde_type, kde_kwargs=kde_kwargs)

        print("...KDE contour time {}: {:.2f}s".format(kde_type, time.time()-a))
        pd.set_data(cname, density)
  
        plev = list(density.max()*np.array(levels))

        if len(plev) == 2:
            styles = ["dot", "solid"]
        else:
            styles = "solid"
        
        # contour widths
        if "contour width" in mm.config["plotting"]:
            cwidth = mm.config["plotting"]["contour width"]
        else:
            cwidth = 1.2

        plot.contour_plot(cname,
                          name=cname,
                          type="line",
                          xbounds = (X[0][0], X[0][-1]),
                          ybounds = (Y[0][0], Y[-1][0]),
                          levels = plev,
                          colors = mm.config["plotting"]["contour color"],
                          styles = styles,
                          widths = [cwidth*.7, cwidth], # make outer lines slightly smaller
                          )
