from dexy.filters.process import SubprocessFilter
from dexy.utils import file_exists
import codecs
import dexy.exceptions
import dexy.utils
import os
import subprocess

class LatexFilter(SubprocessFilter):
    """
    Generates a PDF file from LaTeX source.
    """
    aliases = ['latex', 'pdflatex']
    _settings = {
            'executable' : 'pdflatex',
            'input-extensions' : ['.tex', '.txt'],
            'output-extensions' : ['.pdf'],
            'command-string' : "%(prog)s -interaction=batchmode %(args)s %(script_file)s"
            }

    def process(self):
        self.populate_workspace()

        wd = self.parent_work_dir()
        env = self.setup_env()

        latex_command = self.command_string()

        bibtex_command = "bibtex %s" % os.path.splitext(self.output_data.basename())[0]

        def run_cmd(command):
            self.log_info("running %s in %s" % (command, os.path.abspath(wd)))
            proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=env)

            stdout, stderr = proc.communicate()
            self.log_debug(stdout)

        if bibtex_command:
            run_cmd(latex_command) #generate aux
            run_cmd(bibtex_command) #generate bbl

        # TODO specify in options how many times to run latex
        # TODO specify in options whether to run bibtex
        run_cmd(latex_command) # first run
        run_cmd(latex_command) # second run - fix references
        run_cmd(latex_command) # third run - just to be sure

        if not file_exists(os.path.join(wd, self.output_data.basename())):
            msg = "Latex file not generated. Look for information in latex log in %s directory."
            msgargs = os.path.abspath(wd)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

        if self.setting('add-new-files'):
            self.log_debug("adding new files found in %s for %s" % (wd, self.key))
            self.add_new_files()

        self.copy_canonical_file()

class TikzPgfFilter(LatexFilter):
    """
    Takes a snippet of Tikz code, wraps it in a LaTeX document, and renders it to PDF.
    """
    aliases = ['tikz']

    def process(self):
        latex_filename = self.output_data.basename().replace(self.ext, ".tex")

        # TODO allow setting tikz libraries per-document, or just include all of them?
        # TODO how to create a page size that just includes the content
        latex_header = """\documentclass[tikz]{standalone}
\usetikzlibrary{shapes.multipart}
\\begin{document}
        """
        latex_footer = "\n\end{document}"

        self.populate_workspace()
        wd = self.parent_work_dir()

        work_path = os.path.join(wd, latex_filename)
        self.log_debug("writing latex header + tikz content to %s" % work_path)
        with codecs.open(work_path, "w", encoding="utf-8") as f:
            f.write(latex_header)
            f.write(unicode(self.input_data))
            f.write(latex_footer)

        latex_command = "%s -interaction=batchmode %s" % (self.setting('executable'), latex_filename)

        def run_cmd(command):
            self.log_info("about to run %s in %s" % (command, os.path.abspath(wd)))
            proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=self.setup_env())

            stdout, stderr = proc.communicate()

            if proc.returncode > 2: # Set at 2 for now as this is highest I've hit, better to detect whether PDF has been generated?
                raise dexy.exceptions.UserFeedback("latex error, look for information in %s" %
                                latex_filename.replace(".tex", ".log"))
            elif proc.returncode > 0:
                self.log_warn("""A non-critical latex error has occurred running %s,
                status code returned was %s, look for information in %s""" % (
                self.key, proc.returncode,
                latex_filename.replace(".tex", ".log")))

        run_cmd(latex_command)

        self.copy_canonical_file()
