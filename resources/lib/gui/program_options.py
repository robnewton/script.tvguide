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
import buggalo
import datetime

from resources.lib.globals import *
from resources.lib.strings import *
from resources.lib.gui.menu_helper import MenuHelper

class ProgramType(object):
    MOVIE = 100
    MOVIE_FUTURE = 101
    EPISODE = 102
    EPISODE_FUTURE = 103

class ProgramAction(object):
    TUNE_TO_CHANNEL = 5000
    WATCH_NOW = 5001
    RECORD = 5002
    RECORD_EPISODE = 5003
    RECORD_SERIES = 5004
    RECORD_SERIES_W_OPTIONS = 5005
    SET_REMINDER = 5006
    FULL_INFO = 5007
    MORE_LIKE_THIS = 5008
    UPCOMING_SHOWS = 5009
    EXIT = 5010
    CANCEL_RECORDING = 5011
    CANCEL_SERIES = 5012
    MODIFY_SERIES = 5013

class ProgramOptions(xbmcgui.WindowXMLDialog):
    C_MENU_OPTION_1 = 4001
    C_MENU_OPTION_2 = 4002
    C_MENU_OPTION_3 = 4003
    C_MENU_OPTION_4 = 4004
    C_MENU_OPTION_5 = 4005
    C_MENU_OPTION_6 = 4006
    C_MENU_OPTION_7 = 4007
    C_MENU_OPTION_8 = 4008
    
    C_PROGRAM_CHANNEL = 4100
    C_PROGRAM_NAME = 4101
    C_PROGRAM_DATE = 4102
    C_PROGRAM_GENRE = 4103
    C_PROGRAM_EPISODE_MOVIE_LABEL = 4110
    C_PROGRAM_EPISODE_MOVIE_INFO = 4104
    C_PROGRAM_CAST = 4105
    C_PROGRAM_START_TIME = 4106
    C_PROGRAM_END_TIME = 4107
    C_PROGRAM_DESCRIPTION = 4108
    C_PROGRAM_PROGRESS = 4109
    
    controls = [
        C_MENU_OPTION_1,
        C_MENU_OPTION_2,
        C_MENU_OPTION_3,
        C_MENU_OPTION_4,
        C_MENU_OPTION_5,
        C_MENU_OPTION_6,
        C_MENU_OPTION_7,
        C_MENU_OPTION_8
    ]

    def __new__(cls, program):
        return super(ProgramOptions, cls).__new__(cls, 'script-tvguide-programoptions.xml', ADDON.getAddonInfo('path'))

    def __init__(self, program):
        """
        @param program:
        @type program: source.Program
        """
        super(ProgramOptions, self).__init__()
        self.program = program

        if program.category == 'Movie':
            if self.program.startDate > datetime.datetime.today():
                self.type = ProgramType.MOVIE_FUTURE
            else:
                self.type = ProgramType.MOVIE
        else:
            if self.program.startDate > datetime.datetime.today():
                self.type = ProgramType.EPISODE_FUTURE
            else:
                self.type = ProgramType.EPISODE

    @buggalo.buggalo_try_except({'method' : 'ProgramOptions.onInit'})
    def onInit(self):
        self._prepareMenuOptions()
        self.menu = MenuHelper(self, self.menuOptions, self.controls, [], 0, 0, 0, 2)
        self._renderProgramInfo()
        #if not self.program.channel.isPlayable():
        #    playControl.setEnabled(False)
        #if self.program.channel.logo is not None:
        #    channelLogoControl.setImage(self.program.channel.logo)
        #    channelTitleControl.setVisible(False)

    @buggalo.buggalo_try_except({'method' : 'ProgramOptions.onAction'})
    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU, ACTION_LEFT]:
            self.close()
            return

        if action.getId() in [ACTION_SELECT_ITEM]:
            self.close()
            return

        elif action.getId() in [ACTION_UP]:
            self.menu.moveUpOne()
            return

        elif action.getId() in [ACTION_DOWN]:
            self.menu.moveDownOne()
            return

    def _renderProgramInfo(self):
        channelControl = self.getControl(self.C_PROGRAM_CHANNEL)
        if channelControl:
            channelControl.setLabel('[B]%s[/B]' % (self.program.channel.title))

        nameControl = self.getControl(self.C_PROGRAM_NAME)
        if nameControl:
            nameControl.setLabel('[B]%s[/B]' % (self.program.title))

        dateControl = self.getControl(self.C_PROGRAM_DATE)
        if dateControl:
            dateControl.setLabel('[B]%s - %s (%d min) on %s[/B]' % (self.program.startDate.strftime("%I:%M %p").lstrip('0'), self.program.endDate.strftime("%I:%M %p").lstrip('0'),(self.program.endDate - self.program.startDate).seconds / 60, self.program.startDate.strftime("%a %d/%m/%y")))

        genreControl = self.getControl(self.C_PROGRAM_GENRE)
        if genreControl:
            genreControl.setLabel('[B]%s[/B]' % (self.program.category))

        episodeMovieLabelControl = self.getControl(self.C_PROGRAM_EPISODE_MOVIE_LABEL)
        episodeMovieInfoControl = self.getControl(self.C_PROGRAM_EPISODE_MOVIE_INFO)
        if self.type == ProgramType.MOVIE:
            if episodeMovieLabelControl:
                episodeMovieLabelControl.setLabel('[B]Movie Yr:[/B]')
            if episodeMovieInfoControl:
                episodeMovieInfoControl.setLabel('[B]%s[/B]' % ('1500'))
        else:
            if episodeMovieLabelControl:
                episodeMovieLabelControl.setLabel('[B]Episode:[/B]')
            if episodeMovieInfoControl:
                episodeMovieInfoControl.setLabel('[B]"%s" (AirDate: %s)[/B]' % (self.program.title, '0/0/00'))

        castControl = self.getControl(self.C_PROGRAM_CAST)
        if castControl:
            castControl.setLabel('[B]%s[/B]' % ('cast info not available'))

        startTimeControl = self.getControl(self.C_PROGRAM_START_TIME)
        if startTimeControl:
            startTimeControl.setLabel('[B]%s[/B]' % (self.program.startDate.strftime("%I:%M %p").lstrip('0')))

        endTimeControl = self.getControl(self.C_PROGRAM_END_TIME)
        if endTimeControl:
            endTimeControl.setLabel('[B]%s[/B]' % (self.program.endDate.strftime("%I:%M %p").lstrip('0')))

        descriptionControl = self.getControl(self.C_PROGRAM_DESCRIPTION)
        if descriptionControl:
            descriptionControl.setLabel('[B]%s[/B]' % (self.program.description))

        progressControl = self.getControl(self.C_PROGRAM_PROGRESS)
        if progressControl:
            if datetime.datetime.today() > self.program.endDate:
                percent = 100
            else:
                percent = (self.program.endDate - datetime.datetime.today()).seconds / (self.program.endDate - self.program.startDate).seconds
            progressControl.setPercent(percent)

    def _prepareMenuOptions(self):
        if self.type == ProgramType.MOVIE:
            self.menuOptions = [
                {'ActionId':ProgramAction.WATCH_NOW, 'Label':'Watch Now'},
                {'ActionId':ProgramAction.RECORD, 'Label':'Record'},
                {'ActionId':ProgramAction.FULL_INFO, 'Label':'Full Info'},
                {'ActionId':ProgramAction.MORE_LIKE_THIS, 'Label':'More Like This'},
                {'ActionId':ProgramAction.UPCOMING_SHOWS, 'Label':'Upcoming Shows'},
                {'ActionId':ProgramAction.EXIT, 'Label':'Exit'}]
        elif self.type == ProgramType.MOVIE_FUTURE:
            self.menuOptions = [
                {'ActionId':ProgramAction.TUNE_TO_CHANNEL, 'Label':'Tune to Channel'},
                {'ActionId':ProgramAction.RECORD, 'Label':'Record'},
                {'ActionId':ProgramAction.SET_REMINDER, 'Label':'Set Reminder'},
                {'ActionId':ProgramAction.FULL_INFO, 'Label':'Full Info'},
                {'ActionId':ProgramAction.MORE_LIKE_THIS, 'Label':'More Like This'},
                {'ActionId':ProgramAction.UPCOMING_SHOWS, 'Label':'Upcoming Shows'},
                {'ActionId':ProgramAction.EXIT, 'Label':'Exit'}]
        elif self.type == ProgramType.EPISODE:
            if self.program.sickbeardManaged:
                self.menuOptions = [
                    {'ActionId':ProgramAction.WATCH_NOW, 'Label':'Watch Now'},
                    {'ActionId':ProgramAction.CANCEL_RECORDING, 'Label':'Cancel This Recording'},
                    {'ActionId':ProgramAction.CANCEL_SERIES, 'Label':'Cancel This Series'},
                    {'ActionId':ProgramAction.MODIFY_SERIES, 'Label':'Modify Series'},
                    {'ActionId':ProgramAction.FULL_INFO, 'Label':'Full Info'},
                    {'ActionId':ProgramAction.UPCOMING_SHOWS, 'Label':'Upcoming Shows'},
                    {'ActionId':ProgramAction.EXIT, 'Label':'Exit'}]
            else:
                self.menuOptions = [
                    {'ActionId':ProgramAction.WATCH_NOW, 'Label':'Watch Now'},
                    {'ActionId':ProgramAction.RECORD_EPISODE, 'Label':'Record Episode'},
                    {'ActionId':ProgramAction.RECORD_SERIES, 'Label':'Record Series'},
                    {'ActionId':ProgramAction.RECORD_SERIES_W_OPTIONS, 'Label':'Record Series w Options'},
                    {'ActionId':ProgramAction.FULL_INFO, 'Label':'Full Info'},
                    {'ActionId':ProgramAction.UPCOMING_SHOWS, 'Label':'Upcoming Shows'},
                    {'ActionId':ProgramAction.EXIT, 'Label':'Exit'}]
        elif self.type == ProgramType.EPISODE_FUTURE:
            if self.program.sickbeardManaged:
                self.menuOptions = [
                    {'ActionId':ProgramAction.TUNE_TO_CHANNEL, 'Label':'Tune to Channel'},
                    {'ActionId':ProgramAction.CANCEL_RECORDING, 'Label':'Cancel This Recording'},
                    {'ActionId':ProgramAction.CANCEL_SERIES, 'Label':'Cancel This Series'},
                    {'ActionId':ProgramAction.MODIFY_SERIES, 'Label':'Modify Series'},
                    {'ActionId':ProgramAction.SET_REMINDER, 'Label':'Set Reminder'},
                    {'ActionId':ProgramAction.FULL_INFO, 'Label':'Full Info'},
                    {'ActionId':ProgramAction.UPCOMING_SHOWS, 'Label':'Upcoming Shows'},
                    {'ActionId':ProgramAction.EXIT, 'Label':'Exit'}]
            else:
                self.menuOptions = [
                    {'ActionId':ProgramAction.TUNE_TO_CHANNEL, 'Label':'Tune to Channel'},
                    {'ActionId':ProgramAction.RECORD_EPISODE, 'Label':'Record Episode'},
                    {'ActionId':ProgramAction.RECORD_SERIES, 'Label':'Record Series'},
                    {'ActionId':ProgramAction.RECORD_SERIES_W_OPTIONS, 'Label':'Record Series w Options'},
                    {'ActionId':ProgramAction.SET_REMINDER, 'Label':'Set Reminder'},
                    {'ActionId':ProgramAction.FULL_INFO, 'Label':'Full Info'},
                    {'ActionId':ProgramAction.UPCOMING_SHOWS, 'Label':'Upcoming Shows'},
                    {'ActionId':ProgramAction.EXIT, 'Label':'Exit'}]

    @buggalo.buggalo_try_except({'method' : 'ProgramOptions.onClick'})
    def onClick(self, controlId):
        self.close()

    def onFocus(self, controlId):
        pass

    def getSelectedMenuOption(self):
        return self.menu.getSelectedMenuItem()
