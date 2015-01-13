import os
import yaml
import imp
import re

"""
A few things to watch out for... Currently, the *.sublime-snippet files must be placed in
a direct child folder of Packages, not just a descendant (grandchild).
$SUBLIME_HOME/Packages/User
Placeing them in a sub-folder will not work.
Symlinking from Packages will work.
Packages> ln -s Ansible User/Ansible

The scope of the file is set to source.yaml in the <scope> section of the snippet.
If you have troubles, remove this line to see if that fixes it.
Open a file you want to have ansible tab completions (.yml file)
Press Ctr+Shift+Alt+p to see what source type sublime thinks the file is.

"""
ansible_version = 1.8
sublime2_mac_user_dir = "Library/Application Support/Sublime Text 2/Packages/User"

sublime3_linux_user_dir = ".config/sublime-text-3/Packages/User"
sublime2_linux_user_dir = ".Sublime Text 2/Packages"

from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    sublime_packages_user_dir = sublime3_linux_user_dir
elif _platform == "darwin":
    sublime_packages_user_dir = sublime2_mac_user_dir
elif _platform == "win32":
    raise NotImplementedError("Windows not yet supported.  Taking pull requests")


def build_module_docs(ansible_home=None):
    '''
    Build documentation yaml tree by reading ansible source tree folder

    @ansible_home: path to ansible installation. 
                   If not specified, $ANSIBLE_HOME must be set.
    @returns: yaml tree
    Examples: For accessing tree values
    library = build_module_docs()
    library['files']['assemble']['options']['src']['description']
    returns the description of the assemble module in the files group of modules.
    library['<module_group>']['module']['module_field']  # some module_fields are simple
    '''

    if not ansible_home:
        ansible_home = os.path.expandvars("$ANSIBLE_HOME")
        print(ansible_home)
        if not ansible_home or ansible_home == "$ANSIBLE_HOME":
            raise ValueError('''ANSIBLE_HOME not set.  
                                Add it to ~/.bash_profile or /etc/profile.d/ansible 
                                or pass in the path to the ansible installation''') 
    library_dirs = []
    if ansible_version < 1.6:
        library_dirs=[os.path.join(ansible_home,"library")]
    else:
        library_dirs=list(map(lambda x: os.path.join(ansible_home, 'modules', x),['core', 'extras']))
    print (list(library_dirs))
    library = {}
    module_groups = {}
    module_fields = {}
    print("library_dirs",library_dirs)
    for library_dir in library_dirs:
        print (library_dir)
        for dirpath, dirnames, filenames in os.walk(library_dir, topdown=False):
            # if we are in library/<module_group>/ directory
            if os.path.basename(os.path.dirname(dirpath)) in ['core', 'extras', 'library']:
                module_group_name = os.path.basename(dirpath)
                library[module_group_name] = {}
                modules = [ x for x in filenames if not x.endswith(".pyc") and not x.startswith("__init__")]
                for module in modules:
                    fq_module_filename = os.path.join(dirpath, module)
                    with open(fq_module_filename, "r") as f:
                        source = f.read()
                        # \s matches white space
                        # * matches 0 or more of the previous item
                        # ( A | B ) matches A or B  - for the 2 kinds of triple quotes in python
                        # (.*?) makes the middle match non-greedy 
                        # so we match the next, not the last, ''' in the file
                        # DOTALL and MULTILINE flags allow . to match spanning multiple lines
                        DOCUMENTATION=re.search("DOCUMENTATION\s*=\s*('''|\"\"\")(.*?)('''|\"\"\")", 
                                                source, re.DOTALL | re.MULTILINE)
                        # each () pair is a group starting at 1.  Get the middle.
                        # print DOCUMENTATION.group(2)
                        # return # DOCUMENTATION is big, just print one example and bail
                        if not DOCUMENTATION:
                            print("WARNING: No documentation for module {}".format(module) )
                        else:
                            module_dict = yaml.load(DOCUMENTATION.group(2))
                            #print module_dict
                            #return
                            # load the yaml portion of interest (DESCRIPTION = ...)
                            library[module_group_name][module] = module_dict
    return library
            
def lookup_module_group(library, module):
    for module_group in library.keys():
        for _module in library[module_group]:
            if _module == module:
                return module_group
            

