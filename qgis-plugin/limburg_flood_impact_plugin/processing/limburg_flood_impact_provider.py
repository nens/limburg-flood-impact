# from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .tool_check_address import CheckAddressAlgorithm
from .tool_urban_rain import ClassifyUrbanRainAlgorithm
from .tool_rural_rain import ClassifyRuralRainAlgorithm
from .tool_area_wide_rain import ClassifyAreaWideRainAlgorithm
from .tool_combine_classification import CombineClassificationAlgorithm
from .tool_test_against_flood_protection_norm import TestAgainstFloodProtectionNormAlgorithm
from .tool_style_result import StyleResultAlgorithm


class LimburgFloodImpactProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def load(self) -> bool:
        return super().load()

    def loadAlgorithms(self):
        self.addAlgorithm(CheckAddressAlgorithm())
        self.addAlgorithm(CombineClassificationAlgorithm())
        self.addAlgorithm(ClassifyUrbanRainAlgorithm())
        self.addAlgorithm(ClassifyRuralRainAlgorithm())
        self.addAlgorithm(ClassifyAreaWideRainAlgorithm())
        self.addAlgorithm(TestAgainstFloodProtectionNormAlgorithm())
        self.addAlgorithm(StyleResultAlgorithm())

    def id(self):
        return "limburgfloodimpact"

    def name(self):
        return "Limburg Flood Impact"

    # def icon(self):
    #     path = get_icon_path("los_tools_icon.svg")
    #     return QIcon(path)
