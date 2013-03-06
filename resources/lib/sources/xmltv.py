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
import time
import xbmcvfs
import os
from xml.etree import ElementTree

from resources.lib.source_abstract import *
from resources.lib.utils.file_wrapper import *
from resources.lib.apis.sickbeard import *
from resources.lib.apis.couchpotato import *
from resources.lib.apis.tvdb import *
from resources.lib.apis.tmdb import *
from resources.lib.globals import *
from resources.lib.strings import *
from resources.lib.models.channel import *
from resources.lib.models.program import *

class XMLTVSource(Source):
    KEY = 'xmltv'

    def __init__(self, addon):
        self.logoFolder = addon.getSetting('xmltv.logo.folder')
        self.xmltvFile = addon.getSetting('xmltv.file')

        if not self.xmltvFile or not xbmcvfs.exists(self.xmltvFile):
            raise SourceNotConfiguredException()

    def getDataFromExternal(self, date, progress_callback = None):
        f = FileWrapper(self.xmltvFile)
        context = ElementTree.iterparse(f, events=("start", "end"))
        return parseXMLTV(context, f, f.size, self.logoFolder, progress_callback)

    def isUpdated(self, lastUpdated):
        if hasattr(xbmcvfs, 'Stat'):
            stat = xbmcvfs.Stat(self.xmltvFile)
            mtime = stat.st_mtime()
        else:
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.stat(self.xmltvFile)

        fileUpdated = datetime.datetime.fromtimestamp(mtime)
        return fileUpdated > lastUpdated

