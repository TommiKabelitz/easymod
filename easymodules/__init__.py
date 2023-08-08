"""
`easymodules` provides a simple interface to the command line :code:`module` command for 
managing environment modules.

Through the `Module` class, all sub-commands (eg. :code:`module load`, :code:`module list`, etc.),
may be used and all environment variables associated with the module command
may be easily accessed.
"""
from .core import Module
