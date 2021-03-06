'''
This file provides data and objects that do not change throughout the runtime.
'''

import converter
import logging
import shutil
import string
import traceback
import warnings

FFMPEG_NOT_FOUND = '''
ffmpeg or ffprobe not found.
Add them to your PATH or use symlinks such that they appear in:
Linux: which ffmpeg & which ffprobe
Windows: where ffmpeg & where ffprobe
'''

def _load_ffmpeg():
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')

    if (not ffmpeg_path) or (not ffprobe_path):
        warnings.warn(FFMPEG_NOT_FOUND)
        return None

    try:
        ffmpeg = converter.Converter(
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    except converter.ffmpeg.FFMpegError:
        traceback.print_exc()
        ffmpeg = None

    return ffmpeg

ffmpeg = _load_ffmpeg()

FILENAME_BADCHARS = '\\/:*?<>|"'

# Note: Setting user_version pragma in init sequence is safe because it only
# happens after the out-of-date check occurs, so no chance of accidentally
# overwriting it.
DATABASE_VERSION = 11
DB_INIT = '''
PRAGMA cache_size = 10000;
PRAGMA count_changes = OFF;
PRAGMA foreign_keys = ON;
PRAGMA user_version = {user_version};

----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users(
    id TEXT PRIMARY KEY NOT NULL,
    username TEXT NOT NULL COLLATE NOCASE,
    password BLOB NOT NULL,
    created INT
);
CREATE INDEX IF NOT EXISTS index_users_id on users(id);
CREATE INDEX IF NOT EXISTS index_users_username on users(username COLLATE NOCASE);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS albums(
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT,
    description TEXT,
    author_id TEXT,
    FOREIGN KEY(author_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS index_albums_id on albums(id);
CREATE INDEX IF NOT EXISTS index_albums_author_id on albums(author_id);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookmarks(
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT,
    url TEXT,
    author_id TEXT,
    FOREIGN KEY(author_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS index_bookmarks_id on bookmarks(id);
CREATE INDEX IF NOT EXISTS index_bookmarks_author_id on bookmarks(author_id);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS photos(
    id TEXT PRIMARY KEY NOT NULL,
    filepath TEXT COLLATE NOCASE,
    override_filename TEXT COLLATE NOCASE,
    extension TEXT,
    width INT,
    height INT,
    ratio REAL,
    area INT,
    duration INT,
    bytes INT,
    created INT,
    thumbnail TEXT,
    tagged_at INT,
    author_id TEXT,
    searchhidden INT,
    FOREIGN KEY(author_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS index_photos_id on photos(id);
CREATE INDEX IF NOT EXISTS index_photos_filepath on photos(filepath COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS index_photos_override_filename on
    photos(override_filename COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS index_photos_created on photos(created);
CREATE INDEX IF NOT EXISTS index_photos_extension on photos(extension);
CREATE INDEX IF NOT EXISTS index_photos_author_id on photos(author_id);
CREATE INDEX IF NOT EXISTS index_photos_searchhidden on photos(searchhidden);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags(
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    author_id TEXT,
    FOREIGN KEY(author_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS index_tags_id on tags(id);
CREATE INDEX IF NOT EXISTS index_tags_name on tags(name);
CREATE INDEX IF NOT EXISTS index_tags_author_id on tags(author_id);
----------------------------------------------------------------------------------------------------


----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS album_associated_directories(
    albumid TEXT NOT NULL,
    directory TEXT NOT NULL COLLATE NOCASE,
    FOREIGN KEY(albumid) REFERENCES albums(id)
);
CREATE INDEX IF NOT EXISTS index_album_associated_directories_albumid on
    album_associated_directories(albumid);
CREATE INDEX IF NOT EXISTS index_album_associated_directories_directory on
    album_associated_directories(directory);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS album_group_rel(
    parentid TEXT NOT NULL,
    memberid TEXT NOT NULL,
    FOREIGN KEY(parentid) REFERENCES albums(id),
    FOREIGN KEY(memberid) REFERENCES albums(id)
);
CREATE INDEX IF NOT EXISTS index_album_group_rel_parentid on album_group_rel(parentid);
CREATE INDEX IF NOT EXISTS index_album_group_rel_memberid on album_group_rel(memberid);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS album_photo_rel(
    albumid TEXT NOT NULL,
    photoid TEXT NOT NULL,
    FOREIGN KEY(albumid) REFERENCES albums(id),
    FOREIGN KEY(photoid) REFERENCES photos(id)
);
CREATE INDEX IF NOT EXISTS index_album_photo_rel_albumid on album_photo_rel(albumid);
CREATE INDEX IF NOT EXISTS index_album_photo_rel_photoid on album_photo_rel(photoid);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS id_numbers(
    tab TEXT NOT NULL,
    last_id TEXT NOT NULL
);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS photo_tag_rel(
    photoid TEXT NOT NULL,
    tagid TEXT NOT NULL,
    FOREIGN KEY(photoid) REFERENCES photos(id),
    FOREIGN KEY(tagid) REFERENCES tags(id)
);
CREATE INDEX IF NOT EXISTS index_photo_tag_rel_photoid on photo_tag_rel(photoid);
CREATE INDEX IF NOT EXISTS index_photo_tag_rel_tagid on photo_tag_rel(tagid);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tag_group_rel(
    parentid TEXT NOT NULL,
    memberid TEXT NOT NULL,
    FOREIGN KEY(parentid) REFERENCES tags(id),
    FOREIGN KEY(memberid) REFERENCES tags(id)
);
CREATE INDEX IF NOT EXISTS index_tag_group_rel_parentid on tag_group_rel(parentid);
CREATE INDEX IF NOT EXISTS index_tag_group_rel_memberid on tag_group_rel(memberid);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tag_synonyms(
    name TEXT NOT NULL,
    mastername TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS index_tag_synonyms_name on tag_synonyms(name);
----------------------------------------------------------------------------------------------------
'''.format(user_version=DATABASE_VERSION)

def _extract_columns(create_table_statement):
    column_names = create_table_statement.split('(')[1].rsplit(')', 1)[0]
    column_names = column_names.split(',')
    column_names = [x.strip() for x in column_names]
    column_names = [x.split(' ')[0] for x in column_names]
    column_names = [c for c in column_names if c.lower() != 'foreign']
    return column_names

SQL_COLUMNS = {}
for statement in DB_INIT.split(';'):
    if 'create table' not in statement.lower():
        continue

    table_name = statement.split('(')[0].strip().split(' ')[-1]
    SQL_COLUMNS[table_name] = _extract_columns(statement)

def _sql_dictify(columns):
    '''
    A dictionary where the key is the item and the value is the index.
    Used to convert a stringy name into the correct number to then index into
    an sql row.
    ['test', 'toast'] -> {'test': 0, 'toast': 1}
    '''
    return {column: index for (index, column) in enumerate(columns)}

SQL_INDEX = {table: _sql_dictify(columns) for (table, columns) in SQL_COLUMNS.items()}


ALLOWED_ORDERBY_COLUMNS = [
    'extension',
    'width',
    'height',
    'ratio',
    'area',
    'duration',
    'bytes',
    'created',
    'tagged_at',
    'random',
]


# Errors and warnings
WARNING_MINMAX_INVALID = 'Field "{field}": "{value}" is not a valid request. Ignored.'
WARNING_ORDERBY_INVALID = 'Invalid orderby request "{request}". Ignored.'
WARNING_ORDERBY_BADCOL = '"{column}" is not a sorting option. Ignored.'
WARNING_ORDERBY_BADDIRECTION = '''
You can\'t order "{column}" by "{direction}". Defaulting to descending.
'''

# Operational info
TRUTHYSTRING_TRUE = {s.lower() for s in ('1', 'true', 't', 'yes', 'y', 'on')}
TRUTHYSTRING_NONE = {s.lower() for s in ('null', 'none')}

ADDITIONAL_MIMETYPES = {
    '7z': 'archive',
    'gz': 'archive',
    'rar': 'archive',

    'aac': 'audio/aac',
    'ac3': 'audio/ac3',
    'dts': 'audio/dts',
    'm4a': 'audio/mp4',
    'opus': 'audio/ogg',

    'mkv': 'video/x-matroska',

    'ass': 'text/plain',
    'md': 'text/plain',
    'nfo': 'text/plain',
    'rst': 'text/plain',
    'srt': 'text/plain',
}

DEFAULT_DATADIR = '.\\_etiquette'
DEFAULT_DBNAME = 'phototagger.db'
DEFAULT_CONFIGNAME = 'config.json'
DEFAULT_THUMBDIR = 'site_thumbnails'

DEFAULT_CONFIGURATION = {
    'log_level': logging.DEBUG,

    'cache_size': {
        'album': 1000,
        'bookmark': 100,
        'photo': 100000,
        'tag': 1000,
        'user': 200,
    },

    'enable_feature': {
        'album': {
            'edit': True,
            'new': True,
        },
        'bookmark': {
            'edit': True,
            'new': True,
        },
        'photo': {
            'add_remove_tag': True,
            'new': True,
            'edit': True,
            'generate_thumbnail': True,
            'reload_metadata': True,
        },
        'tag': {
            'edit': True,
            'new': True,
        },
        'user': {
            'login': True,
            'new': True,
        },
    },

    'tag': {
        'min_length': 1,
        'max_length': 32,
        'valid_chars': string.ascii_lowercase + string.digits + '_()',
    },

    'user': {
        'min_length': 2,
        'min_password_length': 6,
        'max_length': 24,
        'valid_chars': string.ascii_letters + string.digits + '~!@#$%^*()[]{}:;,.<>/\\-_+=',
    },

    'digest_exclude_files': [
        'phototagger.db',
        'desktop.ini',
        'thumbs.db',
    ],
    'digest_exclude_dirs': [
        '_etiquette',
        '_site_thumbnails',
        'site_thumbnails',
    ],

    'file_read_chunk': 2 ** 20,
    'id_length': 12,
    'thumbnail_width': 400,
    'thumbnail_height': 400,

    'motd_strings': [
        'Good morning, Paul. What will your first sequence of the day be?',
    ],
}
