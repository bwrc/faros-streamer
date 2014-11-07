#!/usr/bin/env python2

# Copyright 2014
# Andreas Henelius <andreas.henelius@ttl.fi>
# Finnish Institute of Occupational Health
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
#
# Please see the file LICENSE for details.

import wx
import libfaros as faros
import hashlib

import sys
from pylsl import StreamInfo, StreamOutlet
import random
import time

import threading

class WorkerThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self._parent = parent
        self.stream_data = False
        self.start()

    def run(self):
        self.stream_data = True
        faros.start_measurement(self._parent.faros_port, 5)

        while (self.stream_data):
            bytesToRead = self._parent.faros_port.inWaiting()
            if bytesToRead >= self._parent.packetsize:
                farosdata = self._parent.faros_port.read(self._parent.packetsize)
                packet = self._parent.packet_format.parse(farosdata)

                if ((packet["start_1"] != "\xcf") & (packet["start_2"] != "\xcf")):
                    self._parent.faros_port.flushInput()
                else:
                    if self._parent.stream_ecg.Value:
                        self._parent.faros_ecg_outlet.push_chunk(packet["ECG"])
                    if self._parent.stream_acc.Value:
                        self._parent.faros_acc_outlet.push_chunk(packet["acc"])

        self._parent.faros_port.flushInput()

    def abort(self):
        self.stream_data = False


