"""
The Variables module allows setting of variables before processing.

"""

import jenkins_jobs.modules.base
import string
import logging
from jenkins_jobs.errors import JenkinsJobsException
from collections import defaultdict


logger = logging.getLogger(__name__)

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'

class Variables(jenkins_jobs.modules.base.Base):

    changed = False
    def deep_replace(self, obj, vardict):
        if isinstance(obj, str):
            logger.debug("deep_replace")
            logger.debug(obj)
            try:

                ret = string.Formatter().vformat(str(obj), (), vardict)
                self.changed &= ret == obj
            except KeyError as exc:
                missing_key = exc.message
                desc = "%s parameter missing to format %s\nGiven: %s" % (
                       missing_key, obj, vardict)
                raise JenkinsJobsException(desc)
        elif isinstance(obj, list):
            ret = []
            for item in obj:
                ret.append(self.deep_replace(item, vardict))
        elif isinstance(obj, dict):
            ret = {}
            for item in obj:
                key = string.Formatter().vformat(str(item), (), vardict)
                ret[key] = self.deep_replace(obj[item], vardict)
                self.changed &= key == item and ret[key] == obj[item]
        else:
            ret = obj
        return ret

    def handle_data(self, parser):
        self.changed = False
        config_vars = {}
        if parser.config and parser.config.has_section('vars'):
            logger.debug("Found config with variables:")
            logger.debug(parser.config.items('vars'))
            add_vars = parser.config.items('vars')
            for var in add_vars:
                config_vars[var[0]] = var[1]

        if config_vars:
            parser.data = self.deep_replace(parser.data, SafeDict(**config_vars))
        return self.changed
