__author__ = "Lutra Consulting Ltd"
__date__ = "2023-01-12"
__copyright__ = "(C) 2023 by Lutra Consulting Ltd"

from .limburg_flood_impact_plugin import LimburgFloodImpactPlugin


def classFactory(iface):
    return LimburgFloodImpactPlugin(iface)
