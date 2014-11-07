Faros Streamer Overview
------------------------
Stream data from a Mega Electronics Ltd. Faros device (http://www.megaemg.com/products/faros/) using the Lab Streaming Layer (https://code.google.com/p/labstreaminglayer/).


License
--------

The files
- libfaros.py
- faros_streamer.pyw

constitute the software Faros Streamer and are licensed under the MIT License
http://opensource.org/licenses/mit-license.php
Please see the file LICENSE for more information.


Installation Instructions
-------------------------

Operating system: tested on GNU/Linux and Windows
Python version  : Python 2 (tested on Python 2.7.8)

Dependencies not in the Python standard library

- Python bindings for the Lab Streaming Layer
- PySerial
- Construct
- wxPython (GUI toolkit)
 

Installing dependencies
-----------------------
In order to install these dependencies, proceed as follows:

* Python bindings for the Lab Streaming Layer
Download and unpack
ftp://sccn.ucsd.edu/pub/software/LSL/SDK/liblsl-Python-1.10.2.zip
and place the files
- liblsl32.dll
- liblsl64.dll
- liblsl32.dylib
- liblsl64.dylib
- liblsl64.so
- pylsl.py

in the same directory as libfaros.py and faros_streamer.pyw.


* PySerial and Construct
Use PIP (http://en.wikipedia.org/wiki/Pip_%28package_manager%29) as follows:
pip install pyserial
pip install construct

alternatively, 

download the installers from
https://pypi.python.org/pypi/pyserial
https://pypi.python.org/pypi/construct/2.5.2#downloads

* wxPython
Please follow the installation instructions found in the wxPython wiki:
http://wiki.wxpython.org/How%20to%20install%20wxPython


Using Faros Streamer
--------------------
* First set the Faros device into Online mode using Faros Manager (in Windows) or by modifying the configuration file (in GNU/Linux).

* First pair the Faros bluetooth device with the computer and note the name of the serial port. The serial port is usually named, e.g., 'COMx' in Windows or '/dev/rfcommX' in Linux.

* Configuration

1. Start the GUI by running 'faros_streamer.pyw':
   - In Windows you can either double-click the file or type "pythonw.exe faros_streamer.pyw" in the Command Prompt.
   - In GNU/Linux you can either type "python2 faros_streamer.pyw"
2. Configure the measurement options (sampling rate, signal resolution, ...)
3. Choose which signals that are to be streamed over the Lab Streaming Layer using the checkboxes "ECG" and "Acc".
4. Configure the serial port (e.g. /dev/rfcomm0 on GNU/Linux or e.g. COM5 on Windows)
5. Set the names for the streams and the signal types. Note that the stream ID is hashed from the
   stream name, so that the same stream name always will give the same stream ID.

* Requesting information
You can request the software and hardware version of the Faros device by pressing "Info" button, after having configured the Serial port.
You can also use this to test that the connection to the Faros device works before starting to stream data.

* Starting the stream:
After configuring all the options (sampling rates, port, ...) you can start the stream by pressing the "Start" button.
Data from the Faros will now be streamed using the Lab Streaming Layer, and it can be accessed in other applications using the
Lab Streaming Layer, as described below.

* Stopping the Stream
You can stop the stream by pressing the Stop button.


Using the Lab Streaming Layer (LSL)
-----------------------------------
Please visit the website
https://code.google.com/p/labstreaminglayer/
for more information on the LSL.

* Accessing the stream from the Faros in your own software
After downloading and installing the LSL, you can access the LSL stream from your own applications as shown in the examples:
https://code.google.com/p/labstreaminglayer/wiki/ExampleCode

Bindings for the LSL are available for the following langauges: C, C++, Python, Java, C# and MATLAB.


* Visualising the stream from the Faros in Matlab
In Matlab, you can use the following softare to visualise the stream (ECG and/or acceleration):
https://code.google.com/p/labstreaminglayer/wiki/ViewingStreamsInMatlab
which can be downloaded from
ftp://sccn.ucsd.edu/pub/software/LSL/Apps/MATLAB%20Viewer-1.10.1.zip
