.. _release:

Release notes
=============

* Decode order added to the hit data structures.
* Unique ID added to the readout classes, and FileHeader machinery changed accordingly.
* Full I/O implemented in binary files, modeled on the native Python open() builtin.
* Processing of binary .apx files to files containing hits in a few different
  formats implemented (leveraging astropy tables).
* Binary playback facility added, with pretty printing of the readouts.
* Support for legacy .log files added, including conversion from .log to .apx.
* New command-line interface added.
* Docs added.
* Unit tests added.
* .gitignore and Makefile updated.

Merging pull requests
  * https://github.com/AstroPix/astropix-analysis/pull/10

Issue(s) closed
  * https://github.com/AstroPix/astropix-analysis/pull/16
  * https://github.com/AstroPix/astropix-analysis/pull/13
  * https://github.com/AstroPix/astropix-analysis/pull/12
  * https://github.com/AstroPix/astropix-analysis/pull/11
  * https://github.com/AstroPix/astropix-analysis/pull/7
  * https://github.com/AstroPix/astropix-analysis/pull/6
  * https://github.com/AstroPix/astropix-analysis/pull/5
  * https://github.com/AstroPix/astropix-analysis/pull/2


`2063157 <https://github.com/AstroPix/astropix-analysis/tree/2063157>`_
-----------------------------------------------------------------------

* Initial import of the binary I/O machinery, with classes and data structures
  to save astropix readouts to (and read them back from ) persistent storage.
* Initial setup of the unit tests and continuos integration on github.
* Initial setup of the documentation.
* Top-level Makefile added to facilitate some operations.
* pyproject.toml file added.

Merging pull requests
  * https://github.com/AstroPix/astropix-analysis/pull/3

Issue(s) closed
