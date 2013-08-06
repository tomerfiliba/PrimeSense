Crayola: Next-Gen Pastel
========================

Crayola is a testing framework for PrimeSense devices that's based on OpenNI2 (utilized via the Python wrapper).
It provides a base class which tests should derive from (taking care of all the setup/teardown details),
as well as many helpers and utilities.

Writing Tests
-------------
Writing tests is quite simple. For example, here's a simple test that reads a frame from the device and validates
it's not all-zeros::

	from crayola import CrayolaTestBase
	from primesense import openni2
	
	class MySimpleTest(CrayolaTestBase):
		def test(self):
			s = self.device.create_color_stream()
			s.configure_mode(640, 480, 30, openni2.PIXEL_FORMAT_RGB888)
			f = s.read_frame()
			buf = f.get_buffer_as_int8()
			# check that at least one item in `buf` is nonzero
			assert any(buf)

Crayola gives you a ``.device`` attribute that holds the (first) device. If your host has more than one device
connected, you can access all of them as ``.devices``.

While you do have the full power of OpenNI at your finger tips, you might not want to work at such a level of details.
This is where Crayola kicks in and brings you higher-level building blocks. For instance, the same test above
can be written like so::

	class MySimpleTest(CrayolaTestBase):
		def test(self):
			s = self.get_color_stream(640, 480, 30)
			# read frames for 3 seconds and tollerate an error rate of 10% 
			self.verify_stream_fps(s, seconds = 3, error_threshold = 0.10)

A very useful function, ``verify_stream_fps`` will read frames from the stream for 3 seconds (under its current
configuration) and make sure that the number of frames read is within the expected number of frames +- the error 
threshold, that frame timestamps are monotonically increasing and that the number of empty frames is also low enough.

Another useful function is ``general_read_correctness``, which runs ``verify_stream_fps`` on all stream modes of
all connected devices. If allows you to bring the device to a certain state and quickly make sure its functioning 
properly.

Running Tests
-------------
Crayola relies on `nose <https://nose.readthedocs.org/en/latest/>`_, a simple and lightweight testing harness,
for running tests. Nose will automatically discover tests, but for that to work you must follow these simple rules:

* The name of your module has to start with ``test``, e.g., ``test_resets.py``
* The name of your test class can either begin with or end with ``Test``, e.g., ``MySimpleTest``
* In the test class, each method beginning with ``test`` will be executed as a separate test case.

.. note::
   There is no shared-state between test cases. Each test case runs in a new instance of the test class, and
   OpenNI itself is shutdown and re-initialized to ensure proper isolation. 

Running nose tests is very simple. Go to the directory where you placed your tests and run ::

    $ nosetest

In order to make the test report more readable (and easier to collect), Crayola also includes an Nose 
plugin that generates HTML reports. The report will be named ``nose_report.html`` and will be created 
in the current working directory. In order to run tests with this plugin, you must run nose with 
``--with-crayola-report`` -- or use ``crayrun.sh`` (can be found in the root of the repo).

Installation
------------
In order to run Crayola tests, there are number of required dependencies:

* `Nose <https://pypi.python.org/pypi/nose/1.3.0>`_
* `srcgen <https://pypi.python.org/pypi/srcgen>`_
* `OpenNI wrapper <https://pypi.python.org/pypi/primesense>`_

It's easiest to install these using `pip <http://www.pip-installer.org/en/latest/>`_, e.g.
``pip install nose``

You will also need to install the ``crayola-report`` plugin (``cd crayola-report; python setup.py install``),
and crayola itself.

The script ``install.sh`` (found in the root of the repo) can install these for you. 

API Reference
=============

crayola.testbase
----------------
.. automodule:: crayola.testbase
   :members:
   :undoc-members:


crayola.ext_device
------------------
.. automodule:: crayola.ext_device
   :members:
   :undoc-members:

crayola.specs
-------------
.. automodule:: crayola.specs
   :members:
   :undoc-members:


