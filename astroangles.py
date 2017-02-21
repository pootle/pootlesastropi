#!/usr/bin/python3
"""
This module proves a 'smart angles' set of classes which can parse, convert and format
angles for a variety of amateur astronomy purposes.

They are all based around a single class (degradval) which allows much of the detailed behaviour
to be parameterised by the inheriting classes which cater for specific uses of angles.
"""
import math

TWOPI=math.pi*2
HALFPI=math.pi/2
TWELFTHPI=math.pi/12

class degradval():
    """
    a little class to store angles as degrees / radians, allowing either to be set / read and
    laziliy evaluating the other on demand. Hours can also be read, but are always calculated from 
    degrees. All values are automatically wrapped to lie within the allowed range when set.
    
    Smart formatting is available using some extensions to the format string syntax as detailed in format.
  
    Also for parsing from strings, special characters can be defined (such as 'E' or 'S' which will be treated
    as the sign of the result.
    """
    def __init__(self, v, vas='d'):
        """
        setup instance with value v, vas is expected units - used if v doesn't identify the units used.
        
        The value can be a float or int, a string, or another instance of the same type being created.
        
        float or int:
            units are defined by vas ('d'egrees, 'r'adians, 'h'ours)
        
        string:
            if the string contains 'd', 'r' or 'h' the string is interpreted as degrees, radians or hours
            and vas is ignored.
                    
            The string can be preceeded by '+' or '-', this is handled by the normal parsers for float.
        
            The string can be followed by optional strings that inherting classes can easily change to set
            sign such as 'N', 'S' 'E' or 'W'
        
        """
        cval, ctype = self._cleanval(v,vas)
        self._dval=None
        self._rval=None
        if ctype=='r':
            self._rval=cval
            self._dval=None
        elif ctype=='d':
            self._dval=cval
            self._rval=None
        else:
            self._dval=cval*15
            self._rval=None

    @property
    def deg(self):
        """
        see __init__ for details on valid types / formats
        """
        if self._dval is None:
            self._dval=math.degrees(self._rval)
        return self._dval

    @deg.setter
    def deg(self,dval):
        """
        see __init__ for details on valid types / formats
        """
        newval, dtype = self._cleanval(dval,'d')
        if dtype != 'd':
            raise ValueError("%s fails to parse as degrees." % dval)
        if newval != self.deg:
            self._dval = newval
            self._rval = None

    @property
    def rad(self):
        """
        see __init__ for details on valid types / formats
        """
        if self._rval is None:
            self._rval=math.radians(self._dval)
        return self._rval

    @rad.setter
    def rad(self,rval):
        """
        see __init__ for details on valid types / formats
        """
        newval, dtype = self._cleanval(rval, 'r')
        if dtype != 'r':
            raise ValueError("%s fails to parse as radians." % rval)
        if newval != self.rad:
            self._rval = newval
            self._dval = None

    @property
    def hour(self):
        """
        see __init__ for details on valid types / formats
        """
        return self.deg/15

    @hour.setter
    def hour(self,hval):
        """
        see __init__ for details on valid types / formats
        """
        newval, dtype = self._cleanval(hval, 'h')
        if dtype != 'h':
            raise ValueError("%s fails to parse as hours." % hval)
        newval *= 15
        if self._dval != newval:
            self._dval=newval
            self._rval = None

    def _cleanval(self, val, units):
        if type(self) == type(val):
            newval = val.deg
            utype= 'd'
        else:
            if units in ('d','r','h'):
                utype = units
            else:
                utype = 'd'
            if isinstance(val, float):
                newval = val
            elif isinstance(val, int):
                newval = float(val)
            else:
                if isinstance(val,str):
                    usplit = val.split('d')
                    if len(usplit) == 2:
                        utype='d'
                    else:
                        usplit = val.split('r')
                        if len(usplit) == 2:
                            utype='r'
                        else:
                            usplit = val.split('h')
                            if len(usplit) == 2:
                                utype='h'
                    if len(usplit)==2:
                        val=usplit[0]+usplit[1]
                tstr = val.strip()
                for tr,tv in self.trails:
                    if tstr.endswith(tr):
                        endsign = tv
                        tstr = tstr[:-len(tr)]
                        break
                else:
                    endsign=1
                colonsplit=tstr.split(':')
                if len(colonsplit)==3:
                    newval = int(colonsplit[0]) + int(colonsplit[1]) / 60 + float(colonsplit[2]) / 3600
                else:
                    newval = float(tstr)

        offset, cyclic = self.valConstraints(utype)
        newval = (newval+offset)%cyclic-offset
        return newval, utype

    def __format__(self,formatspec):
        """
        The format string adds a short sequence on the front of a standard format string, this is 1 or 2
        characters in length and is separated from the 'standard' part of the format string by a ';' semicolon.
        
        Each class defines defaults for each part of the format.
        
        The first or only character defines if the value to be formated should be in
        'd': degrees
        'r': radians
        'h': hours
        
        The second character defines whether to format as a single floating point number or as a sequence with minutes and
        seconds. In either case a bunch of standard positional parameters are passed to format.
        The second character defaults to's' for single. Any other character is interpreted as multinumber.
        single (float) number:
            0: absolute value of the float
            1: the complete unmodified float
            2: the 'sign' character to use (typically a compass points, but strings such as 'up' and 'down' or 'cw' and 'ccw' 
                can be used
        multi number:
            0: absolutes value of the integer part of the value (as an int)
            1: signed value of the integer part of the value (as an int)
            2: minutes part of the value (1/60ths) as an int
            3: seconds part of the value (1/3600) as an int
            4: hundredths of a second (1/360000) as an int
            5: the sign character to use
        """
        fspec = formatspec if formatspec else self.defaultFormat
        splitspec = fspec.split(';',1)
        part1len = len(splitspec[0])
        if len(splitspec) == 2 and (part1len == 1 or part1len == 2):
            src=splitspec[0][0]
            fmode=splitspec[0][1] if part1len == 2 else 's'
            if src == 'd':
                sval = self.deg
            elif src == 'r':
                sval = self.rad
            elif src == 'h':
                sval = self.hour
            else:
                raise ValueError('Invalid format source value specifier for degradval >%s<' % fspec)
            if fmode == 's':
                formparms=(abs(sval), sval, self.trailsign(sval))
                basestr = splitspec[1] if splitspec[1] else self.defaultSingleFormat
            else:
                posv = 1 if sval >= 0 else -1
                prim, rest = divmod(abs(sval),1)
                mins, rest = divmod(rest,1/60)
                secs, fracs = divmod(rest,1/3600)
                formparms = (int(prim), int(prim)*posv, int(mins), int(secs), int(fracs * 360000), self.trailsign(posv))
                basestr = splitspec[1] if splitspec[1] else self.defaultMultiFormat
 
            return basestr.format(*formparms)
        else:
            return self.deg.__format__(fspec)

    defaultFormat = '5.3f'

    defaultSingleFormat = '{1:7.4f}'

    defaultMultiFormat = '{1:3d}:{2:02d}:{3:02d}.{4:02d}'

    @staticmethod
    def trailsign(val):
        """
        defines strings that can be used to identify the sign for formatting strings
        """
        if val >= 0:
            return '+ve'
        else:
            return '-ve'