def parseXMLTVDate(dateString):
    if dateString is not None:
        if dateString.find(' ') != -1:
            # remove timezone information
            dateString = dateString[:dateString.find(' ')]
        t = time.strptime(dateString, '%Y%m%d%H%M%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    else:
        return None

def parseXMLTV(context, f, size, logoFolder, progress_callback):
    event, root = context.next()
    elements_parsed = 0

    #Rob Newton - 20130131 - Only need to instantiate these once
    tmdbAPI = TMDB(ADDON.getSetting('tmdb.apikey'))
    tvdbAPI = TVDB(ADDON.getSetting('tvdb.apikey'))
    sbAPI = SickBeard(ADDON.getSetting('sickbeard.baseurl'),ADDON.getSetting('sickbeard.apikey'))
    cpAPI = CouchPotato(ADDON.getSetting('couchpotato.baseurl'),ADDON.getSetting('couchpotato.apikey'))
    
    for event, elem in context:
        if event == "end":
            result = None
            if elem.tag == "programme":
                channel = elem.get("channel")
                description = elem.findtext("desc")
                iconElement = elem.find("icon")
                icon = None
                if iconElement is not None:
                    icon = iconElement.get("src")
                if not description:
                    description = strings(NO_DESCRIPTION)
                
                #Rob Newton - 20130127 - Parse the category of the program
                movie = False
                category = 'Normal'
                categories = ''
                categoryList = elem.findall("category")
                for cat in categoryList:
                    categories += ', ' + cat.text
                    if cat.text == 'Movie':
                        movie = True
                        category = cat.text
                    elif cat.text == 'Sports':
                        category = cat.text
                    elif cat.text == 'Children':
                        category = 'Kids'
                    elif cat.text == 'Kids':
                        category = cat.text
                    elif cat.text == 'News':
                        category = cat.text
                    elif cat.text == 'Comedy':
                        category = cat.text
                    elif cat.text == 'Drama':
                        category = cat.text
                
                #Trim prepended comma and space (considered storing all categories, but one is ok for now)
                categories = categories[2:]
                debug('Categories identified: %s' % categories)
                
                #If the movie flag was set, it should override the rest (ex: comedy and movie sometimes come together)
                if movie:
                    category = 'Movie'
                
                #Rob Newton - 20130127 - Read the "new" boolean for this program and store as 1 or 0 for the db
                try:
                    if elem.find("new") != None:
                        new = 1
                    else:
                        new = 0
                except:
                    new = 0
                    pass
                
                #Rob Newton - 20130127 - Decipher the TVDB ID by using the Zap2it ID in dd_progid
                tvdbid = 0
                episodeId = 0
                seasonNumber = 0
                episodeNumber = 0
                if not movie and ADDON.getSetting('tvdb.enabled') == 'true':
                    dd_progid = ''
                    episodeNumList = elem.findall("episode-num")
                    for epNum in episodeNumList:
                        if epNum.attrib["system"] == 'dd_progid':
                            dd_progid = epNum.text

                    #debug('dd_progid %s' % dd_progid)

                    #The Zap2it ID is the first part of the string delimited by the dot
                    #  Ex: <episode-num system="dd_progid">MV00044257.0000</episode-num>
                    dd_progid = dd_progid.split('.',1)[0]
                    tvdbid = tvdbAPI.getIdByZap2it(dd_progid)
                    #Sometimes GetSeriesByRemoteID does not find by Zap2it so we use the series name as backup
                    if tvdbid == 0:
                        tvdbid = tvdbAPI.getIdByShowName(elem.findtext('title'))

                    if tvdbid > 0:
                        #Date element holds the original air date of the program
                        airdateStr = elem.findtext('date')
                        if airdateStr != None:
                            try:
                                #Change date format into the byAirDate lookup format (YYYY-MM-DD)
                                t = time.strptime(airdateStr, '%Y%m%d')
                                airDateTime = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                                airdate = airDateTime.strftime('%Y-%m-%d')
                                
                                #Only way to get a unique lookup is to use TVDB ID and the airdate of the episode
                                episode = ElementTree.fromstring(tvdbAPI.getEpisodeByAirdate(tvdbid, airdate))
                                episode = episode.find("Episode")
                                episodeId = episode.findtext("id")
                                seasonNumber = episode.findtext("SeasonNumber")
                                episodeNumber = episode.findtext("EpisodeNumber")
                            except:
                                pass
                
                #Rob Newton - 20130131 - Lookup the movie info from TMDB
                imdbid = 0
                if movie and ADDON.getSetting('tmdb.enabled') == 'true':
                    #Date element holds the original air date of the program
                    movieYear = elem.findtext('date')
                    movieInfo = tmdbAPI.getMovie(elem.findtext('title'), movieYear)
                    imdbid = movieInfo['imdb_id']
                    moviePosterUrl = tmdbAPI.getPosterUrl(movieInfo['poster_path'])
                
                #Rob Newton - 20130130 - Check for show being managed by SickBeard
                sbManaged = 0
                if ADDON.getSetting('sickbeard.enabled') == 'true':
                    if sbAPI.isShowManaged(tvdbid):
                        sbManaged = 1
                
                #Rob Newton - 20130130 - Check for movie being managed by CouchPotato
                cpManaged = 0
                #if ADDON.getSetting('couchpotato.enabled') == 'true':
                #    if cpAPI.isMovieManaged(imdbid):
                #        cpManaged = 1
                
                result = Program(channel, elem.findtext('title'), parseXMLTVDate(elem.get('start')), parseXMLTVDate(elem.get('stop')), description, None, icon, tvdbid, imdbid, episodeId, seasonNumber, episodeNumber, category, new, sbManaged, cpManaged)
                
                debug('new %r' % result)

            elif elem.tag == "channel":
                id = elem.get("id")
                title = elem.findtext("display-name")
                logo = None
                if logoFolder:
                    logoFile = os.path.join(logoFolder.encode('utf-8', 'ignore'), title.encode('utf-8', 'ignore') + '.png')
                    if xbmcvfs.exists(logoFile):
                        logo = logoFile
                if not logo:
                    iconElement = elem.find("icon")
                    if iconElement is not None:
                        logo = iconElement.get("src")
                result = Channel(id, title, logo)

            if result:
                elements_parsed += 1
                if progress_callback and elements_parsed % 500 == 0:
                    if not progress_callback(100.0 / size * f.tell()):
                        raise SourceUpdateCanceledException()
                yield result

        root.clear()
    f.close()