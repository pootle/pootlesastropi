# pootlesastropi
A bunch of inter-related python 3 modules to support simple astro stuff on small computers and other generic stuff

The modules so far provided are:
    astroangles.py - a bunch of classes that represent various particular angular measurements such as
            latitude, declination, the angle of a rotational motor etc. The classes provide support for
            formatting and parsing from degrees, radians and hour angles, and automatic on demand 
            conversion between the different angular measures.

    stellarGeometry.py - a bunch of classes to represent geo-location, various representations of sky
            locations (alt/az, right ascension/declination, ...) and the location of an equatorial
            mount. As with astroangles, smart formating functionality is supported.

    clockery.py - some classes for different clocks - sidreal time, local time and Universal Time.
    
    check_config.py - a command line program to display info about a camaera's settings as seen by
            python-gphoto2.

    remi_tabs.py - a small module that provides tabbed access to content. A number of labelled tabs
            are defined and each is associated with a class (which inherits from a remi container such
            as VBox). When the tab is selected, the class is instantiated, and other tab instances
            are left for grbage collection to collect (assuming the rest of the app doesn't 
            hang on to references!).