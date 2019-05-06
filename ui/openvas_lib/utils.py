# -*- coding: utf-8 -*-


"""
Utils functions, like timer and random string generator.
"""

import sys
from random import choice
from string import ascii_letters
from string import digits
from threading import Event
from threading import Timer

__license__ = """
Copyright 2018 - Golismero project

Redistribution and use in source and binary forms, with or without modification
, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.
"""


if sys.version_info >= (3,):
    _range = range
else:
    _range = xrange

# ------------------------------------------------------------------------------
#
# Useful functions
#
# ------------------------------------------------------------------------------
def set_interval(interval, times=-1):
    """
	Decorator to execute a function periodically using a timer.
	The function is executed in a background thread.

	Example:

		>>> from time import gmtime, strftime
		>>> @set_interval(2) # Execute every 2 seconds until stopped.
		... def my_func():
		...     print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
		...
		>>> handler = my_func()
		2013-07-25 22:40:55
		2013-07-25 22:40:57
		2013-07-25 22:40:59
		2013-07-25 22:41:01
		>>> handler.set() # Stop the execution.
		>>> @set_interval(2, 3) # Every 2 seconds, 3 times.
		... def my_func():
		...     print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
		...
		>>> handler = my_func()
		2013-07-25 22:40:55
		2013-07-25 22:40:57
		2013-07-25 22:40:59
	"""
    # Validate the parameters.
    if isinstance(interval, int):
        interval = float(interval)
    elif not isinstance(interval, float):
        raise TypeError("Expected int or float, got %r instead" % type(interval))
    if not isinstance(times, int):
        raise TypeError("Expected int, got %r instead" % type(times))

    # Code adapted from: http://stackoverflow.com/q/5179467

    # This will be the actual decorator,
    # with fixed interval and times parameter
    def outer_wrap(function):
        if not callable(function):
            raise TypeError("Expected function, got %r instead" % type(function))

        # This will be the function to be
        # called
        def wrap(*args, **kwargs):

            stop = Event()

            # This is another function to be executed
            # in a different thread to simulate set_interval
            def inner_wrap():
                i = 0
                while i != times and not stop.isSet():
                    stop.wait(interval)
                    function(*args, **kwargs)
                    i += 1

            t = Timer(0, inner_wrap)
            t.daemon = True
            t.start()

            return stop

        return wrap

    return outer_wrap


# ----------------------------------------------------------------------
def generate_random_string(length=30):
    """
	Generates a random string of the specified length.

	The key space used to generate random strings are:

	- ASCII letters (both lowercase and uppercase).
	- Digits (0-9).
	"""
    m_available_chars = ascii_letters + digits

    return "".join(choice(m_available_chars) for _ in _range(length))
