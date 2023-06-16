import os
import sys

from qgis.core import QgsApplication
from qgis.gui import QgisInterface

try:
    import limburg_flood_impact
except ModuleNotFoundError:
    # if required modules are not available on system, let's use the versions that we package
    this_dir = os.path.dirname(os.path.realpath(__file__))
    deps_dir = os.path.join(this_dir, "deps")
    if os.path.exists(deps_dir):
        for f in os.listdir(os.path.join(deps_dir)):
            sys.path.append(os.path.join(deps_dir, f))

    # this configuration is to be used in debug mode, to develop the plugin and
    # to allow debugging in the python package code
    # from pathlib import Path
    # p = Path(__file__).parent.parent.parent / "python-package" / "src"
    # sys.path.append(p.as_posix())


from .processing.limburg_flood_impact_provider import LimburgFloodImpactProvider


class LimburgFloodImpactPlugin:
    def __init__(self, iface):
        self.iface: QgisInterface = iface
        self.provider = LimburgFloodImpactProvider()

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
