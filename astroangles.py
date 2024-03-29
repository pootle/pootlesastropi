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

def FromString(fs):
    parts = fs.split(' ',1)
    typestr = parts[0].strip()
    if typestr=='lat':
        return latVal(parts[1])
    if typestr=='lon':
        return lonVal(parts[1])
    if typestr=='alt':
        return altVal(parts[1])
    if typestr=='az':
        return azVal(parts[1])
    if typestr=='RA':
        return raVal(parts[1])
    if typestr=='DEC':
        return decVal(parts[1])
    if typestr=='move':
        return moveVal(parts[1])
    raise ValueError

class degradval():
    """
    a little class to store angles as degrees / radians, allowing either to be set / read and
    laziliy evaluating the other on demand. Hours can also be read and set, but are always calculated from 
    degrees. All values are automatically wrapped to lie within the allowed range when set.
    
    Smart formatting is available using some extensions to the format string syntax as detailed in format.
  
    Also for parsing from strings, special characters can be defined (such as 'E' or 'S' which will be treated
    as the sign of the result.
    
    Basic functionality for callbacks on read / write access are also provided.
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
        self._rval = None
        self._dval = None
        self._changeWatchers = None
        self._readWatchers = None # this may be handy for diagnostics......
        self._wcounter=0
        self.set(v, vas)

    def set(self, v, vas='d'):
        cval, ctype = self._cleanval(v,vas)
        if ctype=='r':
            self.rad=cval
        elif ctype=='d':
            self.deg=cval
        else:
            self.deg=cval*15

    @property
    def deg(self):
        """
        see __init__ for details on valid types / formats
        """
        self._notifyAccess()
        if self._dval is None:
            if self._rval is None:
                return None
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
            self._notifyChange()
        else:
            self._notifyAccess()

    @property
    def rad(self):
        """
        see __init__ for details on valid types / formats
        """
        self._notifyAccess()
        if self._rval is None:
            if self._dval is None:
                return None
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
            self._notifyChange()
        else:
            self._notifyAccess()

    @property
    def hour(self):
        """
        see __init__ for details on valid types / formats
        """
        self._notifyAccess()
        try:
            return self.deg/15
        except:
            return None

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
            self._notifyChange()
        else:
            self._notifyAccess()

    def setWatch(self, wf, onchange, onread=False):
        """
        anyone interested can nominate a callback to trigger on update or access.
        It returns an id that can later be used to cancel interest
        """
        self._wcounter += 1
        if onchange:
            if self._changeWatchers is None:
                self._changeWatchers = {self._wcounter: wf}
            else:
                self._changeWatchers[self._wcounter]=wf
        if onread:
            if self._readWatchers is None:
                self._readWatchers = {self._wcounter: wf}
            else:
                self._readWatchers[self._wcounter]=wf
        return self._wcounter

    def stopWatch(self,wk, wf):
        """
        cancel a callback on update or access.
        """
        assert (not self._changeWatchers is None and self._changeWatchers.get(wk, None) == wf
                ) or (not self._readWatchers is None and self._readWatchers.get(wk, None) == wf), "unwatch key and callback do not match"
        if not self._changeWatchers is None:
            self._changeWatchers.pop(wk, None)
        if not self._readWatchers is None:
            self._readWatchers.pop(wk, None)

    def _notifyAccess(self):
        if not self._readWatchers is None:
            for wk, wf in self._readWatchers.items():
                wf(wk, self)

    def _notifyChange(self):
        if not self._changeWatchers is None:
            for wk, wf in self._changeWatchers.items():
                wf(wk, self)

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
                if tstr.startswith('+'):
                    tstr = tstr[1:]
                elif tstr.startswith('-'):
                    tstr = tstr[1:]
                    endsign *= -1
                colonsplit=tstr.split(':')
                if len(colonsplit)==3:
                    newval = (int(colonsplit[0]) + int(colonsplit[1]) / 60 + float(colonsplit[2]) / 3600) * endsign
                else:
                    newval = float(tstr) * endsign
        return self._constrain(newval, utype)

    def _constrain(self, newval, utype):
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
        seconds. In either case a bunch of standard keyword parameters are passed to format.
        The second character defaults to's' for single. Any other character is interpreted as multinumber.
        single (float) number:
            'abs'    : absolute value of the float
            'signed' : the complete unmodified float
            'schar'  : the 'sign' character to use (typically a compass points, but strings such as 'up' and 'down' or 'cw' and 'ccw' 
                can be used
            'lab'    : the standard label string
        multi number:
            'abs'    : absolute value of the integer part of the value (as an int)
            'signed' : signed value of the integer part of the value (as an int)
            'min'    : minutes part of the value (1/60ths) as an int
            'sec'    : seconds part of the value (1/3600) as an int
            'frac'   : fractional part of a second (1/360000) as a float
            'schar'  : the sign character to use
            'lab'    : the standard label string
            
        >>> lv =aan.lonVal('10:30:45W')

        >>> '{}'.format(lv)
        'lon 10.5125 W'
        
        >>> '{:dd;}'.format(lv)
       'lon 10:30:44.100 W'

        >>> '{:ds;Longitude {{signed}}}'.format(lv)
        'Longitude -10.512499999999989'
        
        '{:hd;Longitude {{signed}} hours, {{min}} minutes, {{sec}} seconds}'.format(lv)
        'Longitude 0 hours, 42 minutes, 2 seconds'
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
            if sval == sval:
                if fmode == 's':
                    formparms={'abs':abs(sval), 'signed':sval, 'schar':self.trailsign(sval), 'lab': self.defaultLabel}
                    basestr = splitspec[1] if splitspec[1] else self.defaultSingleFormat
                else:
                    posv = 1 if sval >= 0 else -1
                    prim, rest = divmod(abs(sval),1)
                    mins, rest = divmod(rest,1/60)
                    secs, fracs = divmod(rest,1/3600)
                    formparms = {
                            'abs'    : int(prim)
                          , 'signed' : int(prim)*posv
                          , 'min'    : int(mins)
                          , 'sec'    : int(secs)
                          , 'frac'   : fracs * 3600
                          , 'hund'   : round(fracs*360000)
                          , 'schar'  : self.trailsign(posv)
                          , 'lab'    : self.defaultLabel
                        }
                    basestr = splitspec[1] if splitspec[1] else self.defaultMultiFormat
                return basestr.format(**formparms)
            else: # its NaN
               return self.nanFormat
        else:
            return self.deg.__format__(fspec)

    def __str__(self):
        return '{}'.format(self)

    defaultFormat = 'ds;'
    
    defaultLabel = ''
    
    defaultSingleFormat = '{lab}{signed:7.4f}'

    defaultMultiFormat = '{lab}{signed:3d}:{min:02d}:{sec:02d}.{hund:02d}'

    nanFormat='-'

    trails = tuple()

    @staticmethod
    def trailsign(val):
        """
        defines strings that can be used to identify the sign for formatting strings
        """
        if val >= 0:
            return '+ve'
        else:
            return '-ve'

    @staticmethod
    def valConstraints(utype):
        return {'d':(0,360)
              , 'r':(0, TWOPI)
              , 'h':(0,24)}[utype]

class latVal(degradval):
    """
    specialisation of degradval for latitude. 'N' & 'S' can be used to indicate sign on input strings
    and for formatting output strings. Value is constrained to +/- 90 degrees.
    
    initialisation:
    ===============
    
    >>> lv = latVal(14.22)   # from a float
    >>> print(lv)
    lat 14.2200 N

    >>> lv = latVal(-22.14)  ' from a signed float
    >>> print(lv)
    lat 22.1400 S
    
    >>> lv =aan.latVal('10:30:45')  # from a string
    >>> print(lv)
    lat 10.5125 N

    >>> lv =aan.latVal('-10:30:45') # or a signed string 
    >>> print(lv)
    lat 10.5125 S

    lv =aan.latVal('10:30:45S')     # or with N/S (or E/W where appropriate) )
    >>> print(lv)
    lat 10.5125 S

    """
    @staticmethod
    def valConstraints(utype):
        return {'d':(90,180)
              , 'r':(HALFPI,math.pi)
              , 'h':(6,12)}[utype]

    trails = (('n',1), ('N',1), ('s',-1), ('S',-1))

    defaultLabel = 'lat '

    defaultSingleFormat = '{lab}{abs:7.4f} {schar}'

    defaultMultiFormat = '{lab}{abs:d}:{min:02d}:{sec:02d}.{hund:02d} {schar}'

    @staticmethod
    def trailsign(val):
        return 'N' if val >= 0 else 'S'

class lonVal(latVal):
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

    defaultLabel = 'lon '

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
              , 'r':(HALFPI,math.pi)
              , 'h':(6,12)}[utype]

    defaultLabel = 'alt '

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

    defaultLabel = 'az '

    @staticmethod
    def trailsign(val):
        if val >= 0:
            return 'cw'
        else:
            return 'ccw'

class raVal(degradval):
    """
    specialisation of lonVal for right ascension. 'Value is constrained to 0 - 360 degrees.
    """

    defaultFormat = 'hx;'

    defaultLabel = 'RA '

    @staticmethod
    def trailsign(val):
        return ''

class decVal(degradval):
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

    defaultLabel = 'DEC '

class motorVal(degradval):
    """
    specialisation of degradval for motor angles. Value is constrained to 0 - 360 degrees.
    """

    defaultFormat = 'ds;'
    
    defaultLabel = 'motor '

    @staticmethod
    def trailsign(val):
        return ''

class moveVal(degradval):
    """
    specialisation of degradval to represent rotation by up to 1 turn +ve or -ve
    """

    defaultFormat = 'ds;'
    
    defaultLabel = 'rotate '
    
    @staticmethod
    def trailsign(val):
        return ''

    def _constrain(self, newval, utype):
       max = {'d':360, 'r':TWOPI,'h':24}[utype]
       cval = abs(newval) % max
       if newval < 0:
           return -cval, utype
       else:
           return cval, utype

class hourVal(motorVal):
    """
    specialisation of degradval for hour angles. Value is constrained to 0 - 360 degrees.
    """

    defaultFormat = 'hx;'
    
    defaultLabel = 'hour '
