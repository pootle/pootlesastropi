# pootlesastropi
A bunch of inter-related python 3 modules to support simple astro stuff on small computers.

The modules so far provided are:
    astroangles.py - a bunch of classes that represent various particular angular measurements such as
            latitude, declination, the angle of a rotational motor etc. The classes provide support for
            formatting and parsing from degrees, radians and hour angles, and automatic on demand 
            conversion between the different angular measures.

    stellarGeometry.py - a bunch of classes to represent geo-location, various representations of sky
            locations (alt/az, right ascension/declination, ...) and the location of an equatorial mount.
            As with astroangles, smart formating functionality is supported.

    clockery.py - a bunch of classes to represent different times - sidreal time, local time and Universal Time.
    
    check_config.py - a command line program to display info about a camaera's settings as seen by python-gphoto2
   