class FarosStreamer(wx.Frame):
  
    def __init__(self, parent, title):
        super(FarosStreamer, self).__init__(parent, title = title, size = (430, 700))

        self.InitUI()
        self.Centre()
        self.Show()

        self.faros_port = None
       
        self.worker = None

    def InitUI(self):
        panel = wx.Panel(self, -1)

        menubar    = wx.MenuBar()
        fileMenu   = wx.Menu()
        fitem_quit = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')

        menubar.Append(fileMenu, '&File')

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnQuit, fitem_quit)

        # Select the sampling rates
        sampling_rates = ["1000 |  40",
                          "500  | 100",
                          "500  |  20", 
                          "250  | 100",
                          "250  |  50", 
                          "250  |  20", 
                          "125  | 100",
                          "125  |  50" ,
                          "125  |  25", 
                          "125  |  20", 
                          "100  | 100",
                          "100  |  20"]
        
        wx.StaticText(panel, label='Sampling rates: ECG | Acc', pos=(10, 20)).SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.fs = wx.ComboBox(panel, pos=(50, 50), value = "500  | 100", choices=sampling_rates, style=wx.CB_READONLY)
        wx.StaticText(panel, label='Hz', pos=(240, 55))

        # Signal resolutions
        res_ecg_choices = ["0.20", "1.00"]
        res_acc_choices = ["0.25", "1.00"]

        wx.StaticText(panel, label='Signal resolutions', pos=(10, 100)).SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.res_ecg = wx.ComboBox(panel, pos=(90, 125), value = "1.00", choices=res_ecg_choices, style=wx.CB_READONLY, size = (100, 30))
        self.res_acc = wx.ComboBox(panel, pos=(90, 165), value = "1.00", choices=res_acc_choices, style=wx.CB_READONLY, size = (100, 30))
        wx.StaticText(panel, label='ECG:', pos=(50, 130))
        wx.StaticText(panel, label='Acc:', pos=(50, 170))
        wx.StaticText(panel, label='muV / count', pos=(200, 130))
        wx.StaticText(panel, label='mg / count', pos=(200, 170))

        # ECG highpass filter
        hp_ecg_choices = ["1", "10"]
        wx.StaticText(panel, label='ECG highpass filter', pos=(10, 220)).SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.hp_ecg = wx.ComboBox(panel, pos=(50, 250), value = "1", choices=hp_ecg_choices, style=wx.CB_READONLY, size = (70, 30))
        wx.StaticText(panel, label='Hz', pos=(125, 260))

        # What signals to stream
        wx.StaticText(panel, label='Signals to stream', pos=(10, 300)).SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.stream_ecg = wx.CheckBox(panel, label='ECG', pos=(50, 330))
        self.stream_acc = wx.CheckBox(panel, label='Acc', pos=(130, 330))
        self.stream_ecg.SetValue(1)
        self.stream_acc.SetValue(1)

        # Serial port
        wx.StaticText(panel, label='Serial port', pos=(10, 375)).SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.port = wx.TextCtrl(panel, pos = (150, 370), size = (200, 30), value = "/dev/rfcomm0")

        # Stream names and unique IDs
        wx.StaticText(panel, label='Stream names and IDs', pos=(10, 420)).SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        
        wx.StaticText(panel, label='Stream 1', pos=(50, 450))
        wx.StaticText(panel, label='Stream 2', pos=(250, 450))

        self.stream_1_name = wx.TextCtrl(panel, pos = (50, 470), size = (130, 30), value = "Faros_ECG")
        self.stream_2_name = wx.TextCtrl(panel, pos = (250, 470), size = (130, 30), value = "Faros_ACC")

        self.stream_1_name.Bind(wx.EVT_TEXT, self.SetStream_1_ID)
        self.stream_2_name.Bind(wx.EVT_TEXT, self.SetStream_2_ID)

        self.stream_1_type = wx.TextCtrl(panel, pos = (50, 500), size = (130, 30), value = "ECG")
        self.stream_2_type = wx.TextCtrl(panel, pos = (250, 500), size = (130, 30), value = "Acc")

        self.stream_1_id = wx.TextCtrl(panel, pos = (50, 530), size = (130, 30), value = "c374d0066")
        self.stream_2_id = wx.TextCtrl(panel, pos = (250, 530), size = (130, 30), value = "044d9104f")
        
        wx.StaticText(panel, label='name', pos=(185, 475))
        wx.StaticText(panel, label='type', pos=(190, 505))
        wx.StaticText(panel, label='id', pos=(195, 535))

        wx.StaticLine(panel, -1, wx.Point(10, 570), size = (330, -1))

        # Buttons to Start and Stop the streamer
        self.button_info = wx.Button(panel, label = 'Info', pos = (50, 600))
        self.button_start = wx.Button(panel, label = 'Start', pos = (150, 600))
        self.button_stop = wx.Button(panel, label = 'Stop', pos = (248, 600))
        self.button_stop.Disable()

        self.button_info.Bind(wx.EVT_BUTTON, self.GetFarosInfo)
        self.button_start.Bind(wx.EVT_BUTTON, self.StartStream)
        self.button_stop.Bind(wx.EVT_BUTTON, self.StopStream)


        # Status bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Idle')

        # Show nice image of a Faros device
        farosimage = wx.Image('faros_red.png', wx.BITMAP_TYPE_ANY)
        farosimage = farosimage.Scale(100, 134, wx.IMAGE_QUALITY_HIGH)
        farosimage = farosimage.ConvertToBitmap()
        wx.StaticBitmap(panel, -1, farosimage, pos = (220, 220))

    def GetFarosInfo(self, e):
        self.statusbar.SetStatusText('Querying.')
        if (self.faros_port == None):
            self.faros_port = faros.connect(self.port.Value.encode('ascii', 'ignore'))

        firmware_build = faros.get_firmware_build_date(self.faros_port)
        firmware_version = faros.get_firmware(self.faros_port)
        self.statusbar.SetStatusText('Idle.       Version '+ firmware_version + ' (' + firmware_build + ')')

    def OnQuit(self, e):
        self.Close()

    def SetStream_1_ID(self, e):
        self.stream_1_id.SetValue(hashlib.md5(self.stream_1_name.Value).hexdigest()[1:10])

    def SetStream_2_ID(self, e):
        self.stream_2_id.SetValue(hashlib.md5(self.stream_2_name.Value).hexdigest()[1:10])

    def StartStream(self, e):
        # Enable the Stop button
        self.button_stop.Enable()

        # Disable the UI
        self.button_info.Disable()
        self.button_start.Disable()
        self.fs.Disable()
        self.hp_ecg.Disable()
        self.res_ecg.Disable()
        self.res_acc.Disable()
        self.stream_ecg.Disable()
        self.stream_acc.Disable()
        self.port.Disable()
        self.stream_1_name.Disable()
        self.stream_2_name.Disable()
        self.stream_1_type.Disable()
        self.stream_2_type.Disable()
        self.stream_1_id.Disable()
        self.stream_2_id.Disable()

        # Get sampling rates
        fs_tmp = self.fs.Value.split("|")
        fs_ecg = int(fs_tmp[0].strip())
        fs_acc = int(fs_tmp[1].strip())

        # Set parameters
        self.statusbar.SetStatusText('Configuring.')

        if (self.faros_port == None):
            self.faros_port = faros.connect(self.port.Value.encode('ascii', 'ignore'))

        faros.set_ecg_res(self.faros_port, self.res_ecg.Value)
        faros.set_acc_res(self.faros_port, self.res_acc.Value)
        faros.set_ecg_hpf(self.faros_port, self.hp_ecg.Value)
        faros.set_ecg_fs(self.faros_port, fs_ecg)
        faros.set_acc_fs(self.faros_port, fs_acc)

        ## Calculate the packet size
        self.packetsize = faros.get_packet_size(fs_ecg, fs_acc)
        self.packet_format = faros.get_packet_format(self.packetsize)
        acc_chunk_size = (self.packetsize - 64) / 2

        # Initialize LSL streams
        ## ECG
        if self.stream_ecg.Value:
            self.faros_ecg_info = StreamInfo(self.stream_1_name.Value, self.stream_1_type.Value, 1, fs_ecg, 'int16', self.stream_1_id.Value)
            self.faros_ecg_outlet = StreamOutlet(self.faros_ecg_info, chunk_size = 25, max_buffered = 1)

        ## Accelerometer
        if self.stream_acc.Value:
            self.faros_acc_info = StreamInfo(self.stream_2_name.Value, self.stream_2_type.Value, 3, fs_acc, 'int16', self.stream_2_id.Value)
            self.faros_acc_outlet = StreamOutlet(self.faros_acc_info, chunk_size = acc_chunk_size)

        # Start the streaming
        self.statusbar.SetStatusText('Streaming.')
        if not self.worker:
            self.worker = WorkerThread(self)


    def CleanStreams(self):
        if self.faros_ecg_info is not None:
            del(self.faros_ecg_outlet)
            del(self.faros_ecg_info)
            
        if self.faros_acc_info is not None:
            del(self.faros_acc_outlet)
            del(self.faros_acc_info)

                
    def StopStream(self, e):
        # Stop the streaming
        if self.worker:
            self.worker.abort()

        self.worker = None

        faros.stop_measurement(self.faros_port, "idle")

        # Set status
        self.statusbar.SetStatusText('Idle')

        # Disable the Stop-button
        self.button_stop.Disable()

        # Enable the UI
        self.button_info.Enable()
        self.button_start.Enable()
        self.fs.Enable()
        self.hp_ecg.Enable()
        self.res_ecg.Enable()
        self.res_acc.Enable()
        self.stream_ecg.Enable()
        self.stream_acc.Enable()
        self.port.Enable()
        self.stream_1_name.Enable()
        self.stream_2_name.Enable()
        self.stream_1_type.Enable()
        self.stream_2_type.Enable()
        self.stream_1_id.Enable()
        self.stream_2_id.Enable()
    
        self.CleanStreams()
        

if __name__ == '__main__':
    app = wx.App()
    FarosStreamer(None, title = 'Faros Streamer')
    app.MainLoop()

