__author__ = 'labx'

import os
import random
import sys

import numpy
import xraylib
from PyQt4.QtGui import QWidget, QFont, QPalette, QColor, QGridLayout, QLabel
from matplotlib.patches import FancyArrowPatch, ArrowStyle
from scipy import optimize, asarray

from oasys.widgets import gui
from oasys.widgets.gui import OasysPlotWindow
from oasys.widgets import congruence

from silx.gui.plot.ImageView import ImageView

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from matplotlib import figure as matfig
    import pylab
except ImportError:
    print(sys.exc_info()[1])
    pass

import Shadow.ShadowToolsPrivate as stp

class ShadowCongruence():

    @classmethod
    def checkEmptyBeam(cls, input_beam):
        if input_beam is None: return False
        elif not hasattr(input_beam._beam, "rays"): return False
        elif len(input_beam._beam.rays) == 0: return False
        else: return True

    @classmethod
    def checkGoodBeam(cls, input_beam):
        go = numpy.where(input_beam._beam.rays[:, 9] == 1)

        if len(input_beam._beam.rays[go]) == 0:
            return False
        else:
            return True

    @classmethod
    def checkBraggFile(cls, file_name):
        file = open(file_name, "r")

        try:
            rows = file.readlines()

            if len(rows) < 10: raise Exception("Bragg file malformed, please check input")

            first_row = ShadowCongruence.__get_numbers(rows[0].strip())
            if not len(first_row) == 3: raise Exception("Bragg file malformed, please check input")

            second_row = ShadowCongruence.__get_numbers(rows[1].strip())
            if not len(second_row) == 3: raise Exception("Bragg file malformed, please check input")

            if not (rows[2].strip().startswith("(") and \
                            rows[3].strip().startswith("(") and \
                            rows[4].strip().startswith("(") and \
                            rows[5].strip().startswith("(")):
                raise Exception("Bragg file malformed, please check input")

            seventh_row = ShadowCongruence.__get_numbers(rows[6].strip())
            if not len(seventh_row) == 3: raise Exception("Bragg file malformed, please check input")

            eighth_row = ShadowCongruence.__get_numbers(rows[7].strip())
            if not len(eighth_row) == 3: raise Exception("Bragg file malformed, please check input")

            nineth_row = ShadowCongruence.__get_numbers(rows[8].strip())
            if not len(nineth_row) == 1: raise Exception("Bragg file malformed, please check input")
        except Exception as e:
            file.close()

            raise e

    @classmethod
    def checkPreReflFile(cls, file_name):
        file = open(file_name, "r")

        try:
            rows = file.readlines()

            if len(rows) < 3: raise Exception("PreRefl file malformed, please check input")

            first_row = ShadowCongruence.__get_numbers(rows[0].strip())
            if not len(first_row) == 4: raise Exception("PreRefl file malformed, please check input")

            second_row = ShadowCongruence.__get_numbers(rows[1].strip())
            if not len(second_row) == 1: raise Exception("PreRefl file malformed, please check input")

            try:
                elements = int(second_row[0])
            except:
                raise Exception("PreRefl file malformed, please check input")

            if len(rows) != (elements*2) + 2: raise Exception("PreRefl file malformed, please check input")
        except Exception as e:
            file.close()

            raise e

    @classmethod
    def checkPreMLayerFile(cls, file_name):
        file = open(file_name, "r")

        try:
            rows = file.readlines()

            if len(rows) < 2: raise Exception("PreMLayer file malformed, please check input")

            first_row = ShadowCongruence.__get_numbers(rows[0].strip())
            if not len(first_row) == 1: raise Exception("PreMLayer file malformed, please check input")

            try:
                elements = int(first_row[0])
            except:
                raise Exception("PreRefl file malformed, please check input")

            second_row = ShadowCongruence.__get_numbers(rows[1].strip())
            if not len(second_row) == int(elements): raise Exception("PreMLayer file malformed, please check input")

            try:
                separator_row = ShadowCongruence.__get_numbers(rows[2 + elements*3].strip())
                if not len(separator_row) == 1: raise Exception("PreMLayer file malformed, please check input")
            except:
                raise Exception("PreRefl file malformed, please check input")

            next_row = ShadowCongruence.__get_numbers(rows[2 + elements*3 + 1].strip())
            if not len(next_row) == 4: raise Exception("PreMLayer file malformed, please check input")
        except Exception as e:
            file.close()

            raise e

    @classmethod
    def check2ColumnFormatFile(cls, file_name, specific_name):
        try:
            if file_name.startswith('/'):
                values = numpy.loadtxt(os.path.abspath(file_name))
            else:
                values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/" + file_name))
        except:
            raise Exception(specific_name + " file malformed (should be 2 or more columns of numbers, separated by spaces), please check input")

        if len(values) < 2: raise Exception(specific_name + " file malformed (should be 2 or more columns of numbers, separated by spaces), please check input")

    @classmethod
    def checkErrorProfileFile(cls, file_name):
        file = open(file_name, "r")

        try:
            rows = file.readlines()

            if len(rows) < 2: raise Exception("Surface Error file malformed, please check input")

            first_row = ShadowCongruence.__get_numbers(rows[0].strip())
            if not len(first_row) == 2: raise Exception("Surface Error file malformed, please check input")

            n_x = int(first_row[0])

            if n_x > 500:
                raise Exception("Malformed file: maximum allowed point in X direction is 500")

        except Exception as e:
            file.close()

            raise e

    @classmethod
    def __get_numbers(cls, string):
        values = string.strip().split(" ")

        numbers = []
        for value in values:
            if not value == "":
                try:
                    numbers.append(value)
                except:
                    pass

        return numbers

