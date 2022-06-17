#!/usr/bin/env python

widg_types = {
    0: 'window',
    1: 'section',
    2: 'text',
    3: 'range',
    4: 'toggle',
    5: 'radio',
    6: 'menu',
    7: 'button',
    8: 'date',
}
GP_WIDGET_BUTTON = 7
GP_WIDGET_DATE = 8
GP_WIDGET_MENU = 6
GP_WIDGET_RADIO = 5
GP_WIDGET_RANGE = 3
GP_WIDGET_SECTION = 1
GP_WIDGET_TEXT = 2
GP_WIDGET_TOGGLE = 4
GP_WIDGET_WINDOW = 0

import sys, json
try:
    import gphoto2 as gp
except:
    print('unable to import gphoto2 - please ionstall - see full help ( -h)', file=sys.stderr)
    sys.exit(1)

def gp_widg_state(gpwidg):
    wt=gpwidg.get_type()
    if wt in (0,1):
        ws=[]
        for i in range(gpwidg.count_children()):
            ws += gp_widg_state(gpwidg.get_child(i))
        return ws
    else:
        return [(gpwidg.get_name(), gpwidg.get_value())]

def main(output, compare, listvals, fixedlist, settings):
    cam=gp.Camera()
    try:
        cam.init()
    except gp.GPhoto2Error as gpe:
        if gpe.code == -105:
            print('ERROR: Unable to contact camera - is it connected? has it timed out?', file=sys.stderr)
            sys.exit(1)
    except:
        raise
    xxcam_cfg=cam.get_config()    
    cam_cfg=dict(gp_widg_state(xxcam_cfg))
    if compare is None:
        prev=None
    else:
        with open(compare,'r') as oldvals:
            prev=json.load(oldvals)
    if output:
        with open(output, 'w') as newvals:
            json.dump(cam_cfg, newvals, indent=3)

    if compare is None and output is None:
        for k,v in cam_cfg.items():
            if not settings or k in settings:
                if listvals:
                    cl=None
                    try:
                        cwidg = cam.get_single_config(k)
                    except gp.GPhoto2Error:
                        print('failed to read widget for setting >%s<' % k) # for silly widget with no name
                        cwidg = None
                    if cwidg:
                        wt=cwidg.get_type()
                        if wt in [3,5,6,7]:
                            try:
                                cl = [v for v in cwidg.get_choices()]
                            except:
                                print('not for type', wt )
                    if cl is None:
                        if not fixedlist:
                            print('%20s: %s' % (k,v))
                    else:
                        if fixedlist:
                            print("'%s': [%s]" % (k, ', '.join(["'%s'" % v for v in cl])))
                        else:
                            print('%20s: %s (%s)' % (k,v, ', '.join(['%s' % v for v in cl])))
                else:
                    print('%20s: %s' % (k,v))
    elif compare:
        allnames=set(list(cam_cfg.keys())+list(prev.keys()))
        changes={}
        news={}
        missing={}
        for aname in allnames:
            if aname in cam_cfg:
                if aname in prev:
                    if cam_cfg[aname] != prev[aname]:
                        changes[aname] = (cam_cfg[aname],prev[aname])
                else:
                    news[aname]=cam_cfg[aname]
            else:
                missing[aname] = prev[aname]
        nothing=True
        if changes:
            nothing=False
            print('The following entries have changed (old value then new value)')
            for k, v in changes.items():
                extras = ''
                if listvals:
                    try:
                        cwidg = cam.get_single_config(k)
                    except gp.GPhoto2Error:
                        cwidg = None
                    if cwidg:
                        wt=cwidg.get_type()
                        if wt in [3,5,6,7]:
                            try:
                                extras = ', '.join(['%s' % v  for v in cwidg.get_choices()])
                            except:
                                print('not for type', wt )
                print('%22s: %20s, %20s  %s' % (k, prev[k], cam_cfg[k], extras))
        if news:
            nothing=False
            print('The following are new entries:')
            for k,v in news.items():
                print('%22s: %20s' % (k, cam_cfg[k]))
            print('')
        if missing:
            nothing = False
            print('The following entries are no longer present:')
            for k,v in missing.items():
                print('%22s: %20s' % (k, missing[k]))
            print('')
        if nothing:
            print('No differences found')
    cam.exit()

import sys
import argparse

epil="""
================================================

uses gphoto2 to record and optionally compare live with saved camera settings.

Typically, first run with output file to record settings
    ./check_config.py -o baseset.json

Then disconnect camera and change setting(s) on camera

Then run again with original file as compare file and all differences are printed out
    ./check_config.py -c baseset.json

All the output uses names and values to use in a python program to control the caamera 

examples
========
./checkconfig.py
        print all gphoto2 accessible settings and their current values

./checkconfig.py -l
        as above, but each entry lists the valid values (where relevent)

./checkconfig.py -o baseconf.cfg
        save all accessible settings to a json file (laid out to be readable)
        no console output.

./checkconfig.py -o baseconf.cfg
        check all current settings to a previously saved json file and print
        all the differences.

./checkconfig.py -l drivemode
        print the current value and valid values of the 'drivemode' setting

gphoto2:
=======

You can usually install a relatively old version this with
    sudo apt install python3-gphoto2
or
    pip install gphoto2

but this should get you the latest version if necessary 
    pip install -v gphoto2 --no-binary :all:

See here for full details - including what to do if the above fails
https://github.com/jim-easterbrook/python-gphoto2#installation-binary-wheel

Many thanks to Jim for an excellent and well put together python binding.
"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='record / compare camera settings via gphoto2',
                                     epilog=epil,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output',       help='filename for current settings (json file)')
    parser.add_argument('-c', '--compare',      help='compare current settings with settings in this file')
    parser.add_argument('-l', '--listvals',     help='shows list of valid values for settings that support this',  default=False, action='store_true')
    parser.add_argument('-f', '--fixedlist',    help='only list settings that have a preset list of values', default=False, action='store_true')
    parser.add_argument('settings', nargs = '*', help='restrict output to these settings')
    args=parser.parse_args()
#    for k,v in args.__dict__.items():
#        print('%28s: %s' % (k,v))
    sys.exit(main(**args.__dict__))
