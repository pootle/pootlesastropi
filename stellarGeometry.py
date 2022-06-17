#!/usr/bin/python3
"""
Stellar Geometry provides classes and functions for handling and converting between astronomical
and other spherical coordinates.

Most angles can be defined in degrees, radians or hours:mins:secs, and can be retrieved in any of these
representations. 

Likewise formatted strings can be easily retrieved in any of the above units and in various forms 
using format...

most of the formulae and conversions here are based on:
    www.sohcahtoa.org.uk/kepler/altaz.html
     - or -
    http://star-www.st-and.ac.uk/~fv/webnotes/chapter7.htm

as well as many other places for some snippets.
"""
import math
from clockery import sidereal
from astroangles import latVal, lonVal, altVal, azVal, raVal, decVal, hourVal, motorVal

TWOPI=math.pi*2
HALFPI=math.pi/2
TWELFTHPI=math.pi/12

class twoCoords():
    """
    A base class for all the basic stuff needed to support the various representations / uses to follow
    """
    def __init__(self, **kwargs):
        for vn, vname, vclass in self.initVarInfo: 
            if vname in kwargs or vn in kwargs:
                vs, vt = (kwargs[vname], kwargs.get(vname+'as', 'd')) if vname in kwargs else (kwargs[vn], kwargs.get(vn+'as','d'))
                nv = vclass(vs,vt)
            else:
                nv=None
            setattr(self, vn, nv)
            setattr(self, vname, nv)
        if 'sources' in kwargs:
            self.setupfrom(kwargs['sources'])
        if getattr(self, self.initVarInfo[0][0], None) is None or getattr(self, self.initVarInfo[1][0], None) is None:
            raise TypeError("no value provided for %s" % _v2from)

    def setupfrom(self, sources):
        pass

    def __str__(self):
        """
        Return self as a nice string in ornery float format (degrees:mins:secs?) 
        """
        return self.strFormat.format(self.v1, self.v2)        

class earthLoc(twoCoords):
    """
    a location on the earths surface as latitude and longitude. Values are held in degrees and radians
    with lazy evaluation. Hour values are also available (degrees / 15)
    
    Provides attributes lat and lon.
    
    snowdon = earthLoc(53.068508,-4.076269)
            #creates an instance, by default floats are treated as degrees
    str(snowdon)
            # retrieves co-ordinates as string in deg:min:sec format
    snowdon.lat.rad
            # retrieves the latitude in radians
    snowdon.lon.hour
            # retrieves the longitude in hours            
    snowdon.lon.hour *=2
            # moves snowdon to twice as far from Greenwich meridian
    notsnowdon = sg.earthLoc(snowdon.lat.deg*-1, snowdon.lon.deg+180)
            # creates an antipode to snowdon
    str(notsnowdon)
            # shows the co-ordinates

    __init__:
        supply latitude and longitude as signed floats or strings, or as latVal or longVal as appropriate.

        See those classes for details of string parsing.
            latitiude - positive for North, negative for south. 
            longitude - positive for East, negative for west.

            latas - defines if latitude is to be interpreted as degrees ('d'), radians('r') or hours ('h').
                    overridden if latitude is a string and contains one of these characters

            lonas - defines if longitude is to be interpreted as degrees ('d'), radians('r') or hours ('h').
                    overridden if longitude is a string and contains one of these characters            
    """
    initVarInfo = (('lat', 'v1', latVal),('lon', 'v2', lonVal))

    strFormat='earthLoc: {0:dx;}, {1:dx;}'

class observedCoord(twoCoords):
    """
    a (sky) location in alt / az co-ordinates. Values are held in degrees and radians
    with lazy evaluation. Hour values are also available (degrees / 15)
    
    Provides attributes alt and az:
        alt - positive for above the horizon
        az - positive for North of equatorial plane

    for __init__:   
        supply 'alt' and 'az' as signed floats or strings, or as altVal or azVal as appropriate.
        'altas' and 'azas' can be used to define the units for 'alt' and 'as' - both default to 'd'.

        See altVal and azVal classes for details of string parsing.
        
        Alternatively pass a tuple containing a localEquatorial and a (latVal or earthLoc) and 
        the alt,az values are calculated from their contents.
    """
   
    initVarInfo = (('alt', 'v1', altVal),('az', 'v2', azVal))

    def setupfrom(self, sources):
        indec = None
        inha=None
        inlat=None
        for anob in sources:
            if isinstance(anob,localEquatorial):
                indec = anob.dec.rad
                inha = anob.hour.rad
                if not inlat is None:
                    break
            if isinstance(anob,latVal):
                inlat = anob.rad
                if not inha is None and not indec is None:
                    break
            if isinstance(anob,earthLoc):
                inlat = anob.lat.rad
                if not inha is None and not indec is None:
                    break
        else:
            raise KeyError("localEquatorial and latitude source not found in params")
        alt, az  =  mapCoords(indec, inlat, inha)
        self.alt = altVal(alt,'r')
        self.v1 = self.alt
        self.az = azVal(az,'r')
        self.v2 = self.az
    
    strFormat='observedCoord: {0:dx;}, {1:dx;}'

#    def stellarCoord(self, lst, latLon):
#        """ THIS ISNT PROVEN YET
#        Convert horizon coordinates to equatorial given the local sidereal time and observer location
#        """
#        dec, hourRad = mapCoords(self.alt.rad, latLon.lat.rad, self.az.rad)

#        if isinstance(lst,sidereal):
#            ra = ((lst._hours - hourRad / TWELFTHPI) % 24.0 ) * TWELFTHPI
#        else:
#            ra = ((lst.hours - hourRad / TWELFTHPI) % 24.0 ) * TWELFTHPI

