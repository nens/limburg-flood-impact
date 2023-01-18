import os
import sys

from qgis.core import QgsApplication
from qgis.gui import QgisInterface

from qgis.PyQt.QtGui import (QIcon)

try:
    import limburg_flood_impact
except ModuleNotFoundError:
    # if required modules are not available on system, let's use the versions that we package
    this_dir = os.path.dirname(os.path.realpath(__file__))
    deps_dir = os.path.join(this_dir, 'deps')
    if os.path.exists(deps_dir):
        for f in os.listdir(os.path.join(deps_dir)):
            sys.path.append(os.path.join(deps_dir, f))

from .processing.limburg_flood_impact_provider import LimburgFloodImpactProvider


class LimburgFloodImpactPlugin():

    def __init__(self, iface):

        self.iface: QgisInterface = iface
        self.provider = LimburgFloodImpactProvider()

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
