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
import urllib
import urllib2
import json
import xbmc

class SickBeard(object):
    def __init__(self, base_url='http://localhost:8081', api_key='cf6a9873e3f6dd25abbb654c7e362d9d'):
        self.apikey = api_key
        self.baseurl = base_url

    def __repr__(self):
        return 'SickBeard(base_url=%s, apikey=%s)' % (self.baseurl, self.apikey)

    def _get(self, url):
        f = urllib2.urlopen(url)
        a = f.read()
        f.close()
        return a

    def _exec(self, cmd, parms, response):
        parmsCopy = parms.copy()
        parmsCopy.update({'cmd' : cmd})
        url = '%s/api/%s/?%s' % (self.baseurl, self.apikey, urllib.urlencode(parmsCopy))
        xbmc.log('[script.tvguide.SickBeard] Url: %s' % (url), xbmc.LOGDEBUG)
        f = urllib2.urlopen(url)
        a = f.read()
        f.close()
        j = json.loads(a)
        response = j
        return j['result'] == 'success'

    def isShowManaged(self, tvdbid):
        return self._exec('show', {'tvdbid': tvdbid}, json)

    def addNewShow(self, tvdbid, flatten=0, status='skipped'):
        xbmc.log('[script.tvguide.SickBeard.addNewShow] tvdbid=%s, flatten=%s, status=%s' % (tvdbid, flatten, status), xbmc.LOGDEBUG)
        return self._exec('show.addnew', {'tvdbid': tvdbid, 'flatten_folders' : flatten, 'status' : status}, json)

    # Get the show ID numbers
    def getShowIds(self):
        show_ids=[]
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+"?cmd=shows"))
        for each in result['data']:
            show_ids.append(each)
        return show_ids

    # Get show info dict, key:show_name value:tvdbid
    def getShowInfo(self, show_ids):
        show_info={}
        for id in show_ids:
            result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show&tvdbid='+id))
            name=result['data']['show_name']
            paused=result['data']['paused']
            show_info[name] = [id, paused]
        return show_info

    # Returns the details of a show from Sickbeard 
    def getShowDetails(self, show_id):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show&tvdbid='+show_id))
        details=result['data']
        
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show.stats&tvdbid='+show_id))
        total=result['data']['total']
        
        return details, total

    # Return a list of season numbers
    def getSeasonNumberList(self, show_id):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show.seasonlist&tvdbid='+show_id))
        season_number_list = result['data']
        season_number_list.sort()
        return season_number_list

    # Get the list of episodes ina given season
    def getSeasonEpisodeList(self, show_id, season):
        season = str(season)
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show.seasons&tvdbid='+show_id+'&season='+season))
        season_episodes = result['data']
            
        for key in season_episodes.iterkeys():
            if int(key) < 10:
                newkey = '{0}'.format(key.zfill(2))
                if newkey not in season_episodes:
                    season_episodes[newkey] = season_episodes[key]
                    del season_episodes[key]
        
        return season_episodes

    # Gets the show banner from Sickbeard    
    def getShowBanner(self, show_id):
        result = baseurl+'/showPoster/?show='+str(show_id)+'&which=banner'
        return result

    # Check if there is a cached thumbnail to use, if not use Sickbeard poster
    def getShowPoster(self, show_id):
        return baseurl+'/showPoster/?show='+str(show_id)+'&which=poster'

    # Get list of upcoming episodes
    def getFutureShows(self):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=future&sort=date&type=today|soon'))
        future_list = result['data']
        return future_list

    # Return a list of the last 20 snatched/downloaded episodes    
    def getHistory(self):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=history&limit=20'))
        history = result['data']
        return history

    # Search the tvdb for a show using the Sickbeard API    
    def searchShowName(self, name):
        search_results = []
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=sb.searchtvdb&name='+name+'&lang=en'))
        for each in result['data']['results']:
            search_results.append(each)
        return search_results

    # Return a list of the default settings for adding a new show
    def getDefaults(self):
        defaults_result = json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=sb.getdefaults'))
        print defaults_result.keys()
        defaults_data = defaults_result['data']
        defaults = [defaults_data['status'], defaults_data['flatten_folders'], str(defaults_data['initial'])]
        return defaults

    # Return a list of the save paths set in Sickbeard
    def getRoodDirs(self):
        directory_result = json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=sb.getrootdirs'))
        directory_result = directory_result['data']
        return directory_result

    # Get the version of Sickbeard
    def getSickbeardVersion(self):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=sb'))
        version = result['data']['sb_version']
        return version

    # Set the status of an episode
    def setShowStatus(self, tvdbid, season, ep, status):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=episode.setstatus&tvdbid='+str(tvdbid)+'&season='+str(season)+'&episode='+str(ep)+'&status='+status))
        return result

    # Return a list of the last 20 snatched/downloaded episodes    
    def forceSearch(self):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=sb.forcesearch'))
        success = result['result']
        settings.messageWindow("Force Search", "Force search returned "+success)

    def setPausedState(self, paused, show_id):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show.pause&tvdbid='+show_id+'&pause='+paused))
        message = result['message']
        return message

    def manualSearch(self, tvdbid, season, ep):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=episode.search&tvdbid='+str(tvdbid)+'&season='+str(season)+'&episode='+str(ep)))
        message = result['message']
        return message    

    def deleteShow(self, tvdbid):
        result=json.load(urllib.urlopen(('%s/api/%s/' % (self.baseurl, self.apikey))+'?cmd=show.delete&tvdbid='+str(tvdbid)))
        message = result['message']
        return message     