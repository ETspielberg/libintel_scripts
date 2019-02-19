from pbr.version import VersionInfo

_v = VersionInfo('scopus').semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()

from query.scopus.utils import *

from query.scopus.abstract_citations import *
from query.scopus.scopus_affiliation import *
from query.scopus.scopus_affiliation import *
from query.scopus.scopus_author import *
from query.scopus.scopus_reports import *
from query.scopus.scopus_search import *
from query.scopus.search_affiliation import *
from query.scopus.search_author import *
