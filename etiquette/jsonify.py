'''
This file provides functions that convert the Etiquette objects into
dictionaries suitable for JSON serializing.
'''

def album(a, minimal=False):
    j = {
        'id': a.id,
        'description': a.description,
        'title': a.title,
        'author': user_or_none(a.get_author()),
    }
    if not minimal:
        j['photos'] = [photo(p) for p in a.get_photos()]
        parent = a.get_parent()
        if parent is not None:
            j['parent'] = album(parent, minimal=True)
        else:
            j['parent'] = None
        j['sub_albums'] = [child.id for child in a.get_children()]

    return j

def bookmark(b):
    j = {
        'id': b.id,
        'author': user_or_none(b.get_author()),
        'url': b.url,
        'title': b.title,
    }
    return j

def exception(e):
    j = {
        'error_type': e.error_type,
        'error_message': e.error_message,
    }
    return j

def photo(p, include_albums=True, include_tags=True):
    tags = p.get_tags()
    tags.sort(key=lambda x: x.name)
    j = {
        'id': p.id,
        'author': user_or_none(p.get_author()),
        'extension': p.extension,
        'width': p.width,
        'height': p.height,
        'ratio': p.ratio,
        'area': p.area,
        'bytes': p.bytes,
        'duration_str': p.duration_string,
        'duration': p.duration,
        'bytes_str': p.bytestring,
        'has_thumbnail': bool(p.thumbnail),
        'created': p.created,
        'filename': p.basename,
        'mimetype': p.mimetype,
        'searchhidden': bool(p.searchhidden),
    }
    if include_albums:
        j['albums'] = [album(a, minimal=True) for a in p.get_containing_albums()]

    if include_tags:
        j['tags'] = [tag(t) for t in tags]

    return j

def tag(t, include_synonyms=False):
    j = {
        'id': t.id,
        'author': user_or_none(t.get_author()),
        'name': t.name,
        'description': t.description,
        'qualified_name': t.qualified_name(),
    }
    if include_synonyms:
        j['synonyms'] = list(t.get_synonyms())
    return j

def user(u):
    j = {
        'id': u.id,
        'username': u.username,
        'created': u.created,
    }
    return j

def user_or_none(u):
    if u is None:
        return None
    return user(u)
