from pyproj import enums, database, Transformer, CRS
import pandas as pd
from shapely.geometry import Polygon, Point
import requests
import sys

def getProjectionTypes():
    """
    A simple function to obtain an overview of different types of CRS

    Returns
    -------
    List
        A list of different types of CRS.

    """
    return dir(enums.PJType)
    

def geocode(locStr):
    """
    Function that retreives a list of coordinates for a given descriptive location. This function uses the Nonminatim API for geocoding.

    Parameters
    ----------
    locStr : String
        Description of the spatial location.

    Returns
    -------
    refList : List of Points (shapely.geometry)
        A list of coordinates for a given descriptive location.

    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {"format": "json", "q": locStr}
    r = requests.get(url, params=params)
    locList = r.json()
    refList = []
    for loc in locList:
        refLAT, refLON = (float(loc['lat']), float(loc['lon']))
        refPoint = Point(refLON, refLAT)
        refList.append(refPoint)
    print("Obtained coordinates for %s" % locStr)
    return refList

def getAuthorityNames():
    """
    A simple function to obtain an overview of implemented authorities in PyProj.

    Returns
    -------
    List
        A list of authorities (string).

    """
    return database.get_authorities()
    
def getCandidateList(refPoint, buffer=0):
    """
    Function that generates a list of all CRS in the database that intersect with the given point. The selection is based on the intersection of this point with the boundaries of the "area of use" of all available CRS.

    Parameters
    ----------
    refPoint : Point (shapely.geometry)
        A point that contains the geographic coordinates of the estimated location of the study area (in LON, LAT).
    buffer : Integer, optional
        Optional value that represents a buffer distance around the given point. To be used when the estimated location cannot be defined with great certainty. The default is 0.

    Returns
    -------
    candidates : List
        A list of pyproj.CRS objects corresponding with the CRS intersecting the given reference point.

    """
    candidates = []
    epsgList = database.get_codes('EPSG', 'PROJECTED_CRS')
    if buffer > 0 and buffer < 1:
        epsgList = database.get_codes('EPSG', 'GEOGRAPHIC_CRS')
    for epsg in epsgList:
        crs = CRS.from_epsg(epsg)
        crsBounds = crs.area_of_use.bounds
        crsBoundsPolygon = Polygon(((crsBounds[0], crsBounds[1]),
            (crsBounds[2], crsBounds[1]), (crsBounds[2], crsBounds[3]),
            (crsBounds[0], crsBounds[3])))
        if crsBoundsPolygon.intersects(refPoint):
            candidates.append(crs)
    print("Prepared list of candidate CRS for [%.3f, %.3f]" % (refPoint.y, refPoint.x))
    return candidates

def evaluateCRSList(candidates, givenPoint, refPoint):
    """
    For each CRS in the list, the reprojected coordinates of the reference point are calculated. Then, the distance between the given point with unknown CRS and the reprojected reference point is calculated. This function results in a sorted Pandas DataFrame with reference to the CRS and the accompanying distance.

    Parameters
    ----------
    candidates : List
        A list of pyproj.CRS objects corresponding with the CRS intersecting the given reference point.
    givenPoint : Point (shapely.geometry)
        A point with given coordinates but with an unknown CRS.
    refPoint : Point (shapely.geometry)
        A point that contains the geographic coordinates of the estimated location of the study area (in LON, LAT).

    Returns
    -------
    assessmentDf : DataFrame (pandas)
        A Pandas DataFrame containing a distance for each CRS:
            - 'crs': pyproj.CRS-object, the CRS itself
            - 'name': string, the name of the CRS
            - 'dist': float, the distance between the projected reference point and the given point (in m).

    """
    assessment = []
    for candidate in candidates:
        try:
            refCRS = CRS.from_epsg(4326)
            if candidate is not refCRS:
                transformer = Transformer.from_crs(refCRS, candidate, always_xy=True)
                calcX, calcY = transformer.transform(refPoint.x, refPoint.y)
                calcPoint = Point(calcX, calcY)
            else:
                calcPoint = refPoint
            dist = givenPoint.distance(calcPoint)
            assessment.append({'crs': candidate, 'name': candidate.name, 'dist': dist})
        except:
            continue
    assessmentDf = pd.DataFrame.from_records(assessment)
    assessmentDf = assessmentDf.sort_values('dist')
    print("Calculated distances for candidate CRS for [%.3f, %.3f]" % (refPoint.y, refPoint.x))
    return assessmentDf
