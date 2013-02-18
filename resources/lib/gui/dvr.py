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
import sys
import xbmc
import xbmcgui
import buggalo
import datetime
import pprint

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

from resources.lib.globals import *
from resources.lib.strings import *
from resources.lib.gui.menu_helper import MenuHelper
from resources.lib.gui.gui_helpers import GUIHelpers

class EpisodeInfo(object):
    visibility = 4100
    channelName = 4101
    seriesName = 4102
    subtitle = 4103
    airDate = 4104
    duration = 4105
    cast = 4106
    description = 4107

class DVR(xbmcgui.WindowXMLDialog):
    C_MENU_SELECTED_INDEX = 6
    
    C_MENU_OPTION_1 = 4001
    C_MENU_OPTION_2 = 4002
    C_MENU_OPTION_3 = 4003
    C_MENU_OPTION_4 = 4004
    C_MENU_OPTION_5 = 4005
    C_MENU_OPTION_6 = 4006
    C_MENU_OPTION_7 = 4007
    C_MENU_OPTION_8 = 4008
    C_MENU_OPTION_9 = 4009
    C_MENU_OPTION_10 = 4010
    C_MENU_OPTION_11 = 4011
    C_MENU_OPTION_12 = 4012
    
    C_MENU_ICON_1 = 4301
    C_MENU_ICON_2 = 4302
    C_MENU_ICON_3 = 4303
    C_MENU_ICON_4 = 4304
    C_MENU_ICON_5 = 4305
    C_MENU_ICON_6 = 4306
    C_MENU_ICON_7 = 4307
    C_MENU_ICON_8 = 4308
    C_MENU_ICON_9 = 4309
    C_MENU_ICON_10 = 4310
    C_MENU_ICON_11 = 4311
    C_MENU_ICON_12 = 4312
    
    C_MENU_LEFT_ARROW = 4350
    C_MENU_RIGHT_ARROW = 4351
    C_MENU_OK_BUTTON = 4352
    
    C_SUBMENU_VISIBILITY = 4200
    C_SUBMENU_OPTION_1 = 4201
    C_SUBMENU_OPTION_2 = 4202
    C_SUBMENU_OPTION_3 = 4203
    C_SUBMENU_OPTION_4 = 4204
    C_SUBMENU_OPTION_5 = 4205
    C_SUBMENU_OPTION_6 = 4206
    C_SUBMENU_OPTION_7 = 4207
    
    mainMenuControls = [
        C_MENU_OPTION_1,
        C_MENU_OPTION_2,
        C_MENU_OPTION_3,
        C_MENU_OPTION_4,
        C_MENU_OPTION_5,
        C_MENU_OPTION_6,
        C_MENU_OPTION_7,
        C_MENU_OPTION_8,
        C_MENU_OPTION_9,
        C_MENU_OPTION_10,
        C_MENU_OPTION_11,
        C_MENU_OPTION_12
    ]
    
    mainMenuIconControls = [
        C_MENU_ICON_1,
        C_MENU_ICON_2,
        C_MENU_ICON_3,
        C_MENU_ICON_4,
        C_MENU_ICON_5,
        C_MENU_ICON_6,
        C_MENU_ICON_7,
        C_MENU_ICON_8,
        C_MENU_ICON_9,
        C_MENU_ICON_10,
        C_MENU_ICON_11,
        C_MENU_ICON_12
    ]
    
    submenuControls = [
        C_SUBMENU_OPTION_1,
        C_SUBMENU_OPTION_2,
        C_SUBMENU_OPTION_3,
        C_SUBMENU_OPTION_4,
        C_SUBMENU_OPTION_5,
        C_SUBMENU_OPTION_6,
        C_SUBMENU_OPTION_7
    ]

    def __new__(cls):
        return super(DVR, cls).__new__(cls, 'script-tvguide-dvr.xml', ADDON.getAddonInfo('path'))

    def __init__(self):
        super(DVR, self).__init__()

    @buggalo.buggalo_try_except({'method' : 'DVR.onInit'})
    def onInit(self):
        self._prepareMenuOptions()
        self.menu = MenuHelper(self, self.menuOptions, self.mainMenuControls, self.mainMenuIconControls, 
                               self.C_MENU_LEFT_ARROW, self.C_MENU_RIGHT_ARROW, self.C_MENU_OK_BUTTON, self.C_MENU_SELECTED_INDEX,
                               self.submenuControls, None, None, True)
        self._showSubMenu()
        GUIHelpers.hide(self, self.C_SUBMENU_VISIBILITY)
        GUIHelpers.hide(self, EpisodeInfo.visibility)

    @buggalo.buggalo_try_except({'method' : 'DVR.onAction'})
    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU]:
            self.close()
            return

        if action.getId() in [ACTION_LEFT]:
            if isinstance(self.menu.parentMenu, MenuHelper):
                self.menu = self.menu.parentMenu
                self.menu.render()
            else:
                self.close()
                return

        if action.getId() in [ACTION_SELECT_ITEM, ACTION_RIGHT]:
            curItem = self.menu.getSelectedMenuItem()
            if 'Submenu' in curItem:
                self.menu = MenuHelper(self, curItem['Submenu'], self.mainMenuControls, self.mainMenuIconControls, 
                               self.C_MENU_LEFT_ARROW, self.C_MENU_RIGHT_ARROW, self.C_MENU_OK_BUTTON, self.C_MENU_SELECTED_INDEX,
                               self.submenuControls, self.menu, 0, True)
            else:
                if curItem['Type'] == 'E':
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": "1", "method": "Player.Open", "params":{"item": {"episodeid": %d}}}' % curItem['ActionId'])
                    self.close()
                elif curItem['Type'] == 'M':
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": "1", "method": "Player.Open", "params":{"item": {"movieid": %d}}}' % curItem['ActionId'])
                    self.close()

        elif action.getId() in [ACTION_UP]:
            self.menu.moveUpOne()

        elif action.getId() in [ACTION_DOWN]:
            self.menu.moveDownOne()

        self._showSubMenu()
        return

    def _showSubMenu(self):
        if 'Submenu' in self.menu.getSelectedMenuItem():
            GUIHelpers.show(self, self.C_SUBMENU_VISIBILITY)
        else:
            GUIHelpers.hide(self, self.C_SUBMENU_VISIBILITY)

    def _prepareMenuOptions(self):
        #Sample Playback JSONRPC Payload Format
        #  { "jsonrpc": "2.0", "id": "1", "method": "Player.Open", "params":{"item": {"episodeid": 21}}}
        self.menuOptions = []
        jsonQuery = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"limits": { "start" : 0, "end": 100 }, "properties": ["showtitle", "title","playcount", "firstaired"], "sort": {"method": "dateadded", "order": "descending"} }, "id": "0"}')
        jsonResponse = unicode(jsonQuery, 'utf-8', errors='ignore')
        jsonObject = simplejson.loads(jsonResponse)
        if jsonObject.has_key('result') and jsonObject['result'] != None and jsonObject['result'].has_key('episodes'):
            shows = []
            for episode in jsonObject['result']['episodes']:
                showIndex = None
                try:
                    showIndex = shows.index(episode['showtitle'])
                    debug('Found %s at index: %s' % (episode['showtitle'], showIndex))
                except ValueError:
                    shows.append(episode['showtitle'])
                    self.menuOptions.append({'ActionId':episode['episodeid'], 'Label':episode['showtitle'], 'Type':'E', 'Episode':episode})
                #Check if the show already existed in the list (then we are adding another episode)
                if showIndex != None:
                    #Create the submenu element if it doesn't already exist
                    if 'Submenu' not in self.menuOptions[showIndex]:
                        #Readd the first encountered episode
                        self.menuOptions[showIndex]['Submenu'] = [{'ActionId':self.menuOptions[showIndex]['ActionId'], 'Label':self.menuOptions[showIndex]['Episode']['title'], 'Type':'E'}]
                    #Add the current episode to the list
                    self.menuOptions[showIndex]['Submenu'].append({'ActionId':episode['episodeid'], 'Label':episode['title'], 'Type':'E'})
                else:
                    showIndex = len(self.menuOptions) - 1
        #Add 10 recent movies
        jsonQuery = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"limits": { "start" : 0, "end": 10 }, "properties": ["title","playcount"], "sort": {"method": "dateadded", "order": "descending"} }, "id": "0"}')
        jsonResponse = unicode(jsonQuery, 'utf-8', errors='ignore')
        jsonObject = simplejson.loads(jsonResponse)
        if jsonObject.has_key('result') and jsonObject['result'] != None and jsonObject['result'].has_key('movies'):
            for movie in jsonObject['result']['movies']:
                self.menuOptions.append({'ActionId':movie['movieid'], 'Label':movie['title'], 'Type':'M', 'Movie':movie})

