import dexy.plugin
import dexy.artifact
import os
import shutil

class Reporter(object):
    TITLE = None
    ALIASES = []
    __metaclass__ = dexy.plugin.PluginMeta

    @classmethod
    def is_active(klass):
        return True

    ALLREPORTS = True # whether to be included in 'allreports', set to false for reporters with side effects
    REPORTS_DIR = None
    SAFETY_FILENAME = ".dexy-generated"
    README_FILENAME = "README"

    @classmethod
    def create_reports_dir(self, reports_dir):
        self.remove_reports_dir(reports_dir)

        safety_filepath = os.path.join(reports_dir, self.SAFETY_FILENAME)
        readme_filepath = os.path.join(reports_dir, self.README_FILENAME)

        os.mkdir(reports_dir)

        with open(safety_filepath, "w") as f:
            f.write("""
            This directory was generated by the %s Dexy Reporter and
            may be deleted without notice.\n\n""" % self.__class__.__name__)
        with open(readme_filepath, "w") as f:
            f.write("""
            This directory was generated by the %s Dexy Reporter and
            may be deleted without notice.\n\n""" % self.__class__.__name__)

    @classmethod
    def remove_reports_dir(self, reports_dir=None):
        if not reports_dir:
            reports_dir = self.REPORTS_DIR

        safety_filepath = os.path.join(reports_dir, self.SAFETY_FILENAME)

        if os.path.exists(reports_dir) and not os.path.exists(safety_filepath):
            raise Exception("Please remove directory %s, Dexy wants to put a report here but doesn't want to overwrite anything by accident." % os.path.abspath(reports_dir))
        elif os.path.exists(reports_dir):
            shutil.rmtree(reports_dir)

    def run(self, runner):
        pass
