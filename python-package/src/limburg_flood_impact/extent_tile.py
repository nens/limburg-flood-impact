from __future__ import annotations

import typing
from dataclasses import dataclass
from pathlib import Path

from osgeo import gdal, ogr


@dataclass
class Extent:
    minX: float = 0
    maxX: float = 0
    minY: float = 0
    maxY: float = 0

    @classmethod
    def from_gdal_ds(cls, ds: gdal.Dataset):
        xmin, xpixel, _, ymax, _, ypixel = ds.GetGeoTransform()
        width, height = ds.RasterXSize, ds.RasterYSize
        xmax = xmin + width * xpixel
        ymin = ymax + height * ypixel

        return cls(xmin, xmax, ymin, ymax)

    def create_tiles(self, maxSize: float) -> typing.List[Extent]:
        currX = self.minX
        currY = self.minY

        tiles = []

        count = 1
        while currY < self.maxY:
            while currX < self.maxX:
                win_maxX = min(currX + maxSize, self.maxX)
                win_maxY = min(currY + maxSize, self.maxY)

                tiles.append(Extent(currX, win_maxX, currY, win_maxY))

                currX += maxSize
                count += 1

            currX = self.minX

            currY += maxSize

        return tiles

    def as_gdal_projWin(self) -> typing.List[float]:
        return [self.minX, self.maxY, self.maxX, self.minY]

    def buffer_by(self, size: float) -> None:
        self.minX = self.minX - size
        self.maxX = self.maxX + size
        self.minY = self.minY - size
        self.maxY = self.maxY + size

    def extract_from(self, ds: gdal.Dataset) -> gdal.Dataset:
        params = {"projWin": self.as_gdal_projWin()}

        raster_path = Path(ds.GetDescription())

        vsimem_path = f"/vsimem/{raster_path.stem}.tif"

        gdal.Translate(vsimem_path, ds, **params)

        return gdal.Open(vsimem_path)

    def as_geometry(self) -> ogr.Geometry:
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(self.minX, self.minY)
        ring.AddPoint(self.maxX, self.minY)
        ring.AddPoint(self.maxX, self.maxY)
        ring.AddPoint(self.minX, self.maxY)
        ring.AddPoint(self.minX, self.minY)

        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(ring)

        return polygon

    def as_spatial_filter(self) -> ogr.Geometry:
        return self.as_geometry()