class ShadowStatisticData:
    intensity = 0.0
    total_number_of_rays = 0
    total_good_rays = 0
    total_lost_rays = 0

    def __init__(self, intensity = 0.0,
                 total_number_of_rays = 0,
                 total_good_rays = 0,
                 total_lost_rays = 0):
        self.intensity = intensity
        self.total_number_of_rays = total_number_of_rays
        self.total_good_rays = total_good_rays
        self.total_lost_rays = total_lost_rays

class ShadowHistoData(ShadowStatisticData):
    fwhm = 0.0
    x_fwhm_i = 0.0
    x_fwhm_f = 0.0
    y_fwhm = 0.0

    def __init__(self, intensity = 0.0,
                 total_number_of_rays = 0,
                 total_good_rays = 0,
                 total_lost_rays = 0,
                 fwhm = 0.0,
                 x_fwhm_i = 0.0,
                 x_fwhm_f = 0.0,
                 y_fwhm = 0.0):
        super().__init__(intensity, total_number_of_rays, total_good_rays, total_lost_rays)
        self.fwhm = fwhm
        self.x_fwhm_i = x_fwhm_i
        self.x_fwhm_f = x_fwhm_f
        self.y_fwhm = y_fwhm

class ShadowPlotData(ShadowStatisticData):
    fwhm_h = 0.0
    fwhm_v = 0.0

    def __init__(self, intensity = 0.0,
                 total_number_of_rays = 0,
                 total_good_rays = 0,
                 total_lost_rays = 0,
                 fwhm_h = 0.0,
                 fwhm_v = 0.0):
        super().__init__(intensity, total_number_of_rays, total_good_rays, total_lost_rays)
        self.fwhm_h = fwhm_h
        self.fwhm_v = fwhm_v

