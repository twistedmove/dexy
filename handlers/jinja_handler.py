from dexy.handler import DexyHandler

from jinja2 import Environment
import json
import os
import pexpect
import re
import uuid

class FilenameHandler(DexyHandler):
    """Generate random filenames from keys to track provenance of data."""
    ALIASES = ['fn']
    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        for k, a in self.artifact.input_artifacts_dict.items():
            for ak, av in a['additional_inputs'].items():
                self.artifact.additional_inputs[ak] = av

        for m in re.finditer("dexy--(.+)\.([a-z]+)", input_text):
            key = m.groups()[0]
            ext = m.groups()[1]
            if key in self.artifact.additional_inputs.keys():
                filename = self.artifact.additional_inputs[key]
                self.log.debug("existing key %s in artifact %s links to file %s" %
                          (key, self.artifact.key, filename))
            else:
                filename = "%s.%s" % (uuid.uuid4(), ext)
                self.artifact.additional_inputs[key] = filename
                self.log.debug("added key %s to artifact %s ; links to file %s" %
                          (key, self.artifact.key, filename))

            input_text = input_text.replace(m.group(), filename)
        return input_text


class JinjaHelper:
    def ri(self, query):
        # --system flag needed or else ri complains about multiple versions
        command = "ri --system -T -f simple %s" % query
        return pexpect.run(command)

    def read_file(self, filename):
        f = open(filename, "r")
        return f.read()

class JinjaHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['jinja']

    def process_text(self, input_text):
        document_data = {}
        document_data['filenames'] = {}
        document_data['sections'] = {}
        document_data['a'] = {}

        # TODO move to separate 'index' handler for websites
        # create a list of subdirectories of this directory
        doc_dir = os.path.dirname(self.artifact.doc.name)
        children = [f for f in os.listdir(doc_dir) \
                    if os.path.isdir(os.path.join(doc_dir, f))]
        document_data['children'] = sorted(children)
    
        self.artifact.load_input_artifacts()
        for k, a in self.artifact.input_artifacts_dict.items():
            common_prefix = os.path.commonprefix([self.artifact.doc.name, k])
            common_path = os.path.dirname(common_prefix)
            relpath = os.path.relpath(k, common_path)
            
            if document_data['filenames'].has_key(relpath):
                raise Exception("Duplicate key %s" % relpath)
            
            document_data['filenames'][relpath] = a['fn']
            document_data['sections'][relpath] = a['data_dict']
            document_data[relpath] = a['data']
            for ak, av in a['additional_inputs'].items():
                document_data['a'][ak] = av
                fullpath_av = os.path.join('artifacts', av)
                if av.endswith('.json') and os.path.exists(fullpath_av):
                    print "loading JSON for %s" % fullpath_av
                    document_data[ak] = json.load(open(fullpath_av, "r"))
        
        if self.artifact.ext == ".tex":
            print "changing jinja tags for", self.artifact.key
            env = Environment(
                block_start_string = '<%',
                block_end_string = '%>',
                variable_start_string = '<<',
                variable_end_string = '>>',
                comment_start_string = '<#',
                comment_end_string = '#>'
                )
        else:
            env = Environment()
        template = env.from_string(input_text)
        
        # TODO test that we are in textile or other format where this makes sense
        if re.search("latex", self.artifact.doc.key()):
            is_latex = True
        else:
            is_latex = False

        document_data['filename'] = document_data['filenames']
        template_hash = {
            'd' : document_data, 
            'filenames' : document_data['filenames'],
            'dk' : sorted(document_data.keys()),
            'a' : self.artifact,
            'h' : JinjaHelper(),
            'is_latex' : is_latex
        }

        try:
            result = str(template.render(template_hash))
        except Exception as e:
            print "error occurred while processing", self.artifact.key
            raise e
        
        return result