def emit_module_options(library, module, policy="default"):
    '''
    emit module options as required by emit_snippet

    @policy: from the future.  use this to set rules for what options get shown
    For now, edit snippets by hand to customize to frequent use patterns.
    '''

    opt_list = ""
    for i, option in enumerate(library[lookup_module_group(library,module)][module]["options"].items()):
        opt_list += emit_option(module, option, i, policy)
    return opt_list

def emit_option(module, option, num, policy="default"):
    option_name = option[0]
    option_dict = option[1]
    default_value = option_dict.get('default', 'nodefault')

    required = option_dict.get('required', False)
    description = option_dict.get('description', module)
        
    if policy=="default":
        emit = option_name + "=" + "${" + str(num+2) + ":" + str(default_value) + "}\n" + make_spaces(len(module)+5)

    return emit

#     opt_list = ""
#     for i, option in enumerate(library[lookup_module_group(library,module)][module]["options"].items()):
#         opt_list += emit_option(module, option, i, policy)
#     return opt_list

def make_spaces(num):
    spaces = ""
    for i in range(num):
        spaces += " "
    return spaces

def emit_snippet(library, module):
    snippet = '''<snippet>
    <content><![CDATA[ - name: ${1:.}\n''' + \
    make_spaces(3) + module.replace(".py","") + ": " + emit_module_options(library, module) + \
    ''']]></content>
    <tabTrigger>{trigger}</tabTrigger>
    <scope>source.yml</scope>
    <description>{description}</description>
</snippet>\n'''.format(description=library[lookup_module_group(library,module)][module]['short_description'],
                       trigger=module[0:3])
    return snippet

def generate_snippits(library, sublime_user_dir=None, sublime_language="Ansible"):
    '''
    Generates snippets files in path for each ansible module

    @library: ansible module datastructure generated by build_module_docs
    @sublime_path: path to sublime Packages/User/<Language>
                   defaults to mac path for sublime ending in Packages/User/YAML
    @sublime_language: language directory in Packages/User which will associate with the snippets
                       Defaults to "Ansible".  May also be good to run with "YAML" if you only use 
                       sublime-text for ansible work.

    '''
    if sublime_user_dir:
        if not os.path.exists(sublime_user_dir):
            raise ValueError("requested path {} does not exist".format(sublime_user_dir))
    else:
        sublime_user_dir = os.path.expandvars("$SUBLIME_USER_DIR")
        # if "$SUBLIME_USER_DIR" is not defined expandvars returns the string requested
        if  sublime_user_dir == "$SUBLIME_USER_DIR":
            #TODO The first non-mac user should refactor this to detect os and locate default
            # directory automatically.        
            home = os.path.expandvars("$HOME")
            sublime_user_dir = os.path.join(home, ".config/sublime-text-3/Packages/User")
            if not os.path.exists(sublime_user_dir):
                raise ValueError("{} does not exist.  Are you on a mac with Sublime Text 2 installed in default location?".format(sublime_user_dir))
    ansible_snippets_dir = os.path.join(sublime_user_dir, sublime_language)
    if not os.path.exists(ansible_snippets_dir):
        os.mkdir(ansible_snippets_dir)
    for module_group in library.keys():
        for module in library[module_group]:
            print ("library", library)
            print ("module", module)
            snippet = emit_snippet(library, module)
            snip_file = os.path.join(ansible_snippets_dir, "ansible-" + module.replace(".py", "") + ".sublime-snippet")
            with open(snip_file, 'w') as f:
                f.write(snippet)
    
def test_build_module_docs(ansible_home=None):
    library = build_module_docs(ansible_home)
    print("Ansible Modules " + str(library.keys()))
    print("library['files']['assemble']['options']['src']['description'] " + str(library['files']['assemble']['options']['src']['description']))
    
def main(ansible_home=None):
#TODO add argparse to allow values to be passed in from commandline
# For now, requires ANSIBLE_HOME and SUBLIME_USER_HOME to be set as environment vars
    library = build_module_docs(ansible_home)
    generate_snippits(library)
    
if __name__ == "__main__":
    main(ansible_home="/usr/local/lib/python2.7/dist-packages/ansible")