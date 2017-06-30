#!/usr/bin/python3
"""
clockery provides classes and functions for handling normal and sidereal time.
"""
import math
import datetime, time
import pytz
from tzlocal import get_localzone

class liveClock():
    """
    A composite clock class that can deliver the current local time of day, Greenwich time and sidereal time using 
    independent clocks so they can easily be fetched in any format.
    
    """
    def __init__(self, timetuple=None, location=None):
        """
        setup clocks by default they will show current time, but passing a timetuple like list will set the 
        clocks to start at that time in the local timezone
        """
        self.tz = get_localzone()
        if timetuple:
            simplet = datetime.datetime(*timetuple)
            toffset = simplet.timestamp() - time.time()
        else:
            simplet = datetime.datetime.now()
            toffset = 0
        currentdt = self.tz.localize(simplet, is_dst=None)
        self.local = localClocktime(offset=toffset, withdt=currentdt)
        self.gmt = greenwichTime(offset=toffset, withdt=currentdt)
        self.lst = sidereal(offset=toffset if location is None else location, withdt=currentdt)

    def showclocks(self):
        print(format(self.local,'x;The time in {4:s} is {0:02d} hours, {1:02d} minutes and {2:02d} seconds.'))
        print(format(self.gmt))
        print(format(self.lst))

class localClocktime():
    """
    This class provides 'transparent' access to a time of day clock. The clock can easily be adapted to
    to different timezones, sidereal time or greenwich mean time.
    
    It uses a calculated offset from a timestamp time which allows fast calculation of an accurate
    time of day on demand. The base time is recalculated whenever the clock wraps round.
    """

    daylength=24*60*60

    def __init__(self, offset, withdt=None):
        self.lz = None
        if isinstance(offset,(int,float)):
            self.offset = offset
        else:
            raise TypeError("offset provided (%s) is not a number" % str(offset))
        self._resetday(withdt)

    def _resetday(self, withdt):
        fixeddt = self._getAwareDT(withdt)
        self._settodFromDT(fixeddt)
       
    def _settodFromDT(self, adt):
        todbit = adt.second + (adt.hour*60 + adt.minute) *60 + adt.microsecond / 1000000
        self._daystart = adt.timestamp() - todbit 

    @property
    def tod(self):
        timeoff = time.time()-self._daystart + self.offset
        if timeoff > localClocktime.daylength:
            self._resetday(None)
            timeoff = time.time()-self._daystart + self.offset
        return timeoff

    @property
    def degrees(self):
        return self.tod/240

    @property
    def hours(self):
        return self.tod/3600

    def __format__(self,formatspec):
        fspec = formatspec if formatspec else self.defaultFormat
        splitspec = fspec.split(';',1)
        part1len = len(splitspec[0])
        sval = self.tod
        if len(splitspec) == 2 and (part1len == 1 ):
            fmode=splitspec[0][0]
            if fmode == 's':
                formparms=(sval,)
                basestr = splitspec[1] if splitspec[1] else self.defaultSingleFormat
            else:
                allsecs, fract = divmod(sval,1)
                rest, sec = divmod(int(allsecs),60)
                hour, min = divmod(rest,60)
                formparms = (hour, min, sec, int(round(fract*100)), self.lz.zone)
                basestr = splitspec[1] if splitspec[1] else self.defaultMultiFormat
 
            return basestr.format(*formparms)
        else:
            return sval.__format__(fspec)

    def _getAwareDT(self, adatetime):
        """
        returns a timezone aware datetime.
        
        If the given datetime is timezone aware it is returned as is. self.lz will be set from this
        datetime if it is not yet set.

        If the given datetime is not timezone aware and there is a timezone in self.lz, then
        self.lz is applied to the datetime and returned (this is a new datetime).
        
        If the given datetime is not timezone aware and there is no timezone in self.lz, then
        self.lz is set to the local timezone, applied to the datetime and returned as a new datetime.
        
        If no datetime is given, self.lz is set to the local timezone if it is unset, then self.lz
        is applied to the current datetime and returned.
        """
        adt = datetime.datetime.fromtimestamp(time.time()+self.offset) if adatetime is None else adatetime
        if adt.tzinfo:
            if self.lz is None:
                self.lz = adt.tzinfo
            return adt
        if self.lz is None:
            self.lz = get_localzone()
        return self.lz.localize(adt, is_dst=None)

    def __str__(self):
        return self.defaultFormat.format(self)

    defaultFormat = 'x;'

    defaultSingleFormat = 'local zone time {0:7.2f}'

    defaultMultiFormat = '{4:s}: {0:02d}:{1:02d}:{2:02d}.{3:02d}'

class greenwichTime(localClocktime):
    """
    this variant of localCLockTime provides greenwich mean time 
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _resetday(self, withdt):
        fixeddt = self._getAwareDT(withdt)
        dfixed = fixeddt.astimezone(pytz.utc)
        self._settodFromDT(dfixed)

    defaultSingleFormat = 'GMT: {0:7.2f}'

    defaultMultiFormat = 'GMT: {0:02d}:{1:02d}:{2:02d}.{3:02d}'

class sidereal(localClocktime):
    """
    this variant of localCLockTime provides mean sidereal time for the given latitude
    """
    
    siderealfix = 365.24 / 364.24
    
    def __init__(self, offset, **kwargs):
        """
        The offset can be provided as an earthLoc or as a lonVal or a simple period in seconds
        """
        from stellarGeometry import lonVal, earthLoc
        lonob = offset if isinstance(offset,lonVal) else offset.lon if isinstance(offset,earthLoc) else None
        if lonob is None:
            self.houroffset = 0
            if isinstance(offset,(int,float)):
                useoffset=offset
            else:
                raise TypeError('provided offset not resolvable to number')
        else:
            self.houroffset = lonob.hour
            useoffset = 0
        
        super().__init__(offset=useoffset, **kwargs)

    @property
    def tod(self):
        timeoff = (time.time()-self._daystart + self.offset) * sidereal.siderealfix
        if timeoff > localClocktime.daylength:
            self._resetday(None)
            timeoff = (time.time()-self._daystart + self.offset) * sidereal.siderealfix
        return timeoff

    def _resetday(self, withdt):
        utz = self._getAwareDT(withdt).astimezone(pytz.utc)
        utt = utz.timetuple()
        utstamp = utz.timestamp()
        partday = ((utt.tm_sec/60 + utt.tm_min)/60 + utt.tm_hour)/24
        offsetjuliandt = datetime.datetime(utt.tm_year,utt.tm_mon,utt.tm_mday).toordinal() - 730121.5 + partday
        st = (18.697374558 + 24.06570982441908 * offsetjuliandt + self.houroffset) % 24
        self._daystart = utstamp - st*3600
    
    defaultSingleFormat = 'LST: {0:7.2f}'

    defaultMultiFormat = 'LST: {0:02d}:{1:02d}:{2:02d}.{3:02d}'
    