#        self.menuOptions = [
#            {'ActionId':0, 'Label':'Mission Impossible III'},
#            {'ActionId':0, 'Label':'How I Made My Millions'},
#            {'ActionId':0, 'Label':'Bering Sea Gold'},
#            {'ActionId':0, 'Label':'Gold Rush'},
#            {'ActionId':0, 'Label':'Attack of the Show'},
#            {'ActionId':0, 'Label':'Jungle Gold'},
#            {'ActionId':0, 'Label':'Panic 9-1-1', 'Submenu':[
#                {'ActionId':0, 'Label':'Sub item 1'},
#                {'ActionId':0, 'Label':'Sub item 2'},
#                {'ActionId':0, 'Label':'Sub item 3'},
#                {'ActionId':0, 'Label':'Sub item 4', 'Submenu':[
#                    {'ActionId':0, 'Label':'Super Sub item 1'},
#                    {'ActionId':0, 'Label':'Super Sub item 2'},
#                    {'ActionId':0, 'Label':'Super Sub item 3'},
#                    {'ActionId':0, 'Label':'Super Sub item 4'},
#                    {'ActionId':0, 'Label':'Super Sub item 5'},
#                    {'ActionId':0, 'Label':'Super Sub item 6'},
#                    {'ActionId':0, 'Label':'Super Sub item 7'},
#                    {'ActionId':0, 'Label':'Super Sub item 8'}]
#                },
#                {'ActionId':0, 'Label':'Sub item 5'},
#                {'ActionId':0, 'Label':'Sub item 6'},
#                {'ActionId':0, 'Label':'Sub item 7'},
#                {'ActionId':0, 'Label':'Sub item 8'}]
#            },
#            {'ActionId':0, 'Label':'Toy Story'},
#            {'ActionId':0, 'Label':'The Code'},
#            {'ActionId':0, 'Label':'Breaking Code, Broken Something'},
#            {'ActionId':0, 'Label':'Clash of the Titans'},
#            {'ActionId':0, 'Label':'The League'},
#            {'ActionId':0, 'Label':'Another Item'},
#            {'ActionId':0, 'Label':'Southpark'},
#            {'ActionId':0, 'Label':'Family Guy'},
#            {'ActionId':0, 'Label':'Something About Mary'}]

    @buggalo.buggalo_try_except({'method' : 'DVR.onClick'})
    def onClick(self, controlId):
        self.close()

    def onFocus(self, controlId):
        pass

    def getSelectedMenuOption(self):
        return self.menu.getSelectedMenuItem()
