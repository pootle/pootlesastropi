#!/usr/bin/env python

"""
A tabbed container.

A container with tabs across the top, each of which can be clicked to select a matching
container to display below the tabs
"""

import remi.gui as gui
from remi import start, App

class TBox(gui.VBox):

    def __init__(self, *args, app, tabs, active_tab, on_tab_change=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.app=app
        self.on_tab_change = on_tab_change
        self.tabheader = gui.HBox(width='100%', style={'background': '#202048', 'padding-top' : '10px'})
        self.active_tab = active_tab
        for tabname, tabinfo in tabs.items():
            if active_tab == tabname:
                bstyle = tabinfo['tstyle']
                assert len(bstyle['background'])==7
            else:
                bstyle = tabinfo['tstyle'].copy()
                assert  len(bstyle['background'])==7
                bstyle['background'] = bstyle['background'] + 'A0'
            atb = gui.Button(text = tabname, style = bstyle)
            atb._tabinfo=tabinfo
            atb._tabname = tabname
            atb.onclick.do(self.switch_tab)
            self.tabheader.append(atb, tabname)
        self.append(self.tabheader, 'tabnames')
        if self.active_tab is None:
            content = gui.Label('nothing here', width='80%', height='50%')
            self.append(content, 'panel')
        else:
            active = self.tabheader.children[self.active_tab]
            actinfo = active._tabinfo
            if 'content' in actinfo:
                content = actinfo['content'](app=self.app, **actinfo['cont_kwargs'])
                self.append(content, 'panel')
            else:
                content = gui.Label('This tab has no content.....', width='80%', height='50%')
                self.append(content, 'panel')

    def switch_tab(self, tabbtn):
        if self.active_tab:
            prev = self.tabheader.children[self.active_tab]
            bstyle = prev._tabinfo['tstyle'].copy()
            bstyle['background'] = bstyle['background'] + 'A0'
            prev.set_style(bstyle)
        tabbtn.set_style(tabbtn._tabinfo['tstyle'])
        self.active_tab = tabbtn._tabname
        if 'panel' in self.children:
            oldpanel = self.children['panel']
            self.remove_child('panel')
        else:
            oldpanel = None
        actinfo = tabbtn._tabinfo
        if 'content' in actinfo:
            content = actinfo['content'](app=self.app, **actinfo['cont_kwargs'])
        else:
            content = gui.Label('This tab has no content.....', width='80%', height='50%')
        self.append(content, 'panel')
        if self.on_tab_change:
            self.on_tab_change(oldpanel, content)

    def current_tab(self):
        try:
            return self.children['panel']
        except:
            return None

import pathlib as pl

class BetterFolderNavigator(gui.FileFolderNavigator):
    def dir_go(self, widget):
        # when the GO button is pressed, it is supposed that the pathEditor is changed
        newpath = pl.Path(self.pathEditor.get_text())
        if newpath.exists():
            self.chdir(str(newpath))
            return
        try:
            newpath.mkdir(parents=True)
            self.chdir(str(newpath))
            return
        except:
            print('error creating directory', file = sys.stderr)
        self.pathEditor.set_text(self._last_valid_path)

class BetterFileSelectionDialog(gui.GenericDialog):
    """file selection dialog, it opens a new webpage allows the OK/CANCEL functionality
    implementing the "confirm_value" and "cancel_dialog" events."""

    def __init__(self, title='File dialog', message='Select files and folders',
                 multiple_selection=True, selection_folder='.',
                 allow_file_selection=True, allow_folder_selection=True, **kwargs):
        super().__init__(title, message, **kwargs)

        self.css_width = '475px'
        self.filenav = BetterFolderNavigator(multiple_selection, selection_folder,
                                                       allow_file_selection,
                                                       allow_folder_selection, width="100%", height="330px")
        self.add_field('fileFolderNavigator', self.filenav)
        self.confirm_dialog.connect(self.confirm_value)

    @gui.decorate_set_on_listener("(self, emitter, fileList)")
    @gui.decorate_event
    def confirm_value(self, widget):
        """event called pressing on OK button.
           propagates the string content of the input field
        """
        self.hide()
        params = (self.filenav.get_selection_list(),)
        return params

tab_btn_style_1 = {'font-size': '2.4em', 'padding': '5px 15px 5px 15px', 'border-radius': '15px 15px 0px 0px', 'color': 'white', 'background': '#704040'}
tab_btn_style_2 = {'font-size': '2.4em', 'padding': '5px 15px 5px 15px', 'border-radius': '15px 15px 0px 0px', 'color': 'white', 'background': '#409040'}
tab_btn_style_3 = {'font-size': '2.4em', 'padding': '5px 15px 5px 15px', 'border-radius': '15px 15px 0px 0px', 'color': 'white', 'background': '#404080'}

if __name__ == "__main__":
    label_style = {'background': '#00000000', 'padding': '2px 8px 2px 2px', 'font-size':'1.7em', 'text-align': 'right', 'box-shadow': '5px 10px #c0c0c0'}

    class camtab(gui.GridBox):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.append({
                'isolbl'     : gui.Label(text='iso:', style = label_style),
                'isoval'     : gui.DropDown.new_from_list(('100', '200', '400', '1600'), style={'font-size': '1.7em'}),
                'shutlbl'    : gui.Label(text='exposure time:', style = label_style),
                'shutval'    : gui.Input(input_type='number', min="2", max="10", step="any",  default_value=3, style={'font-size': '1.7em'}),
                'cardsavelbl': gui.Label(text='save to camera card:', style = label_style),
                'cardsavechk': gui.CheckBox(checked = False, style={'font-size': '1.7em'}),
            })
            self.define_grid([
                ['isolbl', 'isoval'],
                ['shutlbl', 'shutval'],
                ['cardsavelbl', 'cardsavechk']
            ])
    
    class simple_app(App):
        def __init__(self, *args):
            super().__init__(*args)
    
        def main(self):
            #creating a container VBox type, vertical
            wid = gui.VBox(width=1200, height=600)
    
            #a button for simple interaction
            bt = gui.Button('Press me!', width=200, height=30)
    
            #adding the widgets to the main container
            wid.append(TBox(width='100%', height = 450, style={'background': 'pink', 'justify-content': 'flex-start'}, tabs={
                    'one'           : {'ttext': 'oneish', 'tstyle': tab_btn_style_1, 'content': camtab, 'cont_kwargs':{'width': '100%', 'style': {'background': '#704040'}}}, 
                    'two'           : {'ttext': 'istwo', 'tstyle': tab_btn_style_2},
                    'brother mine'  : {'ttext': 'final', 'tstyle': tab_btn_style_3},
            }, active_tab = 'one'))
            wid.append(bt)
    
    
            # returning the root widget
            return wid

    start(simple_app, debug=True, address='0.0.0.0', port=8808)
