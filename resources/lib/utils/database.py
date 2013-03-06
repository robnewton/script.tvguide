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
import sqlite3
import datetime
import threading
import buggalo
import time
import os

from resources.lib.globals import *
from resources.lib.strings import *
from resources.lib.models.channel import *
from resources.lib.models.program import *

SETTINGS_TO_CHECK = ['source', 'youseetv.category', 'xmltv.file', 'xmltv.logo.folder', 'ontv.url']

def instantiateSource():
    SOURCES = {
        'YouSee.tv' : {'module':'you_see_tv', 'class':'YouSeeTvSource'},
        'XMLTV' : {'module':'xmltv', 'class':'XMLTVSource'},
        'ONTV.dk' : {'module':'ontv', 'class':'ONTVSource'}
    }
    module = __import__('resources.lib.sources.%s' % SOURCES[ADDON.getSetting('source')]['module'], {}, {}, SOURCES[ADDON.getSetting('source')]['class'])  
    activeSource = getattr(module, SOURCES[ADDON.getSetting('source')]['class'])
    return activeSource(ADDON)

class SourceException(Exception):
    pass

class SourceUpdateCanceledException(SourceException):
    pass

class SourceNotConfiguredException(SourceException):
    pass

class DatabaseSchemaException(sqlite3.DatabaseError):
    pass

