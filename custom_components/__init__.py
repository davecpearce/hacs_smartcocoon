"""Custom components package.

Makes custom_components a regular package rather than a namespace package.
An editable install (make install / CI) otherwise adds a placeholder entry to
its __path__, which Home Assistant's loader tries to list as a directory and
crashes on -- so any test that loads the integration through Home Assistant
(config flows, entry setup) failed. Only custom_components/smartcocoon is
installed for users; this file never ships.
"""
