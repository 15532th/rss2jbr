import time
import datetime
import logging
import sqlite3

import feedparser

import yt_info


class Record():


    def __init__(self, **attrs):
        # attrs.get() used for youtube-specific fields
        self.link = attrs.get('link')
        self.title = attrs['title']
        self.published = attrs['published']
        self.updated = attrs['updated']
        self.author = attrs['author']
        self.video_id = attrs.get('yt_videoid')
        self.summary = attrs['summary']
        self.unarchived = self.is_unarchived()
        try:
            self.views = int(attrs['media_statistics']['views'])
        except:
            self.views = None
        if self.views == 0:
            self.scheduled = self.get_scheduled()
        else:
            self.scheduled = None

    def get_scheduled(self):
        try:
            scheduled = yt_info.get_sched_isoformat(self.video_id)
        except:
            logging.exception('Exception while trying to get "scheduled" field, skipping')
            scheduled = None
        return scheduled

    def __eq__(self, other):
        return self.link == other.link

    def __str__(self):
        return str(self.__dict__)

    def is_unarchived(self):
        patterns = ['archive', 'アーカイブ']
        for pattern in patterns:
            if pattern in self.title:
                return True
        return False

    def format_date(self, datestring, timezone_offset=0):
        # remove semicolon from timezone part of string because %z don't have it
        datestring = ''.join([datestring[i] for i in range(len(datestring)) if i != 22])
        tz = datetime.timezone(datetime.timedelta(hours=timezone_offset))
        dt = datetime.datetime.strptime(datestring, '%Y-%m-%dT%H:%M:%S%z').astimezone(tz)
        return dt.strftime('%Y-%m-%d %H:%M')

    def format_record(self, timezone_offset=0):
        scheduled = self.scheduled
        if scheduled:
            scheduled_time = '\nscheduled to {}'.format(self.format_date(scheduled, timezone_offset))
        else:
            scheduled_time = ''
        template = '{}\n{}\npublished by {} at {}'
        return template.format(self.link, self.title, self.author, self.format_date(self.published, timezone_offset)) + scheduled_time

    def convert_to_row(self, additional_fields):
        row = {}
        row.update(self.__dict__)
        row.update(additional_fields)
        return row


class RSS2MSG():


    def __init__(self, feeds, db_path=':memory:'):
        '''entries parsed from `feed_links` in `feeds` will be put in table `records`'''
        self.feeds = feeds
        self.db = RecordDB(db_path)
        db_size = self.db.get_size()
        logging.info('{} records in DB'.format(db_size))
        if db_size == 0:
            self.get_new_records()

    def get_feed(self, link):
        try:
            feed = feedparser.parse(link)
            if feed.status == 200: 
                return feed
            else:
                raise Exception('got code {} while fetching {}'.format(feed.status, link))
        except Exception as e:
            logging.warning('Exception while updating rss feed: {}'.format(e))
            return None

    def parse_entries(self, feed):
        records = []
        for entry in feed['entries']:
            records.append(Record(**entry)) 
        return records

    def get_new_records(self):
        records_by_feed = {x:list() for x in self.feeds.keys()}
        for feedname, link in self.feeds.items():
            feed = self.get_feed(link)
            if feed is None:
                continue
            records = self.parse_entries(feed)
            for record in records:
                if not self.db.row_exists(record.video_id):
                    # only first record for given video_id is send to actions
                    records_by_feed[feedname].append(record)
                    template = '{} {:<8} [{}] {}'
                    logging.info(template.format(record.format_date(record.published), feedname, record.video_id, record.title))
                if not self.db.row_exists(record.video_id, record.updated):
                    # every new record for given video_id will be stored in db
                    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat(timespec='seconds')
                    additional_fields = {'feed_name': feedname, 'parsed_at': now}
                    row = record.convert_to_row(additional_fields)
                    self.db.insert_row(row)
                    
        return records_by_feed


class RecordDB():


    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        record_structure = 'parsed_at datetime, feed_name text, author text, video_id text, link text, title text, summary text, published datetime, updated datetime, scheduled datetime DEFAULT NULL, views intefer, PRIMARY KEY(video_id, updated)'
        self.cursor.execute('CREATE TABLE IF NOT EXISTS records ({})'.format(record_structure))
        self.db.commit()

    def insert_row(self, row):
        row_structure = ':parsed_at, :feed_name, :author, :video_id, :link, :title, :summary, :published, :updated, :scheduled, :views'
        sql = "INSERT INTO records VALUES({})".format(row_structure)
        self.cursor.execute(sql, row)
        self.db.commit()

    def row_exists(self, video_id, updated=None):
        if updated is not None:
            sql = "SELECT 1 FROM records WHERE video_id=:video_id AND updated=:updated LIMIT 1"
        else:
            sql = "SELECT 1 FROM records WHERE video_id=:video_id LIMIT 1"
        keys = {'video_id': video_id, 'updated': updated}
        self.cursor.execute(sql, keys)
        return bool(self.cursor.fetchone())

    def get_size(self):
        sql = 'SELECT COUNT(1) FROM records'
        self.cursor.execute(sql)
        return int(self.cursor.fetchone()[0])