class latVal(degradval):
    """
    specialisation of degradval for latitude. 'N' & 'S' can be used to indicate sign on input strings
    and for formatting output strings. Value is constrained to +/- 90 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(90,180)
              , 'r':(HALFPI,math.pi)}[utype]

    trails = (('n',1), ('N',1), ('s',-1), ('S',-1))

    defaultFormat = 'ds;'

    defaultSingleFormat = 'lat {0:7.4f} {2}'

    defaultMultiFormat = 'lat {0:d}:{2:02d}:{3:02d}.{4:02d} {5}'

    @staticmethod
    def trailsign(val):
        return 'N' if val >= 0 else 'S'

class lonVal(degradval):
    """
    specialisation of degradval for longitude. 'E' & 'W' can be used to indicate sign on input strings
    and for formatting output strings. Value is constrained to +/- 180 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(180,360)
              , 'r':(math.pi, TWOPI)
              , 'h':(12,24)}[utype]

    trails = (('e',1), ('E',1), ('w',-1), ('W',-1))

    defaultFormat = 'ds;'

    defaultSingleFormat = 'lon {0:7.4f} {2}'

    defaultMultiFormat = 'lon {0:d}:{2:02d}:{3:02d}.{4:02d} {5}'

    @staticmethod
    def trailsign(val):
        return 'E' if val >= 0 else 'W'