class Database(object):
    SOURCE_DB = 'source.db'
    CHANNELS_PER_PAGE = 9

    def __init__(self):
        self.conn = None
        self.eventQueue = list()
        self.event = threading.Event()
        self.eventResults = dict()

        self.source = instantiateSource()

        self.updateInProgress = False
        self.updateFailed = False
        self.sourceNotConfigured = False

        #buggalo.addExtraData('source', self.source.KEY)
        #for key in SETTINGS_TO_CHECK:
        #    buggalo.addExtraData('setting: %s' % key, ADDON.getSetting(key))

        self.channelList = list()

        profilePath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        if not os.path.exists(profilePath):
            os.makedirs(profilePath)
        self.databasePath = os.path.join(profilePath, Database.SOURCE_DB)

        threading.Thread(name = 'Database Event Loop', target = self.eventLoop).start()

    def eventLoop(self):
        print 'Database.eventLoop() >>>>>>>>>> starting...'
        while True:
            self.event.wait()
            self.event.clear()

            event = self.eventQueue.pop(0)

            command = event[0]
            callback = event[1]

            print 'Database.eventLoop() >>>>>>>>>> processing command: ' + command.__name__

            try:
                result = command(*event[2:])
                self.eventResults[command.__name__] = result

                if callback:
                    threading.Thread(name = 'Database callback', target = callback).start()

                if self._close == command:
                    del self.eventQueue[:]
                    break


            except Exception:
                print 'Database.eventLoop() >>>>>>>>>> exception!'
                buggalo.onExceptionRaised()

        print 'Database.eventLoop() >>>>>>>>>> exiting...'

    def _invokeAndBlockForResult(self, method, *args):
        event = [method, None]
        event.extend(args)
        self.eventQueue.append(event)
        self.event.set()

        while not self.eventResults.has_key(method.__name__):
            time.sleep(0.1)

        result = self.eventResults.get(method.__name__)
        del self.eventResults[method.__name__]
        return result

    def initialize(self, callback, cancel_requested_callback):
        self.eventQueue.append([self._initialize, callback, cancel_requested_callback])
        self.event.set()

    def _initialize(self, cancel_requested_callback):
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
        sqlite3.register_converter('timestamp', self.convert_datetime)

        self.sourceNotConfigured = False
        while True:
            if cancel_requested_callback is not None and cancel_requested_callback():
                break

            try:
                self.conn = sqlite3.connect(self.databasePath, detect_types=sqlite3.PARSE_DECLTYPES)
                self.conn.execute('PRAGMA foreign_keys = ON')
                self.conn.row_factory = sqlite3.Row

                # create and drop dummy table to check if database is locked
                c = self.conn.cursor()
                c.execute('CREATE TABLE IF NOT EXISTS database_lock_check(id TEXT PRIMARY KEY)')
                c.execute('DROP TABLE database_lock_check')
                c.close()

                self._createTables()
                self.settingsChanged = self._wasSettingsChanged(ADDON)
                break

            except sqlite3.OperationalError:
                if cancel_requested_callback is None:
                    debug('Database is locked, bailing out...')
                    break
                else: # ignore 'database is locked'
                    debug('Database is locked, retrying...')

            except sqlite3.DatabaseError:
                self.conn = None
                try:
                    os.unlink(self.databasePath)
                except OSError:
                    pass
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), strings(DATABASE_SCHEMA_ERROR_1),
                    strings(DATABASE_SCHEMA_ERROR_2), strings(DATABASE_SCHEMA_ERROR_3))

        if self.conn is None:
            self.sourceNotConfigured = True

    def close(self, callback):
        self.eventQueue.append([self._close, callback])
        self.event.set()

    def _close(self):
        try:
            # rollback any non-commit'ed changes to avoid database lock
            self.conn.rollback()
        except sqlite3.OperationalError:
            pass # no transaction is active
        self.conn.close()

    def _wasSettingsChanged(self, addon):
        settingsChanged = False
        noRows = True
        count = 0

        c = self.conn.cursor()
        c.execute('SELECT * FROM settings')
        for row in c:
            noRows = False
            key = row['key']
            if SETTINGS_TO_CHECK.count(key):
                count += 1
                if row['value'] != addon.getSetting(key):
                    settingsChanged = True

        if count != len(SETTINGS_TO_CHECK):
            settingsChanged = True

        if settingsChanged or noRows:
            for key in SETTINGS_TO_CHECK:
                value = addon.getSetting(key).decode('utf-8', 'ignore')
                c.execute('INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)', [key, value])
                if not c.rowcount:
                    c.execute('UPDATE settings SET value=? WHERE key=?', [value, key])
            self.conn.commit()

        c.close()
        print 'Settings changed: ' + str(settingsChanged)
        return settingsChanged


    def _isCacheExpired(self, date):
        if self.settingsChanged:
            return True

        # check if channel data is up-to-date in database
        try:
            c = self.conn.cursor()
            c.execute('SELECT channels_updated FROM sources WHERE id=?', [self.source.KEY])
            row = c.fetchone()
            if not row:
                return True
            lastUpdated = row['channels_updated']
            c.close()

            today = datetime.datetime.now()
            if lastUpdated is None or lastUpdated.day != today.day:
                return True
        except TypeError:
            return True

        # check if program data is up-to-date in database
        dateStr = date.strftime('%Y-%m-%d')
        c = self.conn.cursor()
        c.execute('SELECT programs_updated FROM updates WHERE source=? AND date=?', [self.source.KEY, dateStr])
        row = c.fetchone()
        today = datetime.datetime.now()
        expired = row is None or row['programs_updated'] is None or row['programs_updated'].day != today.day
        c.close()

        if not self.source.isUpdated(date):
            # no reason to update if source has not been modified
            return False

        return expired

    def updateChannelAndProgramListCaches(self, callback, date = datetime.datetime.now(), progress_callback = None, clearExistingProgramList = True):
        self.eventQueue.append([self._updateChannelAndProgramListCaches, callback, date, progress_callback, clearExistingProgramList])
        self.event.set()

    def _updateChannelAndProgramListCaches(self, date, progress_callback, clearExistingProgramList):
        # todo workaround service.py 'forgets' the adapter and convert set in _initialize.. wtf?!
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime)
        sqlite3.register_converter('timestamp', self.convert_datetime)

        if not self._isCacheExpired(date):
            return

        self.updateInProgress = True
        self.updateFailed = False
        dateStr = date.strftime('%Y-%m-%d')
        c = self.conn.cursor()
        try:
            debug('Updating caches...')
            if progress_callback:
                progress_callback(0)

            if self.settingsChanged:
                c.execute('DELETE FROM channels WHERE source=?', [self.source.KEY])
                c.execute('DELETE FROM programs WHERE source=?', [self.source.KEY])
                c.execute("DELETE FROM updates WHERE source=?", [self.source.KEY])
            self.settingsChanged = False # only want to update once due to changed settings

            if clearExistingProgramList:
                c.execute("DELETE FROM updates WHERE source=?", [self.source.KEY]) # cascades and deletes associated programs records
            else:
                c.execute("DELETE FROM updates WHERE source=? AND date=?", [self.source.KEY, dateStr]) # cascades and deletes associated programs records

            # programs updated
            c.execute("INSERT INTO updates(source, date, programs_updated) VALUES(?, ?, ?)", [self.source.KEY, dateStr, datetime.datetime.now()])
            updatesId = c.lastrowid

            imported = imported_channels = imported_programs = 0
            for item in self.source.getDataFromExternal(date, progress_callback):
                imported += 1

                if imported % 10000 == 0:
                    self.conn.commit()

                if isinstance(item, Channel):
                    imported_channels += 1
                    channel = item
                    c.execute('INSERT OR IGNORE INTO channels(id, title, logo, stream_url, visible, weight, source) VALUES(?, ?, ?, ?, ?, (CASE ? WHEN -1 THEN (SELECT COALESCE(MAX(weight)+1, 0) FROM channels WHERE source=?) ELSE ? END), ?)', [channel.id, channel.title, channel.logo, channel.streamUrl, channel.visible, channel.weight, self.source.KEY, channel.weight, self.source.KEY])
                    if not c.rowcount:
                        c.execute('UPDATE channels SET title=?, logo=?, stream_url=?, visible=(CASE ? WHEN -1 THEN visible ELSE ? END), weight=(CASE ? WHEN -1 THEN weight ELSE ? END) WHERE id=? AND source=?',
                            [channel.title, channel.logo, channel.streamUrl, channel.weight, channel.visible, channel.weight, channel.weight, channel.id, self.source.KEY])

                elif isinstance(item, Program):
                    imported_programs += 1
                    program = item
                    if isinstance(program.channel, Channel):
                        channel = program.channel.id
                    else:
                        channel = program.channel

                    c.execute('INSERT INTO programs(channel, title, start_date, end_date, description, image_large, image_small, source, updates_id, series_id, movie_id, episode_id, season_number, episode_number, category, new, in_sickbeard, in_couchpotato) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        [channel, program.title, program.startDate, program.endDate, program.description, program.imageLarge, program.imageSmall, self.source.KEY, updatesId, program.seriesId, program.movieId, program.episodeId, program.seasonNumber, program.episodeNumber, program.category, program.new, program.sickbeardManaged, program.couchpotatoManaged])

            # channels updated
            c.execute("UPDATE sources SET channels_updated=? WHERE id=?", [datetime.datetime.now(), self.source.KEY])
            self.conn.commit()

            if imported_channels == 0 or imported_programs == 0:
                self.updateFailed = True

        except SourceUpdateCanceledException:
            # force source update on next load
            c.execute('UPDATE sources SET channels_updated=? WHERE id=?', [0, self.source.KEY])
            c.execute("DELETE FROM updates WHERE source=?", [self.source.KEY]) # cascades and deletes associated programs records
            self.conn.commit()

        except Exception:
            import traceback as tb
            import sys
            (type, value, traceback) = sys.exc_info()
            tb.print_exception(type, value, traceback)

            try:
                self.conn.rollback()
            except sqlite3.OperationalError:
                pass # no transaction is active

            try:
                # invalidate cached data
                c.execute('UPDATE sources SET channels_updated=? WHERE id=?', [0, self.source.KEY])
                self.conn.commit()
            except sqlite3.OperationalError:
                pass # database is locked

            self.updateFailed = True
        finally:
            self.updateInProgress = False
            c.close()

    def getEPGView(self, channelStart, date = datetime.datetime.now(), progress_callback = None, clearExistingProgramList = True):
        result = self._invokeAndBlockForResult(self._getEPGView, channelStart, date, progress_callback, clearExistingProgramList)

        if self.updateFailed:
            raise SourceException('No channels or programs imported')

        return result


    def _getEPGView(self, channelStart, date, progress_callback, clearExistingProgramList):
        self._updateChannelAndProgramListCaches(date, progress_callback, clearExistingProgramList)

        channels = self._getChannelList(onlyVisible = True)

        if channelStart < 0:
            channelStart = len(channels) - 1
        elif channelStart > len(channels) - 1:
            channelStart = 0
        channelEnd = channelStart + Database.CHANNELS_PER_PAGE
        channelsOnPage = channels[channelStart : channelEnd]

        programs = self._getProgramList(channelsOnPage, date)

        return [channelStart, channelsOnPage, programs]


    def getNextChannel(self, currentChannel):
        channels = self.getChannelList()
        idx = channels.index(currentChannel)
        idx += 1
        if idx > len(channels) - 1:
            idx = 0
        return channels[idx]

    def getPreviousChannel(self, currentChannel):
        channels = self.getChannelList()
        idx = channels.index(currentChannel)
        idx -= 1
        if idx < 0:
            idx = len(channels) - 1
        return channels[idx]

    def saveChannelList(self, callback, channelList):
        self.eventQueue.append([self._saveChannelList, callback, channelList])
        self.event.set()

    def _saveChannelList(self, channelList):
        c = self.conn.cursor()
        for idx, channel in enumerate(channelList):
            c.execute('INSERT OR IGNORE INTO channels(id, title, logo, stream_url, visible, weight, source) VALUES(?, ?, ?, ?, ?, (CASE ? WHEN -1 THEN (SELECT COALESCE(MAX(weight)+1, 0) FROM channels WHERE source=?) ELSE ? END), ?)', [channel.id, channel.title, channel.logo, channel.streamUrl, channel.visible, channel.weight, self.source.KEY, channel.weight, self.source.KEY])
            if not c.rowcount:
                c.execute('UPDATE channels SET title=?, logo=?, stream_url=?, visible=?, weight=(CASE ? WHEN -1 THEN weight ELSE ? END) WHERE id=? AND source=?', [channel.title, channel.logo, channel.streamUrl, channel.visible, channel.weight, channel.weight, channel.id, self.source.KEY])

        c.execute("UPDATE sources SET channels_updated=? WHERE id=?", [datetime.datetime.now(), self.source.KEY])
        self.channelList = None
        self.conn.commit()

    def getChannelList(self, onlyVisible = True):
        if not self.channelList or not onlyVisible:
            result = self._invokeAndBlockForResult(self._getChannelList, onlyVisible)

            if not onlyVisible:
                return result

            self.channelList = result
        return self.channelList


    def _getChannelList(self, onlyVisible):
        c = self.conn.cursor()
        channelList = list()
        if onlyVisible:
            c.execute('SELECT * FROM channels WHERE source=? AND visible=? ORDER BY weight', [self.source.KEY, True])
        else:
            c.execute('SELECT * FROM channels WHERE source=? ORDER BY weight', [self.source.KEY])
        for row in c:
            channel = Channel(row['id'], row['title'],row['logo'], row['stream_url'], row['visible'], row['weight'])
            channelList.append(channel)
        c.close()
        return channelList

    def getCurrentProgram(self, channel):
        return self._invokeAndBlockForResult(self._getCurrentProgram, channel)

    def _getCurrentProgram(self, channel):
        """

        @param channel:
        @type channel: source.Channel
        @return:
        """
        program = None
        now = datetime.datetime.now()
        c = self.conn.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND start_date <= ? AND end_date >= ?', [channel.id, self.source.KEY, now, now])
        row = c.fetchone()
        if row:
            program = Program(channel, row['title'], row['start_date'], row['end_date'], row['description'], row['image_large'], row['image_small'], row['series_id'], row['movie_id'], row['episode_id'], row['season_number'], row['episode_number'], row['category'], row['new'], row['in_sickbeard'], row['in_couchpotato'])
        c.close()

        return program

    def getNextProgram(self, channel):
        return self._invokeAndBlockForResult(self._getNextProgram, channel)

    def _getNextProgram(self, program):
        nextProgram = None
        c = self.conn.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND start_date >= ? ORDER BY start_date ASC LIMIT 1', [program.channel.id, self.source.KEY, program.endDate])
        row = c.fetchone()
        if row:
            nextProgram = Program(program.channel, row['title'], row['start_date'], row['end_date'], row['description'], row['image_large'], row['image_small'], row['series_id'], row['movie_id'], row['episode_id'], row['season_number'], row['episode_number'], row['category'], row['new'], row['in_sickbeard'], row['in_couchpotato'])
        c.close()

        return nextProgram

    def getPreviousProgram(self, channel):
        return self._invokeAndBlockForResult(self._getPreviousProgram, channel)

    def _getPreviousProgram(self, program):
        previousProgram = None
        c = self.conn.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND end_date <= ? ORDER BY start_date DESC LIMIT 1', [program.channel.id, self.source.KEY, program.startDate])
        row = c.fetchone()
        if row:
            previousProgram = Program(program.channel, row['title'], row['start_date'], row['end_date'], row['description'], row['image_large'], row['image_small'], row['series_id'], row['movie_id'], row['episode_id'], row['season_number'], row['episode_number'], row['category'], row['new'], row['in_sickbeard'], row['in_couchpotato'])
        c.close()

        return previousProgram

    def _getProgramList(self, channels, startTime):
        """

        @param channels:
        @type channels: list of source.Channel
        @param startTime:
        @type startTime: datetime.datetime
        @return:
        """
        endTime = startTime + datetime.timedelta(hours = 2)
        programList = list()

        channelMap = dict()
        for c in channels:
            channelMap[c.id] = c

        c = self.conn.cursor()
        c.execute('SELECT p.*, (SELECT 1 FROM notifications n WHERE n.channel=p.channel AND n.program_title=p.title AND n.source=p.source) AS notification_scheduled FROM programs p WHERE p.channel IN (\'' + ('\',\''.join(channelMap.keys())) + '\') AND p.source=? AND p.end_date > ? AND p.start_date < ?', [self.source.KEY, startTime, endTime])
        for row in c:
            program = Program(channelMap[row['channel']], row['title'], row['start_date'], row['end_date'], row['description'], row['image_large'], row['image_small'], row['series_id'], row['movie_id'], row['episode_id'], row['season_number'], row['episode_number'], row['category'], row['new'], row['in_sickbeard'], row['in_couchpotato'], row['notification_scheduled'])
            programList.append(program)


        return programList

    def _isProgramListCacheExpired(self, date = datetime.datetime.now()):
        # check if data is up-to-date in database
        dateStr = date.strftime('%Y-%m-%d')
        c = self.conn.cursor()
        c.execute('SELECT programs_updated FROM updates WHERE source=? AND date=?', [self.source.KEY, dateStr])
        row = c.fetchone()
        today = datetime.datetime.now()
        expired = row is None or row['programs_updated'].day != today.day
        c.close()
        return expired
        
    def setShowAsSickBeardManaged(self, seriesId):
        if seriesId is not None:
            self._invokeAndBlockForResult(self._setShowAsSickBeardManaged, seriesId)
        # no result, but block until operation is done

    def _setShowAsSickBeardManaged(self, seriesId):
        if seriesId is not None:
            c = self.conn.cursor()
            c.execute('UPDATE programs set in_sickbeard = 1 where series_id = ?',[seriesId])
            self.conn.commit()
            c.close()
        
    def unsetShowAsSickBeardManaged(self, seriesId):
        if seriesId is not None:
            self._invokeAndBlockForResult(self._unsetShowAsSickBeardManaged, seriesId)
        # no result, but block until operation is done

    def _unsetShowAsSickBeardManaged(self, seriesId):
        if seriesId is not None:
            c = self.conn.cursor()
            c.execute('UPDATE programs set in_sickbeard = 0 where series_id = ?',[seriesId])
            self.conn.commit()
            c.close()

    def setCustomStreamUrl(self, channel, stream_url):
        if stream_url is not None:
            self._invokeAndBlockForResult(self._setCustomStreamUrl, channel, stream_url)
        # no result, but block until operation is done

    def _setCustomStreamUrl(self, channel, stream_url):
        if stream_url is not None:
            c = self.conn.cursor()
            c.execute("DELETE FROM custom_stream_url WHERE channel=?", [channel.id])
            c.execute("INSERT INTO custom_stream_url(channel, stream_url) VALUES(?, ?)", [channel.id, stream_url.decode('utf-8', 'ignore')])
            self.conn.commit()
            c.close()

    def getCustomStreamUrl(self, channel):
        return self._invokeAndBlockForResult(self._getCustomStreamUrl, channel)

    def _getCustomStreamUrl(self, channel):
        c = self.conn.cursor()
        c.execute("SELECT stream_url FROM custom_stream_url WHERE channel=?", [channel.id])
        stream_url = c.fetchone()
        c.close()

        if stream_url:
            return stream_url[0]
        else:
            return None

    def deleteCustomStreamUrl(self, channel):
        self.eventQueue.append([self._deleteCustomStreamUrl, None, channel])
        self.event.set()

    def _deleteCustomStreamUrl(self, channel):
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_stream_url WHERE channel=?", [channel.id])
        self.conn.commit()
        c.close()

    def getStreamUrl(self, channel):
        customStreamUrl = self.getCustomStreamUrl(channel)
        if customStreamUrl:
            customStreamUrl = customStreamUrl.encode('utf-8', 'ignore')
            return customStreamUrl

        elif channel.isPlayable():
            streamUrl = channel.streamUrl.encode('utf-8', 'ignore')
            return streamUrl

        return None

    def adapt_datetime(self, ts):
        # http://docs.python.org/2/library/sqlite3.html#registering-an-adapter-callable
        return time.mktime(ts.timetuple())

    def convert_datetime(self, ts):
        try:
            return datetime.datetime.fromtimestamp(float(ts))
        except ValueError:
            return None

    def _createTables(self):
        c = self.conn.cursor()

        try:
            c.execute('SELECT major, minor, patch FROM version')
            (major, minor, patch) = c.fetchone()
            version = [major, minor, patch]
        except sqlite3.OperationalError:
            version = [0, 0, 0]

        try:
            if version < [1, 3, 0]:
                c.execute('CREATE TABLE IF NOT EXISTS custom_stream_url(channel TEXT, stream_url TEXT)')
                c.execute('CREATE TABLE version (major INTEGER, minor INTEGER, patch INTEGER)')
                c.execute('INSERT INTO version(major, minor, patch) VALUES(1, 3, 0)')

                # For caching data
                c.execute('CREATE TABLE sources(id TEXT PRIMARY KEY, channels_updated TIMESTAMP)')
                c.execute('CREATE TABLE updates(id INTEGER PRIMARY KEY, source TEXT, date TEXT, programs_updated TIMESTAMP)')
                c.execute('CREATE TABLE channels(id TEXT, title TEXT, logo TEXT, stream_url TEXT, source TEXT, visible BOOLEAN, weight INTEGER, PRIMARY KEY (id, source), FOREIGN KEY(source) REFERENCES sources(id) ON DELETE CASCADE)')
                
                #Rob Newton - 20130130 - Added series_id, movie_id, episode_id, season_number, episode_number, category, new, in_sickbeard, in_couchpotato
                c.execute('CREATE TABLE programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, image_large TEXT, image_small TEXT, source TEXT, updates_id INTEGER, series_id INTEGER, movie_id TEXT, episode_id INTEGER, season_number INTEGER, episode_number INTEGER, category TEXT, new INTEGER, in_sickbeard INTEGER, in_couchpotato INTEGER, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE, FOREIGN KEY(updates_id) REFERENCES updates(id) ON DELETE CASCADE)')
                
                c.execute('CREATE INDEX program_list_idx ON programs(source, channel, start_date, end_date)')
                c.execute('CREATE INDEX start_date_idx ON programs(start_date)')
                c.execute('CREATE INDEX end_date_idx ON programs(end_date)')

                # For active setting
                c.execute('CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)')

                # For notifications
                c.execute("CREATE TABLE notifications(channel TEXT, program_title TEXT, source TEXT, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE)")

            if version < [1, 3, 1]:
                # Recreate tables with FOREIGN KEYS as DEFERRABLE INITIALLY DEFERRED
                c.execute('UPDATE version SET major=1, minor=3, patch=1')
                c.execute('DROP TABLE channels')
                c.execute('DROP TABLE programs')
                c.execute('CREATE TABLE channels(id TEXT, title TEXT, logo TEXT, stream_url TEXT, source TEXT, visible BOOLEAN, weight INTEGER, PRIMARY KEY (id, source), FOREIGN KEY(source) REFERENCES sources(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED)')
                
                #Rob Newton - 20130130 - Added series_id, movie_id, episode_id, season_number, episode_number, category, new, in_sickbeard, in_couchpotato
                c.execute('CREATE TABLE programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, image_large TEXT, image_small TEXT, source TEXT, updates_id INTEGER, series_id INTEGER, movie_id TEXT, episode_id INTEGER, season_number INTEGER, episode_number INTEGER, category TEXT, new INTEGER, in_sickbeard INTEGER, in_couchpotato INTEGER, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(updates_id) REFERENCES updates(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED)')
                
                c.execute('CREATE INDEX program_list_idx ON programs(source, channel, start_date, end_date)')
                c.execute('CREATE INDEX start_date_idx ON programs(start_date)')
                c.execute('CREATE INDEX end_date_idx ON programs(end_date)')

            # make sure we have a record in sources for this Source
            c.execute("INSERT OR IGNORE INTO sources(id, channels_updated) VALUES(?, ?)", [self.source.KEY, 0])

            self.conn.commit()
            c.close()

        except sqlite3.OperationalError, ex:
            raise DatabaseSchemaException(ex)


    def addNotification(self, program):
        self._invokeAndBlockForResult(self._addNotification, program)
        # no result, but block until operation is done

    def _addNotification(self, program):
        """
        @type program: source.program
        """
        c = self.conn.cursor()
        c.execute("INSERT INTO notifications(channel, program_title, source) VALUES(?, ?, ?)", [program.channel.id, program.title, self.source.KEY])
        self.conn.commit()
        c.close()

    def removeNotification(self, program):
        self._invokeAndBlockForResult(self._removeNotification, program)
        # no result, but block until operation is done

    def _removeNotification(self, program):
        """
        @type program: source.program
        """
        c = self.conn.cursor()
        c.execute("DELETE FROM notifications WHERE channel=? AND program_title=? AND source=?", [program.channel.id, program.title, self.source.KEY])
        self.conn.commit()
        c.close()


    def getNotifications(self, daysLimit = 2):
        return self._invokeAndBlockForResult(self._getNotifications, daysLimit)

    def _getNotifications(self, daysLimit):
        start = datetime.datetime.now()
        end = start + datetime.timedelta(days = daysLimit)
        c = self.conn.cursor()
        c.execute("SELECT DISTINCT c.title, p.title, p.start_date FROM notifications n, channels c, programs p WHERE n.channel = c.id AND p.channel = c.id AND n.program_title = p.title AND n.source=? AND p.start_date >= ? AND p.end_date <= ?", [self.source.KEY, start, end])
        programs = c.fetchall()
        c.close()

        return programs

    def isNotificationRequiredForProgram(self, program):
        return self._invokeAndBlockForResult(self._isNotificationRequiredForProgram, program)

    def _isNotificationRequiredForProgram(self, program):
        """
        @type program: source.program
        """
        c = self.conn.cursor()
        c.execute("SELECT 1 FROM notifications WHERE channel=? AND program_title=? AND source=?", [program.channel.id, program.title, self.source.KEY])
        result = c.fetchone()
        c.close()

        return result

    def clearAllNotifications(self):
        self._invokeAndBlockForResult(self._clearAllNotifications)
        # no result, but block until operation is done

    def _clearAllNotifications(self):
        c = self.conn.cursor()
        c.execute('DELETE FROM notifications')
        self.conn.commit()
        c.close()