class ShadowPlot:

    _is_conversione_active = True

    #########################################################################################
    #
    # FOR TEMPORARY USE: FIX AN ERROR IN PYMCA.PLOT.IMAGEWIEW
    #
    #########################################################################################


    @classmethod
    def set_conversion_active(cls, is_active=True):
        ShadowPlot._is_conversione_active = is_active

    """Sample code to add 2D dataset saving as text to ImageView."""


    #########################################################################################
    #
    # WIDGET FOR DETAILED PLOT
    #
    #########################################################################################

    class InfoBoxWidget(QWidget):
        intensity_field = ""
        total_rays_field = ""
        total_good_rays_field = ""
        total_lost_rays_field = ""
        fwhm_h_field = ""
        fwhm_v_field = ""

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0, is_2d=True):
            super(ShadowPlot.InfoBoxWidget, self).__init__()

            info_box_inner=gui.widgetBox(self, "Info")
            info_box_inner.setFixedHeight(515*y_scale_factor)
            info_box_inner.setFixedWidth(230*x_scale_factor)

            self.intensity = gui.lineEdit(info_box_inner, self, "intensity_field", "Intensity", tooltip="Intensity", labelWidth=115, valueType=str, orientation="horizontal")
            self.total_rays = gui.lineEdit(info_box_inner, self, "total_rays_field", "Total Rays", tooltip="Total Rays", labelWidth=115, valueType=str, orientation="horizontal")
            self.total_good_rays = gui.lineEdit(info_box_inner, self, "total_good_rays_field", "Total Good Rays", tooltip="Total Good Rays", labelWidth=115, valueType=str, orientation="horizontal")
            self.total_lost_rays = gui.lineEdit(info_box_inner, self, "total_lost_rays_field", "Total Lost Rays", tooltip="Total Lost Rays", labelWidth=115, valueType=str, orientation="horizontal")

            label_box_1 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

            self.label_h = QLabel("FWHM ")
            self.label_h.setFixedWidth(115)
            palette =  QPalette(self.label_h.palette())
            palette.setColor(QPalette.Foreground, QColor('blue'))
            self.label_h.setPalette(palette)
            label_box_1.layout().addWidget(self.label_h)
            self.fwhm_h = gui.lineEdit(label_box_1, self, "fwhm_h_field", "", tooltip="FWHM", labelWidth=115, valueType=str, orientation="horizontal")

            if is_2d:
                label_box_2 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

                self.label_v = QLabel("FWHM ")
                self.label_v.setFixedWidth(115)
                palette =  QPalette(self.label_h.palette())
                palette.setColor(QPalette.Foreground, QColor('red'))
                self.label_v.setPalette(palette)
                label_box_2.layout().addWidget(self.label_v)
                self.fwhm_v = gui.lineEdit(label_box_2, self, "fwhm_v_field", "", tooltip="FWHM", labelWidth=115, valueType=str, orientation="horizontal")

            self.intensity.setReadOnly(True)
            font = QFont(self.intensity.font())
            font.setBold(True)
            self.intensity.setFont(font)
            palette = QPalette(self.intensity.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.intensity.setPalette(palette)

            self.total_rays.setReadOnly(True)
            font = QFont(self.total_rays.font())
            font.setBold(True)
            self.total_rays.setFont(font)
            palette = QPalette(self.intensity.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_rays.setPalette(palette)

            self.total_good_rays.setReadOnly(True)
            font = QFont(self.total_good_rays.font())
            font.setBold(True)
            self.total_good_rays.setFont(font)
            palette = QPalette(self.total_good_rays.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_good_rays.setPalette(palette)

            self.total_lost_rays.setReadOnly(True)
            font = QFont(self.total_lost_rays.font())
            font.setBold(True)
            self.total_lost_rays.setFont(font)
            palette = QPalette(self.total_lost_rays.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_lost_rays.setPalette(palette)

            self.fwhm_h.setReadOnly(True)
            font = QFont(self.intensity.font())
            font.setBold(True)
            self.fwhm_h.setFont(font)
            palette = QPalette(self.fwhm_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.fwhm_h.setPalette(palette)

            if is_2d:
                self.fwhm_v.setReadOnly(True)
                font = QFont(self.fwhm_v.font())
                font.setBold(True)
                self.fwhm_v.setFont(font)
                palette = QPalette(self.fwhm_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.fwhm_v.setPalette(palette)

        def clear(self):
            self.intensity.setText("0.0")
            self.total_rays.setText("0")
            self.total_good_rays.setText("0")
            self.total_lost_rays.setText("0")
            self.fwhm_h.setText("0.0000")
            if hasattr(self, "fwhm_v"):  self.fwhm_v.setText("0.0000")

    class DetailedHistoWidget(QWidget):

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0):
            super(ShadowPlot.DetailedHistoWidget, self).__init__()

            self.plot_canvas = OasysPlotWindow(roi=False, control=False, position=True, logScale=False)
            self.plot_canvas.setDefaultPlotLines(True)
            self.plot_canvas.setActiveCurveColor(color='darkblue')
            self.plot_canvas.setMinimumWidth(590*x_scale_factor)
            self.plot_canvas.setMaximumWidth(590*x_scale_factor)

            self.info_box = ShadowPlot.InfoBoxWidget(x_scale_factor, y_scale_factor, is_2d=False)

            layout = QGridLayout()

            layout.addWidget(   self.info_box, 0, 1, 1, 1)
            layout.addWidget(self.plot_canvas, 0, 0, 1, 1)

            layout.setColumnMinimumWidth(0, 600*x_scale_factor)
            layout.setColumnMinimumWidth(1, 230*x_scale_factor)

            self.setLayout(layout)

        def plot_histo(self, beam, col, nolost, xrange, ref, title, xtitle, ytitle, nbins = 100, xum="", conv=1.0):

            ticket = beam.histo1(col, nbins=nbins, xrange=xrange, nolost=nolost, ref=ref)

            factor=ShadowPlot.get_factor(col, conv)

            if ref != 0 and not ytitle is None:  ytitle = ytitle + ' weighted by ' + ShadowPlot.get_shadow_label(ref)

            histogram = ticket['histogram_path']
            bins = ticket['bin_path']*factor

            self.plot_canvas.addCurve(bins, histogram, title, symbol='', color='blue', replace=True) #'+', '^', ','
            if not xtitle is None: self.plot_canvas.setGraphXLabel(xtitle)
            if not ytitle is None: self.plot_canvas.setGraphYLabel(ytitle)
            if not title is None: self.plot_canvas.setGraphTitle(title)
            self.plot_canvas.setDrawModeEnabled(True, 'rectangle')
            self.plot_canvas.setZoomModeEnabled(True)

            if ticket['fwhm'] == None: ticket['fwhm'] = 0.0

            n_patches = len(self.plot_canvas._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._backend.ax.patches.remove(self.plot_canvas._backend.ax.patches[n_patches-1])

            if not ticket['fwhm'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor, x_fwhm_f*factor
                y_fwhm   = max(histogram)*0.5

                self.plot_canvas._backend.ax.add_patch(FancyArrowPatch([x_fwhm_i, y_fwhm],
                                                          [x_fwhm_f, y_fwhm],
                                                          arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                          color='b',
                                                          linewidth=1.5))
            if min(histogram) < 0:
                self.plot_canvas.setGraphYLimits(min(histogram), max(histogram))
            else:
                self.plot_canvas.setGraphYLimits(0, max(histogram))

            self.plot_canvas.replot()

            self.info_box.intensity.setText("{:4.3f}".format(ticket['intensity']))
            self.info_box.total_rays.setText(str(ticket['nrays']))
            self.info_box.total_good_rays.setText(str(ticket['good_rays']))
            self.info_box.total_lost_rays.setText(str(ticket['nrays']-ticket['good_rays']))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm']*factor))
            self.info_box.label_h.setText("FWHM " + xum)

        def clear(self):
            self.plot_canvas.clear()
            self.info_box.clear()

    class DetailedPlotWidget(QWidget):
        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0):
            super(ShadowPlot.DetailedPlotWidget, self).__init__()

            self.x_scale_factor = x_scale_factor
            self.y_scale_factor = y_scale_factor

            self.plot_canvas = ImageView()

            self.plot_canvas.setColormap({"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256})
            self.plot_canvas.setMinimumWidth(590 * x_scale_factor)
            self.plot_canvas.setMaximumWidth(590 * y_scale_factor)

            self.info_box = ShadowPlot.InfoBoxWidget(x_scale_factor, y_scale_factor)

            layout = QGridLayout()

            layout.addWidget(             self.info_box, 0, 1, 2, 1)
            layout.addWidget(self.plot_canvas.toolBar(), 0, 0, 1, 1)
            layout.addWidget(          self.plot_canvas, 1, 0, 1, 1)

            layout.setColumnMinimumWidth(0, 600*x_scale_factor)
            layout.setColumnMinimumWidth(1, 230*x_scale_factor)

            self.setLayout(layout)

            self.plot_canvas.toolBar()

        def plot_xy(self, beam, var_x, var_y, title, xtitle, ytitle, xrange=None, yrange=None, nolost=1, nbins=100, xum="", yum="", conv=1.0, ref=23, is_footprint=False):

            matplotlib.rcParams['axes.formatter.useoffset']='False'

            ticket = beam.histo2(var_x, var_y, nbins=nbins, xrange=xrange, yrange=yrange, nolost=nolost, ref=ref)

            if is_footprint:
                factor1 = 1.0
                factor2 = 1.0
            else:
                factor1=ShadowPlot.get_factor(var_x, conv)
                factor2=ShadowPlot.get_factor(var_y, conv)

            xx = ticket['bin_h_edges']
            yy = ticket['bin_v_edges']

            xmin, xmax = xx.min(), xx.max()
            ymin, ymax = yy.min(), yy.max()

            origin = (xmin*factor1, ymin*factor2)
            scale = (abs((xmax-xmin)/nbins)*factor1, abs((ymax-ymin)/nbins)*factor2)

            # PyMCA inverts axis!!!! histogram must be calculated reversed
            data_to_plot = []
            for y_index in range(0, nbins):
                x_values = []
                for x_index in range(0, nbins):
                    x_values.append(ticket['histogram'][x_index][y_index])

                data_to_plot.append(x_values)

            self.plot_canvas.setImage(numpy.array(data_to_plot), origin=origin, scale=scale)

            if xtitle is None: xtitle=ShadowPlot.get_shadow_label(var_x)
            if ytitle is None: ytitle=ShadowPlot.get_shadow_label(var_y)

            self.plot_canvas.setGraphXLabel(xtitle)
            self.plot_canvas.setGraphYLabel(ytitle)
            self.plot_canvas.setGraphTitle(title)

            self.plot_canvas._histoHPlot.setGraphYLabel('Frequency')

            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._backend.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot.setGraphXLabel('Frequency')

            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._backend.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            if ticket['fwhm_h'] == None: ticket['fwhm_h'] = 0.0
            if ticket['fwhm_v'] == None: ticket['fwhm_v'] = 0.0

            n_patches = len(self.plot_canvas._histoHPlot._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoHPlot._backend.ax.patches.remove(self.plot_canvas._histoHPlot._backend.ax.patches[n_patches-1])

            if not ticket['fwhm_h'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates_h']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor1, x_fwhm_f*factor1
                y_fwhm = max(ticket['histogram_h']) * 0.5

                self.plot_canvas._histoHPlot._backend.ax.add_patch(FancyArrowPatch([x_fwhm_i, y_fwhm],
                                                                     [x_fwhm_f, y_fwhm],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='b',
                                                                     linewidth=1.5))

            n_patches = len(self.plot_canvas._histoVPlot._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoVPlot._backend.ax.patches.remove(self.plot_canvas._histoVPlot._backend.ax.patches[n_patches-1])

            if not ticket['fwhm_v'] == 0.0:
                y_fwhm_i, y_fwhm_f = ticket['fwhm_coordinates_v']
                y_fwhm_i, y_fwhm_f = y_fwhm_i*factor2, y_fwhm_f*factor2
                x_fwhm = max(ticket['histogram_v']) * 0.5

                self.plot_canvas._histoVPlot._backend.ax.add_patch(FancyArrowPatch([x_fwhm, y_fwhm_i],
                                                                     [x_fwhm, y_fwhm_f],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='r',
                                                                     linewidth=1.5))

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()
            self.plot_canvas.replot()

            self.info_box.intensity.setText("{:4.3f}".format(ticket['intensity']))
            self.info_box.total_rays.setText(str(ticket['nrays']))
            self.info_box.total_good_rays.setText(str(ticket['good_rays']))
            self.info_box.total_lost_rays.setText(str(ticket['nrays']-ticket['good_rays']))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm_h'] * factor1))
            self.info_box.fwhm_v.setText("{:5.4f}".format(ticket['fwhm_v'] * factor2))
            self.info_box.label_h.setText("FWHM " + xum)
            self.info_box.label_v.setText("FWHM " + yum)

        def clear(self):
            self.plot_canvas.clear()

            self.plot_canvas._histoHPlot.clear()
            self.plot_canvas._histoVPlot.clear()

            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._backend.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._backend.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoHPlot.setGraphYLabel('Frequency')
            self.plot_canvas._histoVPlot.setGraphXLabel('Frequency')

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()

            self.info_box.clear()

    #########################################################################################

    @classmethod
    def plotxy_preview(cls, plot_window, beam, var_x, var_y, nolost=0, title='PLOTXY', xtitle=None, ytitle=None, conv=1.0, is_footprint=False):

        matplotlib.rcParams['axes.formatter.useoffset']='False'

        col1 = beam.getshonecol(var_x, nolost=nolost)
        col2 = beam.getshonecol(var_y, nolost=nolost)

        if is_footprint:
            factor1 = 1.0
            factor2 = 1.0
        else:
            factor1 = ShadowPlot.get_factor(var_x, conv)
            factor2 = ShadowPlot.get_factor(var_y, conv)

        if xtitle is None: xtitle=ShadowPlot.get_shadow_label(var_x)
        if ytitle is None: ytitle=ShadowPlot.get_shadow_label(var_y)

        plot_window.addCurve(col1*factor1, col2*factor2, title, symbol='.', color='blue', replace=True) #'+', '^', ','

        if not xtitle is None: plot_window.setGraphXLabel(xtitle)
        if not ytitle is None: plot_window.setGraphYLabel(ytitle)
        if not title is None: plot_window.setGraphTitle(title)
        plot_window.setDrawModeEnabled(True, 'rectangle')
        plot_window.setZoomModeEnabled(True)

    @classmethod
    def plot_histo_preview(cls, plot_window, beam, col, nolost, ref, title, xtitle, ytitle, conv=1.0):

        matplotlib.rcParams['axes.formatter.useoffset']='False'

        factor=ShadowPlot.get_factor(col, conv)

        ticket = beam.histo1(col, nbins=100, xrange=None, nolost=nolost, ref=ref)

        if ref != 0 and not ytitle is None:  ytitle = ytitle + ' weighted by ' + ShadowPlot.get_shadow_label(ref)

        histogram = ticket['histogram_path']
        bins = ticket['bin_path']*factor

        plot_window.addCurve(bins, histogram, title, symbol='', color='blue', replace=True) #'+', '^', ','
        if not xtitle is None: plot_window.setGraphXLabel(xtitle)
        if not ytitle is None: plot_window.setGraphYLabel(ytitle)
        if not title is None: plot_window.setGraphTitle(title)
        plot_window.setDrawModeEnabled(True, 'rectangle')
        plot_window.setZoomModeEnabled(True)
        if min(histogram) < 0:
            plot_window.setGraphYLimits(min(histogram), max(histogram))
        else:
            plot_window.setGraphYLimits(0, max(histogram))
        plot_window.replot()

    @classmethod
    def get_factor(cls, var, conv):
        factor = 1.0

        if ShadowPlot._is_conversione_active:
            if var == 1 or var == 2 or var == 3:
                factor = 1e4*conv # cm to micron
            elif var == 4 or var == 5 or var == 6:
                factor = 1e6 # rad to urad

        return factor

    @classmethod
    def get_shadow_label(cls, var):
        return (stp.getLabel(var-1))[0]

class ShadowPreProcessor:

    @classmethod
    def read_surface_error_file(cls, filename):
        file = open(congruence.checkFile(filename), "r")

        rows = file.readlines()

        dimensions = rows[0].split()
        n_x = int(dimensions[0])
        n_y = int(dimensions[1])

        if n_x > 500:
            raise Exception("Malformed file: maximum allowed point in X direction is 500")

        x_coords = numpy.zeros(0)
        y_coords = numpy.zeros(0)
        z_values = numpy.zeros((n_x, n_y))


        index = 1
        dim_y_row = len(rows[index].split())
        is_ycoord = True
        first_x_row_index = 0

        while(is_ycoord):
            y_values = rows[index].split()

            if len(y_values) == dim_y_row:
                for y_value in y_values:
                    y_coords = numpy.append(y_coords, float(y_value))
            else:
                first_x_row_index = index
                is_ycoord = False

            index +=1

        first_x_row = rows[first_x_row_index].split()

        if len(first_x_row) == 2:
            x_index = 0
            z_index = 0

            for index in range(first_x_row_index, len(rows)):
                if z_index == 0:
                    values = rows[index].split()
                    x_coords = numpy.append(x_coords, float(values[0]))
                    z_value = float(values[1])
                else:
                    z_value = float(rows[index])

                z_values[x_index, z_index] = z_value
                z_index += 1

                if z_index == n_y:
                    x_index += 1
                    z_index = 0
        else:
            x_rows = []

            for index in range(2, len(rows)):

                x_row = rows[index].split("\t")

                if len(x_row) != 1 + n_y:
                    x_row = rows[index].split()

                if len(x_row) != 1 + n_y:
                    raise Exception("Malformed file: check format")

                x_rows.append(x_row)

            for x_index in range(0, len(x_rows)):
                x_coords = numpy.append(x_coords, float(x_rows[x_index][0]))

                for z_index in range(0, len(x_rows[x_index]) - 1):
                    z_value = float(x_rows[x_index][z_index + 1])

                    z_values[x_index, z_index] = z_value

        return x_coords, y_coords, z_values


class ShadowMath:

    @classmethod
    def gaussian_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)
        y_norm = y/sum(y)

        mean = sum(x*y_norm)
        sigma = numpy.sqrt(sum(y_norm*(x-mean)**2)/len(x))
        amplitude = max(y)

        parameters, covariance_matrix = optimize.curve_fit(ShadowMath.gaussian_function, x, y, p0 = [amplitude, mean, sigma])
        parameters.resize(4)
        parameters[3] = 2.355*parameters[2]# FWHM

        return parameters, covariance_matrix

    @classmethod
    def gaussian_function(cls, x, A, x0, sigma):
        return A*numpy.exp(-(x-x0)**2/(2*sigma**2))

    @classmethod
    def pseudovoigt_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)
        y_norm = y/sum(y)

        amplitude = max(data_y)
        mean = sum(x*y_norm)
        fwhm = numpy.sqrt(sum(y_norm*(x-mean)**2)/len(x))*2.355
        mixing = 0.1

        parameters, covariance_matrix = optimize.curve_fit(ShadowMath.pseudovoigt_function,
                                                           x, y,
                                                           p0 = [amplitude, mean, fwhm, mixing],
                                                           bounds = ([0.1*amplitude, 0.9*mean,  0.1*fwhm, 1e-3],
                                                                     [10.0*amplitude, 1.1*mean, 10.0*fwhm, 1.0]))

        return parameters, covariance_matrix

    @classmethod
    def pseudovoigt_function(cls, x, A, x0, fwhm, mixing):
        sigma = fwhm/2.355
        gamma = fwhm/2

        return A*(mixing*numpy.exp(-(x-x0)**2/(2*sigma**2)) + (1-mixing)*((gamma**2)/((x-x0)**2 + gamma**2)))

    @classmethod
    def caglioti_broadening_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)

        parameters, covariance_matrix = optimize.curve_fit(ShadowMath.caglioti_broadening_function,
                                                           x, y,
                                                           p0=[0.0001, 0.0001, 0.0001],
                                                           bounds = ([ -1.0, -1.0, -1.0],
                                                                     [ 1.0,  1.0,  1.0]))

        return parameters, covariance_matrix

    @classmethod
    def caglioti_broadening_function(cls, x, U, V, W):
        return numpy.sqrt(W + V * (numpy.tan(x*numpy.pi/360)) + U * (numpy.tan(x*numpy.pi/360))**2)

    @classmethod
    def caglioti_shape_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)

        parameters, covariance_matrix = optimize.curve_fit(ShadowMath.caglioti_shape_function,
                                                           x, y,
                                                           p0=[0.1, 0.0, 0.0],
                                                           bounds = ([ 0.0, -1.0, -1.0],
                                                                     [ 1.0,  1.0,  1.0]))

        return parameters, covariance_matrix

    @classmethod
    def caglioti_shape_function(cls, x, a, b, c):
        return a + b*(x*numpy.pi/360) + c*(x*numpy.pi/360)**2


    @classmethod
    def vectorial_product(cls, vector1, vector2):
        result = [0, 0, 0]

        result[0] = vector1[1]*vector2[2] - vector1[2]*vector2[1]
        result[1] = -(vector1[0]*vector2[2] - vector1[2]*vector2[0])
        result[2] = vector1[0]*vector2[1] - vector1[1]*vector2[0]

        return result

    @classmethod
    def scalar_product(cls, vector1, vector2):
        return vector1[0]*vector2[0] + vector1[1]*vector2[1] + vector1[2]*vector2[2]

    @classmethod
    def vector_modulus(cls, vector):
        return numpy.sqrt(cls.scalar_product(vector, vector))

    @classmethod
    def vector_multiply(cls, vector, constant):
        result = [0, 0, 0]

        result[0] = vector[0] * constant
        result[1] = vector[1] * constant
        result[2] = vector[2] * constant

        return result

    @classmethod
    def vector_divide(cls, vector, constant):
        result = [0, 0, 0]

        result[0] = vector[0] / constant
        result[1] = vector[1] / constant
        result[2] = vector[2] / constant

        return result

    @classmethod
    def vector_normalize(cls, vector):
        return cls.vector_divide(vector, cls.vector_modulus(vector))

    @classmethod
    def vector_sum(cls, vector1, vector2):
        result = [0, 0, 0]

        result[0] = vector1[0] + vector2[0]
        result[1] = vector1[1] + vector2[1]
        result[2] = vector1[2] + vector2[2]

        return result

    @classmethod
    def vector_difference(cls, vector1, vector2):
        result = [0, 0, 0]

        result[0] = vector1[0] - vector2[0]
        result[1] = vector1[1] - vector2[1]
        result[2] = vector1[2] - vector2[2]

        return result

    ##########################################################################
    # Rodrigues Formula:
    #
    # rotated = vector * cos(rotation_angle) + 
    #           (rotation_axis x vector) * sin(rotation_angle) + 
    #           rotation_axis*(rotation_axis . vector)(1 - cos(rotation_angle))
    #
    # rotation_angle in radians
    #
    ##########################################################################
    @classmethod
    def vector_rotate(cls, rotation_axis, rotation_angle, vector):
        result_temp_1 = ShadowMath.vector_multiply(vector, numpy.cos(rotation_angle))
        result_temp_2 = ShadowMath.vector_multiply(ShadowMath.vectorial_product(rotation_axis, vector),
                                                   numpy.sin(rotation_angle))
        result_temp_3 = ShadowMath.vector_multiply(rotation_axis,
                                                   ShadowMath.scalar_product(rotation_axis, vector)) * (1 - numpy.cos(rotation_angle))

        result = ShadowMath.vector_sum(result_temp_1,
                                       ShadowMath.vector_sum(result_temp_2, result_temp_3))
        return result

    @classmethod
    def point_distance(cls, point1, point2):
        return cls.vector_modulus(cls.vector_difference(point1, point2))

class ShadowPhysics:

    ######################################
    # FROM NIST
    codata_h = numpy.array(6.62606957e-34)
    codata_ec = numpy.array(1.602176565e-19)
    codata_c = numpy.array(299792458.0)
    ######################################

    A2EV = (codata_h*codata_c/codata_ec)*1e+10
    K2EV = 2*numpy.pi/(codata_h*codata_c/codata_ec*1e+2)

    @classmethod
    def getWavelengthFromShadowK(cls, k_mod): # in cm
        return (2*numpy.pi/k_mod)*1e+8 # in Angstrom

    @classmethod
    def getShadowKFromWavelength(cls, wavelength): # in A
        return (2*numpy.pi/wavelength)*1e+8 # in cm

    @classmethod
    def getWavelengthFromEnergy(cls, energy): #in eV
        return cls.A2EV/energy # in Angstrom

    @classmethod
    def getEnergyFromWavelength(cls, wavelength): # in Angstrom
        return cls.A2EV/wavelength # in eV

    @classmethod
    def getEnergyFromShadowK(cls, k_mod): # in cm
        return  k_mod/cls.K2EV # in eV

    @classmethod
    def getShadowKFromEnergy(cls, energy): # in A
        return cls.K2EV*energy # in cm

    @classmethod
    def calculateBraggAngle(cls, wavelength, h, k, l, a):

        # lambda = 2 pi / |k| = 2 d sen(th)
        #
        # sen(th) = lambda / (2  d)
        #
        # d = a / sqrt(h^2 + k^2 + l^2)
        #
        # sen(th) = (sqrt(h^2 + k^2 + l^2) * lambda)/(2 a)

        theta_bragg = -1

        argument = (wavelength*numpy.sqrt(h**2+k**2+l**2))/(2*a)

        if argument <=1:
            result = numpy.arcsin(argument)

            if result > 0:
                theta_bragg = result

        return theta_bragg

    @classmethod
    def checkCompoundName(cls, compound_name):
        if compound_name is None: raise Exception("Compound Name is Empty")
        if str(compound_name.strip()) == "": raise Exception("Compound Name is Empty")

        compound_name = compound_name.strip()

        try:
            xraylib.CompoundParser(compound_name)
            return compound_name
        except:
            raise Exception("Compound Name is not correct")

    @classmethod
    def getMaterialDensity(cls, material_name):
        if material_name is None: return 0.0
        if str(material_name.strip()) == "": return 0.0

        try:
            compoundData = xraylib.CompoundParser(material_name)

            if compoundData["nElements"] == 1:
                return xraylib.ElementDensity(compoundData["Elements"][0])
            else:
                return 0.0
        except:
            return 0.0

    @classmethod
    def ConstatoBackgroundNoised(cls, constant_value=0, n_sigma=1.0, random_generator=random.Random()):
        sigma = numpy.sqrt(constant_value) # poisson statistic
        noise = (n_sigma*sigma)*random_generator.random()
        sign_marker = random_generator.random()

        if sign_marker > 0.5:
            return int(round(constant_value+noise, 0))
        else:
            return int(round(constant_value-noise, 0))

    @classmethod
    def Chebyshev(cls, n, x):
        if n==0: return 1
        elif n==1: return x
        else: return 2*x*cls.Chebyshev(n-1, x)-cls.Chebyshev(n-2, x)

    @classmethod
    def ChebyshevBackground(cls, coefficients=[0,0,0,0,0,0], twotheta=0):
        coefficients_set = range(0, len(coefficients))
        background = 0

        for index in coefficients_set:
            background += coefficients[index]*cls.Chebyshev(index, twotheta)

        return background

    @classmethod
    def ChebyshevBackgroundNoised(cls, coefficients=[0,0,0,0,0,0], twotheta=0.0, n_sigma=1.0, random_generator=random.Random()):
        background = cls.ChebyshevBackground(coefficients, twotheta)
        sigma = numpy.sqrt(background) # poisson statistic

        noise = (n_sigma*sigma)*random_generator.random()
        sign_marker = random_generator.random()

        if sign_marker > 0.5:
            return int(round(background+noise, 0))
        else:
            return int(round(background-noise, 0))

    @classmethod
    def ExpDecay(cls, h, x):
      return numpy.exp(-h*x)

    @classmethod
    def ExpDecayBackground(cls, coefficients=[0,0,0,0,0,0], decayparams=[0,0,0,0,0,0], twotheta=0):
        coefficients_set = range(0, len(coefficients))
        background = 0

        for index in coefficients_set:
            background += coefficients[index]*cls.ExpDecay(decayparams[index], twotheta)

        return background

    @classmethod
    def ExpDecayBackgroundNoised(cls, coefficients=[0,0,0,0,0,0], decayparams=[0,0,0,0,0,0], twotheta=0, n_sigma=1, random_generator=random.Random()):
        background = cls.ExpDecayBackground(coefficients, decayparams, twotheta)
        sigma = numpy.sqrt(background) # poisson statistic

        noise = (n_sigma*sigma)*random_generator.random()
        sign_marker = random_generator.random()

        if sign_marker > 0.5:
            return int(round(background+noise, 0))
        else:
            return int(round(background-noise, 0))

import re
import time

class Properties(object):
    def __init__(self, props=None):
        self._props = {}
        self._origprops = {}
        self._keymap = {}
        self.othercharre = re.compile(r'(?<!\\)(\s*\=)|(?<!\\)(\s*\:)')
        self.othercharre2 = re.compile(r'(\s*\=)|(\s*\:)')
        self.bspacere = re.compile(r'\\(?!\s$)')

    def __str__(self):
        s='{'
        for key,value in self._props.items():
            s = ''.join((s,key,'=',value,', '))

        s=''.join((s[:-2],'}'))
        return s

    def __parse(self, lines):
        # Every line in the file must consist of either a comment
        # or a key-value pair. A key-value pair is a line consisting
        # of a key which is a combination of non-white space characters
        # The separator character between key-value pairs is a '=',
        # ':' or a whitespace character not including the newline.
        # If the '=' or ':' characters are found, in the line, even
        # keys containing whitespace chars are allowed.
        # A line with only a key according to the rules above is also
        # fine. In such case, the value is considered as the empty string.
        # In order to include characters '=' or ':' in a key or value,
        # they have to be properly escaped using the backslash character.

        # Some examples of valid key-value pairs:
        #
        # key     value
        # key=value
        # key:value
        # key     value1,value2,value3
        # key     value1,value2,value3 \
        #         value4, value5
        # key
        # This key= this value
        # key = value1 value2 value3

        # Any line that starts with a '#' is considered a comment
        # and skipped. Also any trailing or preceding whitespaces
        # are removed from the key/value.

        # This is a line parser. It parses the
        # contents like by line.

        lineno=0
        i = iter(lines)

        for line in i:
            lineno += 1
            line = line.strip()

            if not line: continue
            if line[0] == '#': continue

            sepidx = -1

            m = self.othercharre.search(line)
            if m:
                first, last = m.span()
                start, end = 0, first
                wspacere = re.compile(r'(?<![\\\=\:])(\s)')
            else:
                if self.othercharre2.search(line):
                    wspacere = re.compile(r'(?<![\\])(\s)')

                start, end = 0, len(line)

            m2 = wspacere.search(line, start, end)
            if m2:
                first, last = m2.span()
                sepidx = first
            elif m:
                first, last = m.span()
                sepidx = last - 1

            while line[-1] == '\\':
                nextline = i.next()
                nextline = nextline.strip()
                lineno += 1
                line = line[:-1] + nextline

            if sepidx != -1:
                key, value = line[:sepidx], line[sepidx+1:]
            else:
                key,value = line,''

            self.processPair(key, value)

    def processPair(self, key, value):
        oldkey = key
        oldvalue = value

        keyparts = self.bspacere.split(key)

        strippable = False
        lastpart = keyparts[-1]

        if lastpart.find('\\ ') != -1:
            keyparts[-1] = lastpart.replace('\\','')

        elif lastpart and lastpart[-1] == ' ':
            strippable = True

        key = ''.join(keyparts)
        if strippable:
            key = key.strip()
            oldkey = oldkey.strip()

        oldvalue = self.unescape(oldvalue)
        value = self.unescape(value)

        self._props[key] = value.strip()

        if self._keymap.__contains__(key):
            oldkey = self._keymap.get(key)
            self._origprops[oldkey] = oldvalue.strip()
        else:
            self._origprops[oldkey] = oldvalue.strip()
            self._keymap[key] = oldkey

    def escape(self, value):
        newvalue = value.replace(':','\:')
        newvalue = newvalue.replace('=','\=')

        return newvalue

    def unescape(self, value):
        newvalue = value.replace('\:',':')
        newvalue = newvalue.replace('\=','=')

        return newvalue

    def load(self, stream):
        if not hasattr(stream, 'read'):
            raise TypeError('Argument should be a file object!')
        if stream.mode != 'r':
            raise ValueError ('Stream should be opened in read-only mode!')

        try:
            lines = stream.readlines()
            self.__parse(lines)
        except IOError as e:
            raise e

    def getProperty(self, key):
        return self._props.get(key)

    def setProperty(self, key, value):
        if type(key) is str and type(value) is str:
            self.processPair(key, value)
        else:
            raise TypeError('both key and value should be strings!')

    def propertyNames(self):
        return self._props.keys()

    def list(self, out=sys.stdout):
        out.write('-- listing properties --\n')
        for key,value in self._props.items():
            out.write(''.join((key,'=',value,'\n')))

    def store(self, out, header=""):
        if out.mode[0] != 'w':
            raise ValueError('Steam should be opened in write mode!')

        try:
            out.write(''.join(('#',header,'\n')))
            tstamp = time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime())
            out.write(''.join(('#',tstamp,'\n')))
            for prop, val in self._origprops.items():
                out.write(''.join((prop,'=',self.escape(val),'\n')))

            out.close()
        except IOError as e:
            raise e

    def getPropertyDict(self):
        return self._props

    def __getitem__(self, name):
        return self.getProperty(name)

    def __setitem__(self, name, value):
        self.setProperty(name, value)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self._props,name):
                return getattr(self._props, name)

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from PyQt4.QtGui import QApplication, QVBoxLayout
from PyQt4.QtCore import QCoreApplication

class MathTextLabel(QWidget):
    def __init__(self, mathText, size=None, parent=None, **kwargs):
        QWidget.__init__(self, parent, **kwargs)

        l=QVBoxLayout(self)
        l.setContentsMargins(0,0,0,0)

        r,g,b,a=self.palette().base().color().getRgbF()

        self._figure=Figure(edgecolor=(r,g,b), facecolor=(r,g,b))
        self._canvas=FigureCanvas(self._figure)
        l.addWidget(self._canvas)

        self._figure.clear()

        if not size:
            size = QCoreApplication.instance().font().pointSize()

        text=self._figure.suptitle(
            mathText,
            x=0.0,
            y=1.0,
            horizontalalignment='left',
            verticalalignment='top',
            size=size)
        self._canvas.draw()

        (x0,y0),(x1,y1)=text.get_window_extent().get_points()
        w=x1-x0; h=y1-y0

        self._figure.set_size_inches(w/80, h/80)
        self.setFixedSize(w,h)



if __name__ == "__main__":

    #print(congruence.checkFileName("pippo.dat"))
    #print(congruence.checkFileName("Files/pippo.dat"))
    #print(congruence.checkFileName("Files/pippo.dat"))
    #print(congruence.checkFileName("/Users/labx/Desktop/pippo.dat"))

    s = " 5   8095683980.2420149       3.34799999999999994E-008"

    print(s.strip().split(" "))


    print("Bragg")
    ShadowCongruence.checkBraggFile("/Users/labx/Oasys/bragg.dat")
    print("PreRefl")
    ShadowCongruence.checkPreReflFile("/Users/labx/Oasys/reflec.dat")
    print("PreMLayer")
    ShadowCongruence.checkPreMLayerFile("/Users/labx/Oasys/mlayer.dat")

    #ShadowCongruence.checkXOPDiffractionProfileFile("/Users/labx/Oasys/mlayer.dat")

    '''
    print(ShadowPhysics.A2EV)

    print(ShadowPhysics.Chebyshev(4, 21))
    print(ShadowPhysics.Chebyshev(0, 35))

    coefficients = [5.530814e+002, 2.487256e+000, -2.004860e-001, 2.246427e-003, -1.044517e-005, 1.721576e-008]
    random_generator=random.Random()

    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 10, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 11, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 12, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 13, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 14, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 15, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 16, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 17, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 18, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 19, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 20, random_generator=random_generator))
    '''
    '''
    import matplotlib.pyplot as plt

    x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file("/Users/labx/Oasys/mirror.dat")

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    X, Y = numpy.meshgrid(x_coords, y_coords)
    surf = ax.plot_surface(X, Y, z_values.T, rstride=1, cstride=1, cmap=cm.coolwarm,
            linewidth=0, antialiased=False)
    #ax.set_zlim(-1.01, 1.01)

    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show()

    app = QApplication(sys.argv)

    widget = QWidget()
    widget.setLayout(QVBoxLayout())

    figure = Figure(figsize=(100, 100))
    figure.patch.set_facecolor('white')

    axis = figure.add_subplot(111, projection='3d')

    axis.set_xlabel("X (cm)")
    axis.set_ylabel("Y (cm)")
    axis.set_zlabel("Z (cm)")

    figure_canvas = FigureCanvasQTAgg(figure)
    widget.layout().addWidget(figure_canvas)
    figure_canvas.setFixedWidth(500)
    figure_canvas.setFixedHeight(450)

    x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file("/Users/labx/Oasys/mirror.dat")

    x_to_plot, y_to_plot = numpy.meshgrid(x_coords, y_coords)

    axis.plot_surface(x_to_plot, y_to_plot, z_values.T,
                      rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

    figure_canvas.draw()
    figure_canvas.show()
    widget.show()

    app.exec()
    '''
