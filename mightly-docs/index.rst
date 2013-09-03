Mightly: New Nightly
====================

Lessons from Nightly
--------------------
The previous nightly system consisted of thousands of lines of code and several XML configuration files.
While it probably began "clean" and well-designed, it quickly grew ad-hoc'ish, so the configuration files
told you only part of the story. Important details were hidden in the code. For instance, the code had a 
function that checked if it were building ``OPENNI2`` on ``WIN32`` and set various environment variables accordingly.

The lesson to be learned here is, such projects are too complex to "real configuration", forcing you to 
augment the configuration with code. And if this is the case, why bother maintaining 4 different XMLs and
countless lines of code for "parsing" them? Let's just use code -- but let's make it declarative.

Goals
-----
Mightly was designed from the grounds up to:
* Use Python for configuration
* Parallelize whenever possible
* Encourage code reuse
* Expose a declarative interface to the end user, but be easily extensible on the framework side ("just Python")

Design
------

Tasks
^^^^^
The basic unit of Mightly is the *task*. A task is basically a function (or rather, an object with a ``run`` method),
which takes in all sorts of configuration parameters and can *depend* on other tasks. For example, the NiTE builder 
task depends on the OpenNI builder task. 

There are effectively two kinds of tasks:
* Builders - clone a git repo, run the build script and return the built artifacts
* Testers - install requirements and run tests, generating an HTML report

The Framework
^^^^^^^^^^^^^
The framework behind tasks is quite straight-forward and basically provides utilities (such as cloning a git repo)
and reusable logic (like running tasks on different hosts in parallel), as well as the actual builders and testers.
The different tasks "know" one another; for example, ``NiteBuilder`` "knows" the ``OpenNIBuilder`` and sets the 
required environment variables, given that ``OpenNIBuilder`` placed its results in an agreed-upon location.

The framework relies on `RPyC <http://rpyc.rtfd.org>`_ for controlling its agents (hosts). An RPyC server is expected
to be up and running on each host.  

Configuration
-------------

Hosts
^^^^^
Hosts are the underlying "workers" on which tasks are executed. They are easily created using the ``Host`` 
class, e.g. ::

    sdk32 = Host("sdk32", gitbase = "/home/buildserver/outputs", 
        installbase = "/home/buildserver/installs")

You need to specify the host name, where git repositories will be created (``gitbase``) and where artifacts
would ultimately be installed (``installbase``). You can also specify the RPyC port to use (the default is
``18861``).

.. note:: An RPyC server is expected to be running on that host, bound to the specified port.

Builders
^^^^^^^^
Builders, or more specifically the ``GitBuilder`` class, check out a particular branch (or hash) of a 
git repository on all given hosts and run a build script. Each builder is expected to know where its build 
script is located and where the built artifacts are placed. The builder knows all this (part of the builder's 
code), instead of it being supplied as configuration, as it get quite complex. For once, the build script 
might require all sorts of environment variables that must be set externally.

A simple builder might be configured like the following::

	nite_task = NiteBuilder(Deps(openni_task = openni_task), hosts = {
	    sdk32 : [
	        Target("linux32", ["python", "ReleaseVersion.py", "x86"], 
	        	output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
	    ],
	    sdk64 : [
	        Target("linux64", ["python", "ReleaseVersion.py", "x64"], 
	        	output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
	        Target("arm", ["python", "ReleaseVersion.py", "Arm"], 
	        	output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
	    ],
	})

First come the builder's dependencies (other tasks, such as the ``nite_task``), followed by the hosts on which 
it should build (a dictionary of ``host : list of Targets``). Each host can build a number of ``Targets``,
which consist of a name, the command to run (and its arguments) and a glob-pattern that's used to collect the 
artifacts.

.. note:: 
   * When a builder is run, it executes in parallel on all hosts. Within each host, ``Targets`` are
     executed serially.
   * Builders remember the last git hash they've built and will skip building if the hash is the same and the 
     outputs exist (unless ``force_build = True``)


CrayolaTester
^^^^^^^^^^^^^

The ``CrayolaTester`` task depends on OpenNI, NiTE, the firmware and the wrapper builders, and takes care of 
orchestrating the show. It runs in parallel on each of its host, installs OpenNI and NiTE, as well as the the
Python wrapper and its dependencies and runs the tests (using ``nose``).

In the future it should also be able to upload the firmware onto the device, but this is not implemented at 
the time of writing.


Running Mightly
---------------
After you finished configuring your scenario, all you need to do is call is ``mightly_run``::

    if __name__ == "__main__":
        mightly_run([root_task1, root_task2, ...],
            to_addrs = ["my.email@primesense.com", "your.email@primesense.com"],
        )

This function will take care of running each task (including its dependencies), producing logs under a 
configurable directory (``G:\RnD\Software\Nightly_Builds`` by default), and sending an email report
to the given addresses.

The function will exit the process with an exit code of 0 upon success and 1 otherwise (you can prevent this 
by passing ``exit = False``).