#        return stellarCoord(ra, dec, raas='r', decas='r')

class localEquatorial(twoCoords):
    """
    A sky location in ra/dec like format, but using local time and location so no account is taken
    of latitude or time.
    
    Values are held in degrees and radians with lazy evaluation. 
    Hour values are also available (degrees / 15)
    
    Provides attributes hour and dec:
        hour - position from meridian, 20 is west, 350 is east
        dec - positive for North of equatorial plane

    __init__:
        supply 'hour' and 'dec' as floats or strings, or as hourVal and decVal.
        'houras' and 'decas' can be used to define the units for 'hour' and 'dec' - both default to 'd'.

        Alternatively pass a tuple containing an observedCoord and a (latVal or earthLoc) and 
        the hour and, dec values are calculated from their contents.
        
        Similarly proper stellar coordinates (right ascension / declination) together with a sidereal clock can be used.

        See hourVal and decVal classes for details of string parsing.
    """
    initVarInfo = (('hour', 'v1', hourVal),('dec', 'v2', decVal))    

    strFormat='localEquatorial: {0:dx;}, {1:dx;}'
    
    def setupfrom(self, sources):
        inalt = None
        inaz=None
        inlat=None
        inra=None
        indec=None
        insrtdeg=None
        for anob in sources:
            if isinstance(anob,observedCoord):
                inalt = anob.alt.rad
                inaz = anob.az.rad
                if not inlat is None:
                    self.setupfromaltaz(inalt, inlat, inaz)
                    break
            if isinstance(anob,latVal):
                inlat = anob.rad
                if not inalt is None and not inaz is None:
                    self.setupfromaltaz(inalt, inlat, inaz)
                    break
            if isinstance(anob,earthLoc):
                inlat = anob.lat.rad
                if not inalt is None and not inaz is None:
                    self.setupfromaltaz(inalt, inlat, inaz)
                    break
            if isinstance(anob,raDec):
                indec = anob.dec
                inra = anob.ra
                if not insrtdeg is None:
                    self.setupfromradec(inra, indec, insrtdeg)
                    break
            if isinstance(anob, sidereal):
                insrtdeg = anob.degrees
                if not indec is None and not inra is None:
                    self.setupfromradec(inra, indec, insrtdeg)
                    break
        else:
            raise KeyError("observedCoord and latitude source or raDec and sidereal not found in params")

    def setupfromaltaz(self, inalt, inlat, inaz):
        decr, hr  =  mapCoords(inalt, inlat, inaz)
        self.hour = hourVal(hr,'r')
        self.v1 = self.hour
        self.dec = decVal(decr,'r')
        self.v2 = self.dec

    def setupfromradec(self, inra, indec, insrtdeg):
        lochour = insrtdeg - inra.deg
#        print("lochour %4.1f from sidereal %4.1f and ra %4.1f" %(lochour, insrtdeg, inra.deg))
        self.hour = hourVal(lochour,'d')
        self.v1 = self.hour
        self.dec = decVal(indec)
        self.v2 = self.dec

class raDec(twoCoords):
    """
    A sky location in ra/dec. Values are held in degrees and radians with lazy evaluation.
    Hour values are also available (degrees / 15)
    
    Provides attributes ra and dec:
        ra - right ascension
        dec - positive for North of equatorial plane

    __init__:
        supply 'ra' and 'dec' as floats or strings, or as raVal and decVal.
        'raas' and 'decas' can be used to define the units for 'ra' and 'dec' - both default to 'd'.

        See raVal and decVal classes for details of string parsing.
    """
    initVarInfo = (('ra', 'v1', raVal),('dec', 'v2', decVal))    

    strFormat='raDec: {0:dx;}, {1:dx;}'

class motorPair(twoCoords):
    """
    co-ordinates for a pair of motors which can rotate 360 degrees. 
    Values are held in degrees and radians with lazy evaluation. Hour values are also available (degrees / 15) 

    Provides attributes ramot and decmot:
        ramot - any value from 0 to 360
        decmot - any value from 0 to 360
    __init__:
        supply 'ra and 'dec' as floats or strings, or as motorVals.
        'raas' and 'decas' can be used to define the units for 'ra' and 'dec' - both default to 'd'.

        See motorVal class for details of string parsing.
    """
    initVarInfo = (('ramot','v1',  motorVal),('decmot', 'v2', motorVal)) 

    strFormat='motorPair: RA:{0:dx;}, DEC:{1:dx;}'

def mapCoords(x, y, z):
    """
    Used to convert between equatorial and horizon coordinates.
    http://www.sohcahtoa.org.uk/kepler/altaz.html#twig04
    """
    sinx = math.sin(x)
    siny = math.sin(y)
    cosy = math.cos(y)
    xt = math.asin(sinx * siny + math.cos(x) * cosy * math.cos(z))
    try:
        yt = math.acos ((sinx - siny * math.sin(xt) ) / (cosy * math.cos(xt)))
        if  math.sin(z) > 0.0:
            yt = TWOPI - yt
        return (xt, yt)
    except ValueError:
        pass
    
    cy = -math.cos(x) * cosy * math.sin(z)
    cx = sinx - siny * math.sin(xt)
    cz = math.atan(cy/cx)

    if cx < 0:
        cz += math.pi

    return xt, cz

def makeGeom(coordtype, **kwargs):
    """
    uses the argument coordtype to construct an object of that type. Further arguments are defined by the class being constructed
    """
    if coordtype in globals():
        return globals()[coordtype](**kwargs)
    else:
        raise ValueError('unknown class given for coordtype:', str(coordtype))
    return
