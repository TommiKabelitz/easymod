import os
import pathlib
import re

class Module:
    # Default sub-commands. This is the list of sub-commands in Modules/v4.3.0
    sub_commands = [
        "help",
        "add",
        "load",
        "rm",
        "unload",
        "swap",
        "switch",
        "show",
        "display",
        "list",
        "avail",
        "aliases",
        "use",
        "unuse",
        "refresh",
        "reload",
        "purge",
        "clear",
        "source",
        "whatis",
        "apropos",
        "keyword",
        "search",
        "test",
        "save",
        "restore",
        "saverm",
        "saveshow",
        "savelist",
        "initadd",
        "initprepend",
        "initrm",
        "initswitch",
        "initlist",
        "initclear",
        "path",
        "paths",
        "config",
    ]
    # Default environment variables.
    # This is the list of environment variables in Modules/v4.3.0
    envinronment_variables = [
        "LOADEDMODULES",
        "MODULECONTACT",
        "MODULEPATH",
        "MODULERCFILE",
        "MODULESHOME",
        "MODULES_AUTO_HANDLING",
        "MODULES_AVAIL_INDEPTH",
        "MODULES_CMD",
        "MODULES_COLLECTION_PIN_VERSION",
        "MODULES_COLLECTION_TARGET",
        "MODULES_COLOR",
        "CLICOLOR",
        "MODULES_COLORS",
        "MODULES_IMPLICIT_DEFAULT",
        "MODULES_LMALTNAME",
        "MODULES_LMCONFLICT",
        "MODULES_LMNOTUASKED",
        "MODULES_LMPREREQ",
        "MODULES_PAGER",
        "MODULES_RUN_QUARANTINE",
        "MODULES_SEARCH_MATCH",
        "MODULES_SET_SHELL_STARTUP",
        "MODULES_SILENT_SHELL_DEBUG",
        "MODULES_SITECONFIG",
        "MODULES_TERM_BACKGROUND",
        "MODULES_UNLOAD_MATCH_ORDER",
        "MODULES_USE_COMPAT_VERSION",
        "MODULES_VERBOSITY",
        "_LMFILES_",
    ]

    def __init__(self, home: os.PathLike = None, init_file: os.PathLike = None):
        """
        The Module object is a simple interface to the sub-commands and environment variables associated with the module command.

        Upon initialisation, module commands are accessed through the result the Module object as if they were class methods. For example

        >> module = Module()
        >> module.list()
        No Modulefiles Currently Loaded.
        >> module.load("openmpi/4.1.5")
        >> module.list()
        Currently Loaded Modulefiles:
         1) openmpi/4.1.5


        Module environment variables may be accessed through the following

        >> module = Module()
        >> module.environ["MODULE_CMD"]
        /opt/Modules/v4.3.0/libexec/modulecmd.tcl

        Parameters
        ----------
        home : os.PathLike, optional
            Path to the home directory for the module command, optional.
        init_file: os.PathLike, optional
            Path to the Modules initialisation file, required only if the initialisation file cannot be found automatically.
            
        Raises
        ------
        ValueError
            If home not passed, a ValueError is raised if the home directory for the module command cannot be found through the environment variable 'MODULESHOME'.
        """
        if home is not None:
            self.modules_home = pathlib.Path(home)
        else:
            try:
                self.modules_home = pathlib.Path(os.environ["MODULESHOME"])
            except KeyError:
                raise ValueError(
                    "Cannot automatically set modules_home. Environment variable MODULESHOME unset. Pass module home directory to Module"
                )

        # Attempts to find the init file based on modules_home
        self.set_init_file(init_file)
        
        # Initialise modules command, variables from init script are saved into global
        # scope here
        with open(self.init_file, "r") as f:
            exec(f.read(), globals())
        # Grabbing the resulting module function
        try:
            self.module = globals()["module"]
        except KeyError:
            raise EnvironmentError("The module environment could not be initialised.")


    def set_init_file(self, init_file: os.PathLike = None):
        """
        Set the path to the module initialisation file.

        If init_file is not passed, self.modules_home is searched for an init file.

        Parameters
        ----------
        init_file : os.PathLike, optional
            Path to the initialisation file, by default None

        Raises
        ------
        FileNotFoundError
            If the initialisation file cannot be found.
        ValueError
            If multiple possible initialisation files are found.
        """
        if init_file is not None:
            self.init_file = pathlib.Path(init_file)
            if not self.init_file.exists():
                raise FileNotFoundError(f"Module initialisation file not found\n{self.init_file}")
            return
        
        # Double asterisk glob allows the init directory to be buried within the directory tree
        possible_init_files = list(self.modules_home.glob("**/init/*python*.py"))
        
        if len(possible_init_files) == 0:
            raise FileNotFoundError("Modules initialisation file could not be found. ")
        elif len(possible_init_files) > 1:
            files = ", ".join(str(p) for p in possible_init_files)
            raise ValueError("Multiple possible Module initialisation files found\n%s" % files)
        
        self.init_file = possible_init_files[0]
        

    def parse_man_file(self, man_file: os.PathLike = None):
        """
        Parse the module manual file for available module sub-commands and environment variables.

        The manual file is generally located in the module home directory in a file called module.1

        Parameters
        ----------
        man_file : os.PathLike, optional
            Path to the manual file, by default None
        """
        self.get_sub_commands(man_file)
        self.get_environment_variables(man_file)

    def get_sub_commands(self, man_file: os.PathLike = None):
        """
        Get list of sub commands to the module command.

        See parse_man_file for information about man_file.

        Parameters
        ----------
        man_file : os.PathLike, optional
            Path to the manual file, by default None
        """

        # Standard manual file location
        if man_file is None:
            man_file = os.path.join(
                self.modules_home, "share", "man", "man1", "module.1"
            )

        with open(man_file, "r") as f:
            man = f.read()

        # Find section of manual re. sub-commands
        start = man.find(".SS Module Sub\-Commands")
        end = start + man[start + 3 :].find(".SS") + 1

        sub_commands_section = man[start:end]

        # Regex to extract the subcommands by utilising the formatting/syntax of
        # manual pages
        self.sub_commands = re.findall(r".sp\n\\fB([\w|-]+)\\fP", sub_commands_section)

    def get_environment_variables(self, man_file: os.PathLike = None):
        """
        Get list of environment variables set by the module command.

        See parse_man_file for information about man_file.

        Parameters
        ----------
        man_file : os.PathLike, optional
            Path to the manual file, by default None
        """
        # Standard manual file location
        if man_file is None:
            man_file = os.path.join(
                self.modules_home, "share", "man", "man1", "module.1"
            )

        with open(man_file, "r") as f:
            man = f.read()

        start = man.find(".SH ENVIRONMENT")
        end = start + man[start + 3 :].find("\n.S") + 1

        environment_vars_section = man[start:end]

        # Regex to extract the environment variables by utilising the formatting/syntax of
        # manual pages
        self.envinronment_variables = re.findall(
            r".sp\n\\fB([A-Z|-|_]+)\\fP", environment_vars_section
        )

    def __getattr__(self, _name):
        """
        Use __getattr__ to allow calling of the module functions as
        if they were methods. See documentation of Module for example use.
        """
        # __getattr__ is only called if _name is not already an attribute of
        # the class.
        # First check if the attribute is in the list of sub-commands.
        if _name in self.sub_commands:
            # Have to return a wrapper function so that args and kwargs
            # can be passed through
            def wrapper(*args, **kwargs):
                return self.module(_name, *args, **kwargs)

            return wrapper
        else:
            raise AttributeError("Module has no such attribute %s" % _name)

    @property
    def environ(self):
        """
        Dictionary of environment variables associated with the module command.

        Dictionary updated each time environ is accessed. If environment variables are missing
        from the dict, they are either unset or missing from self.environment_variables. The
        latter can be updated using self.get_environment_variables.
        """
        return {
            var: os.environ[var]
            for var in self.envinronment_variables
            if os.environ.get(var) is not None
        }
