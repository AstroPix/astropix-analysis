.. _install:

Installation
============

We do not provide anything fancy in terms of installation, at this time, but the
only thing that you have to do to start using the stuff, once you have checked
out the repository from github, is to include the path to the top level folder
where the package lives into the ``$PYTHOPATH`` environmental variable.

Note we provide setup scripts to automate this.


Unix-like
~~~~~~~~~

For GNU/Linux and Mac you should be able to get up and running by just doing

.. code-block:: shell

   source path/to/astropix-analysis/setup.sh


Windows
~~~~~~~

If you are using the good-old fashioned command prompt, do

.. code-block:: shell

   path\to\astropix-analysis\setup.bat

We provide an experimental script for power shell. Of course things get complicated,
here, but there is anecdotal evidence that you might get away with something
along the lines of

.. code-block:: shell

   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   path\to\astropix-analysis\setup.ps1
