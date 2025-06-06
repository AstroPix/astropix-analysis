.. develop:

Development
===========

Here are a few notes about the development process. Useful links:

* `github repo <https://github.com/AstroPix/astropix-analysis>`_
* `github issues <https://github.com/AstroPix/astropix-analysis/issues>`_


Linting
-------

The top-level Makefile provides a few linting-related target, leveraging some of the
most-widely used linters and static code analyzers.

.. literalinclude:: ../Makefile
   :end-before: test:

While sticking to any coding convention is not a goal, per se, running statick checks
on the code helps early identifications of potential problems. If you just run

.. code-block:: shell

   make

you will have a concise summary of the linting output.

.. note::

   We do run

   ```
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   ```

   in our continuos integration on github, so the latter will fail in case of
   severe problems, including

   * E9: Syntax Errors and Indentation Errors
   * F63: Incomplete or Invalid Comprehension Targets
   * F7: Forward Reference or Late Binding Issues
   * F82: Undefined Name in ``__all__``

   If and when we get particularly good at this we can include more check in the
   continuous integration, but for the moment we stick to a relaxed mood.


Unit tests
----------

All the unit tests are in the ``tests`` folder, and we use
`pytest <https://docs.pytest.org/en/stable/>`_ to run them.

You trigger the unit tests locally by doing

.. code-block::

   make test

In addition, we have

.. literalinclude:: ../.github/workflows/ci.yml


Documentation
-------------

All the documentation lives in ``docs`` and leverages the
`sphinx <https://www.sphinx-doc.org/en/master/>`_ system.

You trigger the compilation of the documentation locally by doing

.. code-block::

   make html

(The static html output lives in ``docs/_build/html/``.)
