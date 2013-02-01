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
import re
import xbmc

class TVDB(object):
    def __init__(self, api_key='01F0668B2FC765B9'):
        self.apikey = api_key
        
        # TheTVDB Urls for reference
        self.urls = {
            'defaultURL'        :  'http://thetvdb.com',
            'getSeriesID'       :  '%s/api/GetSeries.php?seriesname=%s&language=%s',     # defaultURL, series_name, language
            'getMirrors'        :  '%s/api/%s/mirrors.xml',                              # defaultURL, apikey
            'bannerURL'         :  '%s/banners/',                                        # baseBannerURL, append bannerFilename.ext
            'apiURL'            :  '%s/api/%s',                                          # mirrorURL, apikey
            'getLanguages'      :  '%s/languages.xml',                                   # apiURL
            'getSeries'         :  '%s/series/%s/%s.xml',                                # apiURL, seriesid, language
            'getSeriesAll'      :  '%s/series/%s/all/%s.%s',                             # apiURL, seriesid, language, (xml|zip)
            'getSeriesActors'   :  '%s/series/%s/actors.xml',                            # apiURL, seriesid
            'getSeriesBanner'   :  '%s/series/%s/banners.xml',                           # apiURL, seriesid
            'getEpisode'        :  '%s/series/%s/default/%s/%s/%s.xml',                  # apiURL, seriesid, season, episode, language
            'getEpisodeDVD'     :  '%s/series/%s/dvd/%s/%s/%s.xml',                      # apiURL, seriesid, season, episode, language
            'getEpisodeAbs'     :  '%s/series/%s/absolute/%s/%s.xml',                    # apiURL, seriesid, absolute_episode, language
            'getEpisodeID'      :  '%s/episodes/%s/%s.xml',                              # apiURL, episodeid, language
            'getUpdates'        :  '%s/updates/updates_%s.%s',                           # apiURL, (day|week|month|all), (xml|zip)

            'getEpisodeByAirDate'  :  '%s/api/GetEpisodeByAirDate.php?apikey=%s&seriesid=%s&airdate=%s&language=%s',
            'GetSeriesByRemoteID'  :  '%s/api/GetSeriesByRemoteID.php?zap2it=%s',
            'getRatingsForUser'    :  '%s/api/GetRatingsForUser.php?apikey=%s&accountid=%s&seriesid=%s',
            'getRatingsForUserAll' :  '%s/api/GetRatingsForUser.php?apikey=%s&accountid=%s'
        }

    def __repr__(self):
        return 'TVDB(apikey=%s)' % (self.apikey)

    def _get(self, url):
        xbmc.log('[script.tvguide.TVDB] Url: %s' % (url), xbmc.LOGDEBUG)
        f = urllib2.urlopen(url)
        a = f.read()
        f.close()
        return a

    def getIdByZap2it(self, zap2it_id):
        url = 'http://thetvdb.com/api/GetSeriesByRemoteID.php?%s' % (urllib.urlencode({'zap2it': zap2it_id})) #example: EP01158384
        a = self._get(url)
        tvdbid = 0
        tvdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
        match = tvdbidRE.search(a)
        if match:
            tvdbid = match.group(1)
        return tvdbid

    def getEpisodeByAirdate(self, tvdbid, airdate):
        url = 'http://thetvdb.com/api/GetEpisodeByAirDate.php?%s' % (urllib.urlencode({'apikey': self.apikey, 'seriesid' : tvdbid, 'airdate' : airdate}))
        return self._get(url)
        
    def getIdByShowName(self, showName):
        url = 'http://thetvdb.com/api/GetSeries.php?%s' % (urllib.urlencode({'seriesname': showName})) #example: The Good Wife
        a = self._get(url)
        #NOTE: This assumes an exact match. It is possible to get multiple results though. This could be smarter
        tvdbid = 0
        tvdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
        match = tvdbidRE.search(a)
        if match:
            tvdbid = match.group(1)
        return tvdbid