class altVal(degradval):
    """
    specialisation of degradval for alititude angles. Value is constrained to +/- 90 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(90,180)
              , 'r':(HALFPI,math.pi)}[utype]

    trails = tuple()

    defaultFormat = 'ds;'

    defaultSingleFormat = 'alt {0:7.4f} {2}'

    defaultMultiFormat = 'alt {1:d}:{2:02d}:{3:02d}.{4:02d}'

    @staticmethod
    def trailsign(val):
        if val >= 0:
            return 'up'
        else:
            return 'dn'

class azVal(degradval):
    """
    specialisation of degradval for azimuth. Value is constrained to +/- 180 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(180,360)
              , 'r':(math.pi, TWOPI)
              , 'h':(12,24)}[utype]

    trails = tuple()

    defaultFormat = 'ds;'

    defaultSingleFormat = 'az {0:7.4f} {2}'

    defaultMultiFormat = 'az {1:d}:{2:02d}:{3:02d}.{4:02d}'

    @staticmethod
    def trailsign(val):
        if val >= 0:
            return 'cw'
        else:
            return 'ccw'

class raVal(lonVal):
    """
    specialisation of lonVal for right ascension. 'Value is constrained to 0 - 1360 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(0,360)
              , 'r':(0, TWOPI)
              , 'h':(0,24)}[utype]

    trails = tuple()

    defaultFormat = 'hx;'

    defaultSingleFormat = 'RA {0:7.4f}'

    defaultMultiFormat = 'RA {1:d}:{2:02d}:{3:02d}.{4:02d}'


    @staticmethod
    def trailsign(val):
        return ''
class decVal(latVal):
    """
    specialisation of latVal for latitude. 'N' & 'S' can be used to indicate sign on input strings
    and for formatting output strings. Value is constrained to +/- 90 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(90,180)
              , 'r':(HALFPI, math.pi)
              , 'h':(6,12)}[utype]

    defaultFormat = 'dx;'

    defaultSingleFormat = 'DEC {1:7.4f}'

    defaultMultiFormat = 'DEC {1:d}:{2:02d}:{3:02d}.{4:02d}'

class motorVal(degradval):
    """
    specialisation of degradval for motor angles. Value is constrained to 0 - 360 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(0,360)
              , 'r':(0, TWOPI)
              , 'h':(0,24)}[utype]

    trails = tuple()

    defaultFormat = 'dx;'

    @staticmethod
    def trailsign(val):
        return ''

class hourVal(degradval):
    """
    specialisation of degradval for hour angles. Value is constrained to 0 - 360 degrees.
    """
    @staticmethod
    def valConstraints(utype):
        return {'h':(0,24)
              , 'd':(0,360)
              , 'r':(0,TWOPI)}[utype]

    trails = tuple()

    defaultFormat = 'hx;'

    defaultSingleFormat = 'hour {1:5.1f}'

    defaultMultiFormat = 'hour {0:02d}:{2:02d}:{3:02d}.{4:02d}'

    @staticmethod
    def trailsign(val):
        return ''
