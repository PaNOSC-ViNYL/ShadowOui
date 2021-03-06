import sys
from PyQt5.QtWidgets import QApplication

from . import ow_optical_element


class PlaneElement(ow_optical_element.OpticalElement):

    ##########################################
    # BASIC SETTING
    ##########################################


    ##########################################

    def __init__(self, graphical_options=ow_optical_element.GraphicalOptions()):

        graphical_options.is_curved=False

        super().__init__(graphical_options)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = PlaneElement()
    ow.show()
    a.exec_()
    ow.saveSettings()