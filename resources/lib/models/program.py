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


#Rob Newton - 20130130 - Added series_id, movie_id, episode_id, season_number, episode_number, category, new, in_sickbeard, in_couchpotato
class Program(object):
    def __init__(self, channel, title, startDate, endDate, description, imageLarge = None, imageSmall=None, seriesId=0, movieId=0, episodeId=0, seasonNumber=0, episodeNumber=0, category='other', new=0, sickbeardManaged=0, couchpotatoManaged=0, notificationScheduled = None):
        """

        @param channel:
        @type channel: source.Channel
        @param title:
        @param startDate:
        @param endDate:
        @param description:
        @param imageLarge:
        @param imageSmall:
        @param seriesId:
        @param movieId:
        @param episodeId:
        @param seasonNumber:
        @param episodeNumber:
        @param category:
        @param new:
        @param sickbeardManaged:
        @param couchpotatoManaged:
        @param notificationScheduled:
        """
        self.channel = channel
        self.title = title
        self.startDate = startDate
        self.endDate = endDate
        self.description = description
        self.imageLarge = imageLarge
        self.imageSmall = imageSmall
        self.seriesId = seriesId
        self.movieId = movieId
        self.episodeId = episodeId
        self.seasonNumber = seasonNumber
        self.episodeNumber = episodeNumber
        self.category = category
        self.new = new
        self.sickbeardManaged = sickbeardManaged
        self.couchpotatoManaged = couchpotatoManaged
        self.notificationScheduled = notificationScheduled

    def __repr__(self):
        return 'Program(channel=%s, title=%s, startDate=%s, endDate=%s, description=%s, imageLarge=%s, imageSmall=%s, seriesId=%s, movieId=%s, episodeId=%s, seasonNumber=%s, episodeNumber=%s, category=%s, new=%s, sickbeardManaged=%s, couchpotatoManaged=%s, notificationScheduled=%s)' % \
            (self.channel, self.title, self.startDate, self.endDate, self.description, self.imageLarge, self.imageSmall, self.seriesId, self.movieId, self.episodeId, self.seasonNumber, self.episodeNumber, self.category, self.new, self.sickbeardManaged, self.couchpotatoManaged, self.notificationScheduled)
