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
import datetime

from resources.lib.source_abstract import *
from resources.lib.apis.ysapi import *
from resources.lib.models.channel import *
from resources.lib.models.program import *

class YouSeeTvSource(Source):
    KEY = 'youseetv'

    def __init__(self, addon):
        self.date = datetime.datetime.today()
        self.channelCategory = addon.getSetting('youseetv.category')
        self.ysApi = YouSeeTVGuideApi()

    def getDataFromExternal(self, date, progress_callback = None):
        channels = self.ysApi.channelsInCategory(self.channelCategory)
        for idx, channel in enumerate(channels):
            c = Channel(id = channel['id'], title = channel['name'], logo = channel['logo'])
            yield c

            for program in self.ysApi.programs(c.id, tvdate = date):
                description = program['description']
                if description is None:
                    description = strings(NO_DESCRIPTION)

                imagePrefix = program['imageprefix']

                p = Program(
                    c,
                    program['title'],
                    self._parseDate(program['begin']),
                    self._parseDate(program['end']),
                    description,
                    imagePrefix + program['images_sixteenbynine']['large'],
                    imagePrefix + program['images_sixteenbynine']['small']
                )
                yield p


            if progress_callback:
                if not progress_callback(100.0 / len(channels) * idx):
                    raise SourceUpdateCanceledException()

    def _parseDate(self, dateString):
        return datetime.datetime.fromtimestamp(dateString)
