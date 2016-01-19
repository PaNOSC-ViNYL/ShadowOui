import sys
import time

from PyQt4 import QtGui
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog


from orangecontrib.shadow.util.shadow_objects import ShadowBeam, EmittingStream, TTYGrabber
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui import ow_automatic_element


class Histogram(ow_automatic_element.AutomaticElement):

    name = "Histogram"
    description = "Display Data Tools: Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 2
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 640

    want_main_area=1
    plot_canvas=None
    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(10)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    weight_column_index = Setting(23)

    number_of_bins=Setting(100)

    title=Setting("Energy")

    keep_result=Setting(0)

    def __init__(self):
        super().__init__()

        gui.button(self.controlArea, self, "Refresh", callback=self.plot_results, height=45)
        gui.separator(self.controlArea, 10)

        tabs_setting = gui.tabWidget(self.controlArea)
        tabs_setting.setFixedWidth(410)

        # graph tab
        tab_set = oasysgui.createTabPage(tabs_setting, "Plot Settings")
        tab_gen = oasysgui.createTabPage(tabs_setting, "Histogram Settings")

        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=110)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"],
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", width=390, height=110)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", width=390, height=110)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        general_box = oasysgui.widgetBox(tab_set, "General Settings", addSpace=True, orientation="vertical", height=250)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="Column", labelWidth=80,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: Es X",
                                            "8: Es Y",
                                            "9: Es Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase s",
                                            "15: Phase p",
                                            "16: Ep X",
                                            "17: Ep Y",
                                            "18: Ep Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X^2 + Y^2 + Z^2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |Es| + |Ep|",
                                            "23: Total Intensity = |Es|^2 + |Ep|^2",
                                            "24: S Intensity = |Es|^2",
                                            "25: P Intensity = |Ep|^2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |Es|^2 + |Ep|^2",
                                            "31: S1-stokes = |Es|^2 - |Ep|^2",
                                            "32: S2-stokes = 2|Es||Ep|cos(Phase s-Phase p)",
                                            "33: S3-stokes = 2|Es||Ep|sin(Phase s-Phase p)",
                                     ],
                                     sendSelectedValue=False, orientation="horizontal")

        self.weight_column = gui.comboBox(general_box, self, "weight_column_index", label="Weight", labelWidth=80,
                                         items=["0: No Weight",
                                                "1: X",
                                                "2: Y",
                                                "3: Z",
                                                "4: X'",
                                                "5: Y'",
                                                "6: Z'",
                                                "7: Es X",
                                                "8: Es Y",
                                                "9: Es Z",
                                                "10: Ray Flag",
                                                "11: Energy",
                                                "12: Ray Index",
                                                "13: Optical Path",
                                                "14: Phase s",
                                                "15: Phase p",
                                                "16: Ep X",
                                                "17: Ep Y",
                                                "18: Ep Z",
                                                "19: Wavelength",
                                                "20: R = sqrt(X^2 + Y^2 + Z^2)",
                                                "21: Theta (angle from Y axis)",
                                                "22: Magnitude = |Es| + |Ep|",
                                                "23: Total Intensity = |Es|^2 + |Ep|^2",
                                                "24: S Intensity = |Es|^2",
                                                "25: P Intensity = |Ep|^2",
                                                "26: |K|",
                                                "27: K X",
                                                "28: K Y",
                                                "29: K Z",
                                                "30: S0-stokes = |Es|^2 + |Ep|^2",
                                                "31: S1-stokes = |Es|^2 - |Ep|^2",
                                                "32: S2-stokes = 2|Es||Ep|cos(Phase s-Phase p)",
                                                "33: S3-stokes = 2|Es||Ep|sin(Phase s-Phase p)",
                                         ],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "x_range", label="X Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)
        self.xrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)

        oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "X min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "X max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="horizontal", height=80, width=395)

        gui.checkBox(incremental_box, self, "keep_result", "Keep Result")
        gui.button(incremental_box, self, "Clear", callback=self.clearResults)

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=70, width=395)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins", "Number of Bins", labelWidth=250, valueType=int, orientation="horizontal")

        main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(main_tabs, "Plots")
        out_tab = gui.createTabPage(main_tabs, "Output")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.shadow_output.setFixedHeight(600)
        self.shadow_output.setFixedWidth(600)

    def clearResults(self):
        if ConfirmDialog.confirmed(parent=self):
            self.input_beam = ShadowBeam()
            self.plot_canvas.clear()

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def replace_fig(self, beam, var, x_range, title, xtitle, ytitle, xum):
        if self.plot_canvas is None:
            self.plot_canvas = ShadowPlot.DetailedHistoWidget(y_scale_factor=1.14)
            self.image_box.layout().addWidget(self.plot_canvas)

        try:
            self.plot_canvas.plot_histo(beam, var, 1, x_range, self.weight_column_index, title, xtitle, ytitle, nbins=self.number_of_bins, xum=xum, conv=self.workspace_units_to_cm)
        except Exception:
            raise Exception("Data not plottable: No good rays or bad content")

    def plot_histo(self, var_x, title, xtitle, ytitle, xum):
        beam_to_plot = self.input_beam._beam

        if self.image_plane == 1:
            new_shadow_beam = self.input_beam.duplicate(history=False)
            dist = 0.0

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                if historyItem is None: image_plane = 0.0
                elif self.input_beam._oe_number == 0: image_plane = 0.0
                else: image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                dist = self.image_plane_new_position - image_plane

            new_shadow_beam._beam.retrace(dist)

            beam_to_plot = new_shadow_beam._beam

        if self.x_range == 1:
            if self.x_range_min >= self.x_range_max: raise Exception("X range min cannot be greater or equal than X range max")

            factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)

            x_range = [self.x_range_min/factor1, self.x_range_max/factor1]
        else:
            x_range = None

        self.replace_fig(beam_to_plot, var_x, x_range, title, xtitle, ytitle, xum)

    def plot_results(self):
        #self.error(self.error_id)

        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                self.number_of_bins = congruence.checkPositiveNumber(self.number_of_bins, "Number of Bins")

                auto_title = self.x_column.currentText().split(":", 2)[1]
                xum = auto_title + " "

                self.title = auto_title

                x = self.x_column_index + 1

                if x == 1 or x == 2 or x == 3:
                    xum = xum + "[" + u"\u03BC" + "m]"
                    auto_title = auto_title + " [$\mu$m]"
                elif x == 4 or x == 5 or x == 6:
                    xum = xum + "[" + u"\u03BC" + "rad]"
                    auto_title = auto_title + " [$\mu$rad]"
                elif x == 11:
                    xum = xum + "[eV]"
                    auto_title = auto_title + " [eV]"
                elif x == 13:
                    xum = xum + " [" + self.workspace_units_label + "]"
                    auto_title = auto_title + " [" + self.workspace_units_label + "]"
                elif x == 14:
                    xum = xum + "[rad]"
                    auto_title = auto_title + " [rad]"
                elif x == 15:
                    xum = xum + "[rad]"
                    auto_title = auto_title + " [rad]"
                elif x == 19:
                    xum = xum + "[Å]"
                    auto_title = auto_title + " [Å]"
                elif x == 20:
                    xum = xum + " [" + self.workspace_units_label + "]"
                    auto_title = auto_title + " [" + self.workspace_units_label + "]"
                elif x == 21:
                    xum = xum + "[rad]"
                    auto_title = auto_title + " [rad]"
                elif x >= 25 and x <= 28:
                    xum = xum + "[Å-1]"
                    auto_title = auto_title + " [Å-1]"

                self.plot_histo(x, title=self.title, xtitle=auto_title, ytitle="Number of Rays", xum=xum)

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram
        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtGui.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                if self.keep_result == 1 and not self.input_beam is None:
                    self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                else:
                    self.input_beam = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()
