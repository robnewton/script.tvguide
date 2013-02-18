#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import xbmc
import xbmcgui
import pprint

from resources.lib.globals import *
from resources.lib.strings import *
from resources.lib.gui.gui_helpers import GUIHelpers

class MenuHelper(object):
    parentMenu = None
    screen = None
    menuDict = {}
    mainMenuControls = []
    mainMenuIconControls = []
    leftArrowControl = 0
    rightArrowControl = 0
    okButtonControl = 0
    subMenuControls = []
    subMenuEnabled = False
    displayedOptionsCount = 0
    highlightedIndex = 0
    activeMenuItem = 0
    debugEnabled = False

    #Example Menu Dict: {'ActionId':4502, 'Label':'Watch Now', 'Submenu':{}}
    #Example Control Dict: {'ActionId':4502, 'Label':'Watch Now', 'Submenu':{}}
    def __init__(self, screen, menuDict, mainMenuControls = [], mainMenuIconControls = [],
                 leftArrowControl = 0, rightArrowControl = 0, okButtonControl = 0, highlightedIndex = 2,
                 subMenuControls = [], parentMenu = None, activeMenuItem = None, debugEnabled = False):
        self.parentMenu = parentMenu
        self.debugEnabled = debugEnabled
        self.screen = screen
        self.menuDict = menuDict
        self.mainMenuControls = mainMenuControls
        self.mainMenuIconControls = mainMenuIconControls
        self.leftArrowControl = leftArrowControl
        self.rightArrowControl = rightArrowControl
        self.okButtonControl = okButtonControl
        self.subMenuControls = subMenuControls
        if len(self.subMenuControls) > 0:
            self.subMenuEnabled = True
        self.highlightedIndex = highlightedIndex
        if activeMenuItem == None:
            self.activeMenuItem = highlightedIndex
        else:
            self.activeMenuItem = activeMenuItem
        if self.activeMenuItem >= len(self.menuDict):
            if self.debugEnabled:
                debug('small set of menu items: %s >= %s' % (self.activeMenuItem, len(self.menuDict)))
            self.activeMenuItem = int(round(len(self.menuDict) / 2))
        if self.debugEnabled:
            debug('%r' % self)
        self._renderMenu()
        if 'Submenu' in self.menuDict[self.activeMenuItem]:
            self._renderSubmenu()
        GUIHelpers.hide(self.screen, self.leftArrowControl)
        GUIHelpers.hide(self.screen, self.rightArrowControl)

    def __repr__(self):
        return pprint.pformat(self.menuDict)

    def moveUpOne(self):
        if self.activeMenuItem > 0 and self.activeMenuItem <= (len(self.menuDict)-1):
            if self.debugEnabled:
                debug('activeMenuItem: %s' % self.activeMenuItem)
            self.activeMenuItem -= 1
            self._renderMenu()
            self._renderSubmenu()

    def moveDownOne(self):
        if self.activeMenuItem >= 0 and self.activeMenuItem < (len(self.menuDict)-1):
            if self.debugEnabled:
                debug('activeMenuItem: %s' % self.activeMenuItem)
            self.activeMenuItem += 1
            self._renderMenu()
            self._renderSubmenu()

    def getSelectedMenuItem(self):
        try:
            return self.menuDict[self.activeMenuItem]
        except IndexError:
            return {}

    def getSelectedAction(self):
        try:
            return self.menuDict[self.activeMenuItem]['ActionID']
        except IndexError:
            return 0
        
    def render(self):
        self._renderMenu()
        self._renderSubmenu()

    def _renderMenu(self):
        offset = self.activeMenuItem - (self.highlightedIndex - 1)
        if self.debugEnabled:
            debug('offset: %s' % offset)
        for i in range(0, len(self.mainMenuControls)):
            try:
                try:
                    #Show the icon if there are submenu items
                    if self.debugEnabled:
                        debug('Checking if icon is needed (Submenu in the following): %s' % pprint.pformat(self.menuDict[i + offset]))
                    if 'Submenu' in self.menuDict[i + offset]:
                        GUIHelpers.show(self.screen, self.mainMenuIconControls[i])
                        if self.debugEnabled:
                            debug('Showed icon!')
                    else:
                        GUIHelpers.hide(self.screen, self.mainMenuIconControls[i])
                except:
                    if self.debugEnabled:
                        debug('Failed checking if icon is needed')
                    pass
                if (i + offset) < 0:
                    labelBuf = ''
                else:
                    labelBuf = self.menuDict[i + offset]['Label']
            except (IndexError, KeyError):
                labelBuf = ''
            if i == (self.highlightedIndex - 1):
                try:
                    #Show the right arrow if there are submenu items
                    if self.debugEnabled:
                        debug('Checking if right arrow is needed (Submenu in the following): %s' % pprint.pformat(self.menuDict[i + offset]))
                    if 'Submenu' in self.menuDict[i + offset]:
                        GUIHelpers.show(self.screen, self.rightArrowControl)
                        if self.debugEnabled:
                            debug('Showed right arrow!')
                    else:
                        GUIHelpers.hide(self.screen, self.rightArrowControl)
                except:
                    if self.debugEnabled:
                        debug('Failed checking if right arrow is needed')
                    pass
                try:
                    #Show the left arrow if there is a parent menu
                    if self.debugEnabled:
                        debug('Checking if left arrow is needed (ParentMenu iis of type: MenuHelper) %s' % pprint.pformat(self.parentMenu))
                    if isinstance(self.parentMenu, MenuHelper):
                        GUIHelpers.show(self.screen, self.leftArrowControl)
                        if self.debugEnabled:
                            debug('Showed left arrow!')
                    else:
                        GUIHelpers.hide(self.screen, self.leftArrowControl)
                except:
                    if self.debugEnabled:
                        debug('Failed checking if left arrow is needed')
                    pass
                GUIHelpers.setBoldLabelText(self.screen, self.mainMenuControls[i], labelBuf)
            else:
                GUIHelpers.setLabelText(self.screen, self.mainMenuControls[i], labelBuf)

    def _renderSubmenu(self):
        if self.subMenuEnabled == False:
            return
        for i in range(0, len(self.subMenuControls)):
            try:
                labelBuf = self.menuDict[self.activeMenuItem]['Submenu'][i]['Label']
            except KeyError:
                labelBuf = ''
            GUIHelpers.setLabelText(self.screen, self.subMenuControls[i], labelBuf)
            if self.debugEnabled:
                debug('submenu item: %s' % labelBuf)

        
