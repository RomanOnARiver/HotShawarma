
#!/usr/bin/python3
# coding=utf8

##    Hot Shawarma
##    Copyright (C) 2020 Roman Verzub
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import wx
import os
import sys
import socket
import urllib.request
from xml.etree.ElementTree import fromstring, ElementTree
import time
import appdirs # pip3 install appdirs
import configparser
import distutils.util
import datetime
import webbrowser

commandIsBeingIssued=True
roku_devices=[]
cids=[]
chanIsMenu=[]
macros=[['',''],['',''],['',''],['','']]
datadir=appdirs.AppDirs('Hot Shawarma','Nemmy Games').user_data_dir
print('datadir: '+datadir)
saveFileParser=configparser.ConfigParser()
inputs=[]


class MainWindow(wx.Frame):

    def beBusy(self,busy):
        if busy:
            print('Something is happening.')
            #wx.BeginBusyCursor()
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        else:
            print('Something is NOT happening.')
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

    def delay(self,time): # delay, time is in seconds
        print('Delaying for '+str(time)+' seconds...')
        sw=wx.StopWatch()
        sw.Start(milliseconds=0)
        t_prev=0
        while sw.Time()<time*1000: # seconds to millseconds
            if not int(sw.Time()/1000) == t_prev:
                print('Time elapsed: '+str(int(sw.Time()/1000))) # milliseconds to seconds
                t_prev=int(sw.Time()/1000)
        sw.Pause()

    def getIPAddress(self): # this gets used a lot
        return roku_devices[self.cbDevices.GetSelection()][0]

    def blockNonNumbers(self,e):
        key_code = e.GetKeyCode()

        if ord('0') <= key_code <= ord('9'): # allow numbers
            e.Skip()
            return

        if key_code == ord('\t'): # allow tabs to switch between controls
            e.Skip()
            return

        if key_code in (8,127,314,316): # allow backspace, delete, left, and right
            e.Skip()
            return

        return

    def cbType_Changed(self,e):
        if self.cbType.GetSelection()==2:
            self.txtSeason.Enable()
        else:
            self.txtSeason.Disable()
            self.txtSeason.Clear()


    def btnSearch_Clicked(self,e):
        print('Search!')
        w_height=325
        self.search=wx.Dialog(self,title='Search',size=(400,w_height)) # 400

        self.lblKeyword=wx.StaticText(self.search,label='Search:',pos=(15,35))
        self.txtKeyword=wx.TextCtrl(self.search,pos=(85,35),size=(285,35),style=wx.HSCROLL)

        #self.lblTitle=wx.StaticText(self.search,label='Or exact\ntitle:',pos=(15,75))
        #self.txtTitle=wx.TextCtrl(self.search,pos=(85,75),size=(285,35),style=wx.HSCROLL)

        self.rbKwd=wx.RadioButton(self.search,label='Keyword',pos=(85,85)) # 15, 85
        self.rbKwd.SetValue(True) # keyword by default - needed to be set specifically for mac
        self.rbExact=wx.RadioButton(self.search,label='Exact title',pos=(170,85)) #100, 85

        self.lblType=wx.StaticText(self.search,label='Type:',pos=(15,115))

        self.cbType=wx.Choice(self.search,pos=(85,115),size=(155,35),choices=['Any','Movie','TV Show','Person','Channel','Game'])
        self.cbType.SetSelection(0)
        #self.Bind(wx.EVT_CHOICE,self.cbType_Changed,self.cbType)
        self.cbType.Bind(wx.EVT_CHOICE,self.cbType_Changed)

        self.lblSeason=wx.StaticText(self.search,pos=(15,155),label='Season:')

        self.txtSeason=wx.TextCtrl(self.search,pos=(85,155),size=(155,35))
        #self.Bind(wx.EVT_CHAR,self.blockNonNumbers,self.txtSeason)
        self.txtSeason.Bind(wx.EVT_CHAR,self.blockNonNumbers)
        self.txtSeason.Disable() # only enabled if type is 2 (tv-show)

        self.chkIncludeUnavail=wx.CheckBox(self.search,pos=(15,195),label='Include content that is unavailable')
        self.chkIncludeUnavail.SetValue(True) # checked by default per discussion on usability

        self.btnSearchGo=wx.Button(self.search,id=wx.ID_OK,label='Search',pos=(285,w_height-80),size=(90,30)) # 320 # treat like an OK button (ie. close the window)
        self.btnSearchCancel=wx.Button(self.search,id=wx.ID_CANCEL,label='Cancel',pos=(190,w_height-80),size=(90,30)) # 320
        
        searchRes=self.search.ShowModal()

        kwd=''
        ttl=''
        typ=''
        seas=''
        if not searchRes==wx.ID_CANCEL: # search
            print('Keyword: '+str(self.rbKwd.GetValue())+'\tExact title: '+str(self.rbExact.GetValue()))
            self.beBusy(True)
            #if not self.txtKeyword.GetValue() == '':
            if self.rbKwd.GetValue()==True:
                kwd='keyword='+urllib.parse.quote(self.txtKeyword.GetValue())
                ttl=''
            else:
                kwd='keyword=' # keyword is a required argument even if it's blank, in which case exact title is required
                ttl='&title='+urllib.parse.quote(self.txtKeyword.GetValue())
            print('kwd: '+kwd)
##            if not self.txtTitle.GetValue()=='':
##                ttl='&title='+urllib.parse.quote(self.txtTitle.GetValue())
##            else:
##                ttl=''
            print('ttl: '+str(ttl))
            if not self.cbType.GetCurrentSelection()==0:
                typ='&type='+self.cbType.GetString(self.cbType.GetCurrentSelection()).replace(' ','-').lower()
            else:
                typ=''
            print('typ: '+str(typ))

            if not self.txtSeason.GetValue()=='':
                seas='&season='+self.txtSeason.GetValue()
            else:
                seas=''

            print('seas: '+seas)
            
            su='&show-unavailable='+str(self.chkIncludeUnavail.GetValue()).lower()
            print('su: '+str(su))
            print('wget -O- --post-data=\'\' \'http://'+self.getIPAddress()+':8060/search/browse?'+kwd+ttl+typ+seas+su+'\'')
            req=urllib.request.Request('http://'+self.getIPAddress()+':8060/search/browse?'+kwd+ttl+typ+seas+su,data=''.encode())
            try:
                resp=urllib.request.urlopen(req)
            except Exception as e:
                self.disableOnError('Error: '+str(e))
            else:
                pge=resp.read().decode()
                print('\n\n'+pge+'\n\n')

                #self.btnRemoteEnter_Clicked(0)

            self.delay(5)
            self.btnRefreshCurrentChannel_Clicked(0)
            
            self.beBusy(False)
                

    def disableOnError(self,error):
        dependentControls=[self.btnRefreshCurrentChannel,self.btnRefreshInstalledChannels,self.lbChannelSelector,self.btnSearch,self.btnLaunchChannel,self.btnRemoteBack,self.btnRemoteHome,self.btnRemoteUp,self.btnRemoteDown,self.btnRemoteLeft,self.btnRemoteRight,self.btnRemoteOK,self.btnRemoteReplay,self.btnRemoteVoice,self.btnRemoteInfo,self.btnRemoteReverse,self.btnRemotePlayPause,self.btnRemoteForward,self.btnMacro0,self.btnMacro1,self.btnMacro2,self.btnMacro3]

        msg=wx.MessageDialog(self,message=error,caption='Error',style=wx.OK|wx.OK_DEFAULT|wx.ICON_ERROR)
        msg.ShowModal()
        self.lblFindRemote.Disable()
        self.lblFindRemote.Hide()
        self.btnFindRemote.Disable()
        self.btnFindRemote.Hide()
        self.inputs.DeleteAllItems()
        self.enableOrDisableTVItems(False)
        self.cbDevices.Clear()
        self.cbDevices.Disable()
        self.bmpCurrentChannel.Hide()
        self.lblChannelID.SetLabel('')
        self.lblCurrentChannel.SetLabelMarkup('<u>Current channel:</u>\n...')
        self.lbChannelSelector.Clear()
        for control in dependentControls:
            control.Disable()

    def checkForSearchEnabled(self):
        print('Checking to see if this device supports search...')
        ret=False
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/query/device-info')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
                #print(child.tag,child.text)
            for device in root.iter('search-enabled'):
                print('Does the device support search? ' +str(bool(distutils.util.strtobool(device.text))))
                ret=bool(distutils.util.strtobool(device.text))
            #print('\n\n'+pge+'\n\n')
        #ret=True # for debugging/layout design
        #print('ret: '+str(ret))
        return ret

    def checkForFindRemote(self):
        print('Checking to see if this device supports FindRemote...')
        ret=[]
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/query/device-info')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
                #print(child.tag,child.text)
            for device in root.iter('supports-find-remote'):
                print('Does the device support FindRemote? ' +str(bool(distutils.util.strtobool(device.text))))
                ret.append(bool(distutils.util.strtobool(device.text)))
                if bool(distutils.util.strtobool(device.text)): # If it's theoretically possible, let's see if it's actually possible on the current remote
                    for device in root.iter('find-remote-is-possible'):
                        print('Is FindRemote possible with the current remote? ' +str(bool(distutils.util.strtobool(device.text))))
                        ret.append(bool(distutils.util.strtobool(device.text)))

        #ret=[True,True] # only for debugging and layout design
        #print('ret: '+str(ret))
        return ret

    def checkForVoiceSearch(self):
        print('Checking to see if voice search is supported...')

        ret=False
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/query/device-info')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
                #print(child.tag,child.text)
            for device in root.iter('voice-search-enabled'):
                print('Does the device support voice search? ' +str(bool(distutils.util.strtobool(device.text))))
                ret=bool(distutils.util.strtobool(device.text))

        #print('ret: '+str(ret))
        return ret

    def checkForTV(self):
        print('Checking to see if the device is a TV...')

        ret=False
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/query/device-info')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
                #print(child.tag,child.text)
            for device in root.iter('is-tv'):
                print('Is the device a TV? ' +str(bool(distutils.util.strtobool(device.text))))
                ret=bool(distutils.util.strtobool(device.text))

        #ret=True # for debugging/layout design
        #print('ret: '+str(ret))
        return ret



    def btnFindRemote_Clicked(self,e):
        print('Finding remote...')

        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/FindRemote',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def findRokus(self):
        print('Searching for Rokus on the network...')

        roku_devices.clear()
        
        discover_timeout=2 # TODO: Make this variable ???
        discover_message = 'M-SEARCH * HTTP/1.1\r\nHost: 239.255.255.250:1900\r\nMan: \"ssdp:discover\"\r\nST: roku:ecp\r\n'.encode() # SSDP for device discovery, per https://developer.roku.com/docs/developer-program/debugging/external-control-api.md#simple-service-discovery-protocol-ssdp


        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.settimeout(discover_timeout)

        ret=[]

        try:
            s.sendto(discover_message,('239.255.255.250', 1900))
        except Exception as e:
            msg=wx.MessageDialog(self,message='Error: '+str(e),caption='An error has occurred',style=wx.OK|wx.OK_DEFAULT|wx.ICON_ERROR)
            msg.ShowModal()
            return []
        
        try:
            while True:
                data, addr = s.recvfrom(65507)
                if 'roku' in str(data) or 'Roku' in str(data): # TODO: Is this correct? can we get properties from the device instead of seaching like this?
                    print('Found roku at '+addr[0]+'.') # There's other data, but we don't care about it
                    ret.append([addr[0],''])
                    #devices[len(devices)-1]=(addr[0],'')\
                else:
                    print('Found non-roku device at '+addr[0]+'.')
        except socket.timeout:
            print('Timeout.')
            pass
        
        #print('Devices addresses: '+str(ret))
        #print(str(len(ret)))
        for c in range(0,len(ret)):
            print('Searching item '+str(c)+' of '+str(len(ret))+'...')
            print('Getting name of device at address '+ret[c][0]+'...')
            req=urllib.request.Request('http://'+ret[c][0]+':8060/query/device-info')
            resp=urllib.request.urlopen(req)
            pge=resp.read().decode()
            print('\n\n'+pge+'\n\n') # this is the only full response we want to see, for debug purposes on some smart tv features
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            ##for child in root:
            ##    print(child.tag,child.text)
            for device in root.iter('friendly-device-name'):
                #print(device.text)
                ret[c][1]=device.text
                roku_devices.append((ret[c][0],ret[c][1]))


            print('ret: '+str(ret))
            #print('roku_devices at set: '+str(roku_devices))
        return ret

    def getPowerState(self,ip):
        print('Getting power state of IP '+ip+'...')
        ret=None
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/query/device-info')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
                #print(child.tag,child.text)
            for device in root.iter('power-mode'):
                print('Current power mode: ' +device.text)
                if device.text=='PowerOn' or device.text=='DisplayOn': # just guessing about that last one
                    ret=True
                elif device.text=='Headless' or device.text=='DisplayOff' or device.text=='Ready' or device.text=='PowerOff': # just guessing about the last one
                    ret=False
                else:
                    self.disableOnError('Error: Unsupported TV state: '+str(device.text))

        return ret

            
    def getCurrentChannel(self,ip):
        print('Getting the current channel for '+ip+'...')
        ret=-1
        req=urllib.request.Request('http://'+ip+':8060/query/active-app')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
                #print(child.tag,child.text)
            for device in root.iter('app'):
                #ret[c][1]=device.text
                if device.get('type')=='appl': # regular channels, which have an ID
                    ret=[device.text,device.get('id')]
                    self.lblCurrentDChannel.Disable()
                    self.lblCurrentDChannel.Hide()
                elif device.get('type')=='tvin': # tvinputs, which have an ID, but need to be treated differently in labeling
                    ret=[device.text+' ('+device.get('id').replace('tvinput.','').upper()+')',device.get('id')] # "tvinput.hdmi1" becomes "HDMI1", TODO: CVBS should become AV1
                    if device.get('id')=='tvinput.dtv':
                        print('This is digital TV.')
                        currentDChannelInfo=self.getCurrentDChannel(self.getIPAddress())
                        self.lblCurrentDChannel.SetValue('Channel: '+str(currentDChannelInfo[0])+' '+str(currentDChannelInfo[1])+'\nQuality: '+str(currentDChannelInfo[2])+'\nProgram: '+str(currentDChannelInfo[3])+'\nDescription: '+str(currentDChannelInfo[4])+'\nRating: '+str(currentDChannelInfo[5]))
                        #self.lblCurrentDChannel.Wrap(width=200)
                        print('Showing and enabling DChannelInfo button...')

                        self.lblCurrentDChannel.Show()
                        self.lblCurrentDChannel.Enable()

                    else:
                        print('This is NOT digital TV.')
                        self.lblCurrentDChannel.Disable()
                        self.lblCurrentDChannel.Hide()
                else:
                    ret=[device.text,-1] # Other screens like the home screen that do not have an ID
                    self.lblCurrentDChannel.Disable()
                    self.lblCurrentDChannel.Hide()
            for device in root.iter('screensaver'):
                #ret[c][1]=device.text
                ret=[device.text,device.get('id')]


        return ret

    def getCurrentDChannel(self,ip):
        print('Getting the current digital TV channel of '+ip+'...')

        ret=['','','','','','']
        req=urllib.request.Request('http://'+ip+':8060/query/tv-active-channel')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            for child in root:
                for subchild in child:
                    #print(subchild.tag,subchild.text)
                    if subchild.tag=='number':
                        ret[0]=subchild.text
                    if subchild.tag=='name':
                        ret[1]=subchild.text
                    if subchild.tag=='signal-mode':
                        ret[2]=subchild.text
                    if subchild.tag=='program-title':
                        ret[3]=subchild.text
                    if subchild.tag=='program-description':
                        ret[4]=subchild.text
                    if subchild.tag=='program-ratings':
                        ret[5]=subchild.text

        print(ret)
        return ret

    def btnDChannelInfo_Clicked(self,e):
        currentDChannelInfo=self.getCurrentDChannel(self.getIPAddress())
        msg=str(currentDChannelInfo[0])+' '+str(currentDChannelInfo[1])+' ('+str(currentDChannelInfo[2])+')\n'+str(currentDChannelInfo[3])+'\n'+str(currentDChannelInfo[4])+'\nRating: '+str(currentDChannelInfo[5])
        msg=wx.MessageDialog(self,message=msg,caption='Information',style=wx.OK|wx.OK_DEFAULT|wx.ICON_INFORMATION)
        msg.ShowModal()
        
    
    def getCurrentChannelType(self,ip):
        print('Getting the current channel type for '+ip+'...')
        ret=-1
        req=urllib.request.Request('http://'+ip+':8060/query/active-app')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
##            print(root.tag,root.attrib)
##            for child in root:
##                print(child.tag,child.text)
            for device in root.iter('app'):                
                if device.get('type')=='appl': # this means it's a normal channel
                    ret='app'
                elif device.get('type')=='tvin': # tv inputs do not have channel icons as far as I know - though they have internal icons from the home screen, so maybe there's a way to pull those?
                    ret='tvinput'
                else:
                    ret='home' # this doesn't have to be the home screen, but it's any screen labeled an "app" but without an app id (and thus no icon)
            for device in root.iter('screensaver'):
                ret='screensaver'

        print('The current channel is of type: '+str(ret))
        return ret

    def getChannelIcon(self,ip,cid):
        print('Getting the channel icon for '+str(cid)+' on '+ip+'...')
        self.beBusy(True)
        #req=urllib.request.Request('http://'+ip+':8060/query/icon/'+cid)
        if self.getCurrentChannelType(ip)=='app' or self.getCurrentChannelType(ip)=='screensaver': # only channels and screensavers have icons, IDs, etc.
            try:
                file_name,headers=urllib.request.urlretrieve('http://'+ip+':8060/query/icon/'+cid)
            except Exception as e:
                self.disableOnError('Error: '+str(e))
            else:
                self.lblCurrentDChannel.SetLabelMarkup('')
                #print('file_name: '+str(file_name)+'\nheaders: '+str(headers))
                image=wx.Image(file_name,wx.BITMAP_TYPE_ANY).Rescale(width=145,height=109,quality=wx.IMAGE_QUALITY_NORMAL).ConvertToBitmap() # Resize the image now, to avoid having to add imagemagick as a dependency
                self.bmpCurrentChannel.SetBitmap(image)
                os.remove(file_name) # Remove the file right away that we have no use for anymore
                self.bmpCurrentChannel.Enable()
                self.bmpCurrentChannel.Show()

                if self.getCurrentChannelType(ip)=='app': # is a roku channel, show the icon and id
                    self.cidtip=wx.ToolTip('Channel ID: '+str(cid))
                    self.bmpCurrentChannel.SetToolTip(self.cidtip)
                    self.lblChannelID.SetLabel('Channel ID: '+str(cid))

                    self.lblChannelID.Enable()
                    self.lblChannelID.Show()

                    
                else: # not a roku channel hide the icon and id
                    self.lblChannelID.SetLabel('')
                    self.bmpCurrentChannel.SetToolTip(None)
                    self.lblChannelID.Disable()
                    self.lblChannelID.Hide()
                    
        else: # TV inputs and home menus have no channel icons, IDs, etc.
            self.bmpCurrentChannel.SetToolTip(None)
            self.bmpCurrentChannel.Hide()
            self.bmpCurrentChannel.Disable()
            
            self.lblChannelID.SetLabel('')
            self.lblChannelID.Hide()
            self.lblChannelID.Disable()
        
        self.beBusy(False)
        
              
    def getAllChannels(self,ip):
        print('Getting all channels at IP '+ip+'...')
        ret=[]
        cids.clear()
        chanIsMenu.clear()
        req=urllib.request.Request('http://'+ip+':8060/query/apps')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
            #    print(child.tag,child.text)
            for device in root.iter('app'):
                if device.get('type')=='appl' or device.get('type')=='menu': # menu items like the Fandango store - they take you to a menu but aren't a channel by themselves. The first-party mobile app includes them so I figure I need to as well.
                    #print(device.text)
                    #ret[c][1]=device.text
                    #roku_devices.append((ret[c][0],ret[c][1]))
                    ret.append(device.text)
                    cids.append(device.get('id'))
                    if device.get('type')=='menu':
                        chanIsMenu.append(True)
                    else:
                        chanIsMenu.append(False)

        print('All the channel IDs: '+str(cids))
        print('chanIsMenu: '+str(chanIsMenu))
        return ret

    def getNumHDMI(self,ip):
        print('Getting HDMI inputs at IP '+ip+'...')
        ret=[]
        req=urllib.request.Request('http://'+ip+':8060/query/apps')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
            #    print(child.tag,child.text)
            for device in root.iter('app'):
                if device.get('type')=='tvin':
                    #print(device.text)
                    if 'tvinput.hdmi' in device.get('id'):
                        ret.append(device.get('id'))

        print('Number of HDMI ports: '+str(len(ret))+'.')
        return len(ret)

    def refreshTVInputs_Clicked(self,e):
        print('Refresh current inputs...')
        self.inputs.DeleteAllItems()
        inps=self.getAllInputs(self.getIPAddress()) # inps as in inputs, not imps as in those fairy-demon creatures
        print('inps: '+str(inps))
        for c in range(len(inps)):
            print('['+str(c)+']: '+str(inps[c]))
            inpname=inps[c][0] # of course tuples are immutable so let's grab a string real quick
##            if inpname=='tvinput.cvbs': # save everyone headache in the future
##                inpname='tvinput.av1'
##            if inpname=='tvinput.dtv':
##                inpname='tvinput.tuner'
            inpname='tvinput.'+self.convertInternalToFriendly(inpname.replace('tvinput.',''))
            print('inpname should be: '+inpname.lower())
            self.inputs.Append((inpname.replace('tvinput.','').upper(),inps[c][1]))
            self.inputs.Select(0) # make sure there's always a selected input
            
##        self.inputs.SetColumnWidth(0,wx.LIST_AUTOSIZE_USEHEADER) # commented out because we want to set static column widths to avoid horizontal scroll bars on unnecessarily-long input names
##        self.inputs.SetColumnWidth(1,wx.LIST_AUTOSIZE_USEHEADER)


##    def refreshTVInputs_Clicked(self,e): # this version is for debugging/layout design
##        print('Refresh current inputs...')

    def getAllInputs(self,ip):
        print('Getting all inputs at IP '+ip+'...')
        ret=[]
        req=urllib.request.Request('http://'+ip+':8060/query/apps')
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            tree=ElementTree(fromstring(pge))
            root=tree.getroot()
            #print(root.tag,root.attrib)
            #for child in root:
            #    print(child.tag,child.text)
            for device in root.iter('app'):
                if device.get('type')=='tvin':
                    #print(device.text)
                    #ret[c][1]=device.text
                    #roku_devices.append((ret[c][0],ret[c][1]))
                    ret.append((device.get('id'),device.text))

        ret.sort() # sort so hdmi1 is first, etc.

        print('All the inputs: '+str(ret))
        return ret

    def convertInternalToFriendly(self,internal): # cvbs to AV1 and dtv to Tuner
        print('Converting the internal '+internal+' to friendly...')
        ret=internal.upper()
        if internal=='CVBS':
            ret='AV1'
        elif internal=='DTV':
            ret='Tuner'

        print('End result: '+ret)
        return ret
 
    def convertFriendlyToInternal(self,friendly): # AV1 to cvbs and Tuner to dtv
        print('Converting the friendly '+friendly+' to internal...')
        ret=friendly.upper()
        if friendly=='AV1':
            ret='cvbs'
        elif friendly=='TUNER':
            ret='dtv'

        print('End result: '+ret)
        return ret

    def switchTVInput_Clicked(self,e):
        print('Switching input to '+self.inputs.GetItem(self.inputs.GetFirstSelected(),col=0).GetText()+'...')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Input'+self.convertInternalToFriendly(self.inputs.GetItem(self.inputs.GetFirstSelected(),col=0).GetText()),data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

        print('Testing: '+str(self.inputs.GetItem(self.inputs.GetFirstSelected(),col=0).GetText()))
        #while not self.getCurrentChannelType(self.getIPAddress())=='tvinput':
        while not self.getCurrentChannelType(self.getIPAddress())=='tvinput' and self.getCurrentChannel(self.getIPAddress())[1]=='tvinput.'+self.convertFriendlyToInternal(self.inputs.GetItem(self.inputs.GetFirstSelected(),col=0).GetText().lower()):
            print('Waiting on the change of input...')
            next
        self.lblCurrentDChannel.SetLabelMarkup('')

        self.btnRefreshCurrentChannel_Clicked(0)
        delamt=5 # two seconds for loading the input, 3 more for for the update
        if self.convertFriendlyToInternal(self.inputs.GetItem(self.inputs.GetFirstSelected(),col=0).GetText().lower())=='DTV': # additional time for metadata from digital tv to show up
            delamt=9
        print('delamt: '+str(delamt))
        self.delay(delamt) 
        self.btnRefreshCurrentChannel_Clicked(0)

    def btnMacro0_Clicked(self,e):
        print('Macro 0')
        self.processMacro(0)

    def btnMacro1_Clicked(self,e):
        print('Macro 1')
        self.processMacro(1)

    def btnMacro2_Clicked(self,e):
        print('Macro 2')
        self.processMacro(2)

    def btnMacro3_Clicked(self,e):
        print('Macro 3')
        self.processMacro(3)

    def processMacro(self,macro):
            print('Processing macro '+str(macro)+'...')
            editing=False
            running=False
            print('macros['+str(macro)+']: '+str(macros[macro]))
            if macros[macro]==['','']:
                editing=True
            else:
                sel=wx.SingleChoiceDialog(self,message='Please select an option:',caption='Macro '+str(macro),choices=['Run','Edit','Delete'],style=wx.OK|wx.CANCEL)
                selres=sel.ShowModal() # possible values are 0 for run, 1 for edit, 2 for delete, wx.ID_CANCEL for cancel
                if not selres==wx.ID_CANCEL:
                    if sel.GetSelection()==0:
                        running=True # explosions of the sea
                    if sel.GetSelection()==1:
                        editing=True
                    elif sel.GetSelection()==2:
                        suredelete=wx.MessageDialog(self,message='Are you sure you want to delete this macro?',caption='Are you sure?',style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
                        suredeleteval=suredelete.ShowModal()
                        if suredeleteval==wx.ID_YES:
                            print('Deleting.') # there's no green beans? green beans are a delicacy!

                            saveFileParser.set('macros','macro'+str(macro)+'name','')
                            saveFileParser.set('macros','macro'+str(macro)+'macro','')
                            with open(datadir+'/macros.ini','w') as configfile:
                                saveFileParser.write(configfile)
                                
                            if macro==0: # Python has no switch-case and won't let me append strngs to variables. Maybe if I made the macro buttons a list ???
                                self.btnMacro0.SetLabel('(none set)')
                            elif macro==1:
                                self.btnMacro1.SetLabel('(none set)')
                            elif macro==2:
                                self.btnMacro2.SetLabel('(none set)')
                            elif macro==3:
                                self.btnMacro3.SetLabel('(none set)')
                            macros[macro]=['','']
                            deleted=wx.MessageDialog(self,message='Your macro was deleted.',caption='Deleted',style=wx.OK|wx.ICON_INFORMATION).ShowModal()
                        else:
                            print('Not deleting.')
                            deleted=wx.MessageDialog(self,message='Your macro was not deleted.',caption='Not deleted',style=wx.OK|wx.ICON_INFORMATION).ShowModal()
                    else:
                        print('Cancel.')
        
            if editing:
                print('We are editing!')
                w_height=450
                self.macro=wx.Dialog(self,title='Macro Editor: Macro '+str(macro),size=(425,w_height)) # 400

                self.lblMacroName=wx.StaticText(self.macro,label='Name:\n(optional)',pos=(15,35))

                self.txtMacroName=wx.TextCtrl(self.macro,pos=(85,35),size=(100,35))
                self.txtMacroName.SetMaxLength(10)

                self.lblMacro=wx.StaticText(self.macro,label='Macro:\n(required)',pos=(15,75))

                self.txtMacroText=wx.TextCtrl(self.macro,pos=(85,75),size=(285,35),style=wx.HSCROLL)

                if not macros[macro]==['','']:
                    self.txtMacroName.SetValue(macros[macro][0])
                    self.txtMacroText.SetValue(macros[macro][1])

                self.macroKeyLeft=wx.StaticText(self.macro,label='',pos=(15,110))
                self.macroKeyLeft.SetLabelMarkup('<u>Key:</u>\n\nb Back\nu Up\nl Left\no OK\nv Voice\ne Reverse\n\nw Wait (seconds)\na (A) Launch channel')

                self.macroKeyRight=wx.StaticText(self.macro,label='\n\nh Home\nd Down\nr Right\ni Replay\nn Info\nf F. Fwd\n\ns Send literal (char)\nt Enter',pos=(300,110))

                if self.checkForFindRemote()==[True,True]:
                    self.FindRemoteMacroKeyLeft=wx.StaticText(self.macro,label='m Find remote',pos=(15,280))                    

                if self.checkForTV():
                    self.TVMacroKeyLeft=wx.StaticText(self.macro,label='~ Change channel (#)\n@ Channel (+/-)\n# Change input (h#, a#, t)',pos=(15,300))
                    self.TVMacroKeyRight=wx.StaticText(self.macro,label='! Volume (+/-)\np Power\nz Sleep',pos=(300,300))


                self.btnMacroSave=wx.Button(self.macro,id=wx.ID_OK,label='Save',pos=(285,w_height-80),size=(90,30)) # 320
                self.btnMacroCancel=wx.Button(self.macro,id=wx.ID_CANCEL,label='Cancel',pos=(190,w_height-80),size=(90,30)) # 320
                
                macroRes=self.macro.ShowModal()

                if not macroRes==wx.ID_CANCEL:
                    print('Save the macro...')
                    # TODO: Further validate before saving
                    if self.txtMacroName.GetValue().strip()=='':
                        self.txtMacroName.SetValue('Macro '+str(macro))
                    # TODO: Don't continue if macro is blank
                    macros[macro][0]=self.txtMacroName.GetValue().strip()
                    macros[macro][1]=self.txtMacroText.GetValue().strip()
                    print('Macros: '+str(macros))

                    saveFileParser.set('macros','macro'+str(macro)+'name',macros[macro][0])
                    saveFileParser.set('macros','macro'+str(macro)+'macro',macros[macro][1])
                    with open(datadir+'/macros.ini','w') as configfile:
                        saveFileParser.write(configfile)
                        
                    if macro==0: # Python has no switch-case and won't let me append strngs to variables. Maybe if I made the macro buttons a list ???
                        self.btnMacro0.SetLabel(macros[macro][0])
                    elif macro==1:
                        self.btnMacro1.SetLabel(macros[macro][0])
                    elif macro==2:
                        self.btnMacro2.SetLabel(macros[macro][0])
                    elif macro==3:
                        self.btnMacro3.SetLabel(macros[macro][0])
                    else:
                        print('Cancelled editing/creating a macro. Nothing saved.')
            if running:
                print('We are executing!')
                mac2ex=macros[macro][1]
                mac2exsplit=mac2ex.split(' ')
                print('mac2ex: '+str(mac2ex)+' mac2exsplit: '+str(mac2exsplit))
                for c in range(0,len(mac2exsplit)):
                    if mac2ex=='uuddlrlrba': # eegg
                        print('Loading the eegg...')
                        msg=wx.MessageDialog(self,message='Hi Seth.',caption='NG',style=wx.OK|wx.OK_DEFAULT|wx.ICON_INFORMATION)
                        msg.ShowModal()
                        webbrowser.open('https://youtu.be/u9gCpag84-E?t=55')
                    else:
                        print('Executing macro item '+str(c+1)+' of '+str(len(mac2exsplit))+'...')
                        mac2comm=str(mac2exsplit[c][0])
                        mac2cur=mac2exsplit[c][1:]
                        print('mac2comm: '+mac2comm+' mac2cur: '+str(mac2cur))
                        if mac2comm=='b': # python still in 2020 has no switch-case which is fucking terrible design https://www.python.org/dev/peps/pep-3103/
                            self.btnRemoteBack_Clicked(0)
                        elif mac2comm=='u':
                            self.btnRemoteUp_Clicked(0)
                        elif mac2comm=='l':
                            self.btnRemoteLeft_Clicked(0)
                        elif mac2comm=='o':
                            self.btnRemoteOK_Clicked(0)
                        elif mac2comm=='v':
                            self.btnRemoteVoice_Clicked(0)
                        elif mac2comm=='e':
                            self.btnRemoteReverse_Clicked(0)
                        elif mac2comm=='w':
                            #time.sleep(int(mac2cur))
                            self.delay(int(mac2cur))
                        elif mac2comm=='a':
                            self.launchChannelByCID(int(mac2cur))
                        elif mac2comm=='A':
                            self.tryLaunchChannelByCID(int(mac2cur))
                        elif mac2comm=='h':
                            self.btnRemoteHome_Clicked(0)
                        elif mac2comm=='d':
                            self.btnRemoteDown_Clicked(0)
                        elif mac2comm=='r':
                            self.btnRemoteRight_Clicked(0)
                        elif mac2comm=='i':
                            self.btnRemoteReplay_Clicked(0)
                        elif mac2comm=='n':
                            self.btnRemoteInfo_Clicked(0)
                        elif mac2comm=='f':
                            self.btnRemoteForward_Clicked(0)
                        elif mac2comm=='s':
                            self.sendLiteral(mac2cur)
                        elif mac2comm=='t':
                            self.btnRemoteEnter_Clicked(0)
                            
                        # Below are macro features mostly for TV devices/enhanced voice remote.
                        elif mac2comm=='m': # find remote
                            self.btnFindRemote_Clicked(0)
                        elif mac2comm=='~': # change channel via the tuner (e.g. 1.1)
                            if not mac2cur == '':
                                self.launchChannelTuner(float(mac2cur))
                            else:
                                self.launchChannelTuner('')
                        elif mac2comm=='!': # volume +/-
                            if mac2cur=='+':
                                self.btnTVVolUp_Clicked(0)
                            elif mac2cur=='-':
                                self.btnTVVolDown_Clicked(0)
                        elif mac2comm=='@': # channel +/-
                            if mac2cur=='+':
                                self.btnTVChanUp_Clicked(0)
                            elif mac2cur=='-':
                                self.btnTVChanDown_Clicked(0)
                        elif mac2comm=='#': # change input (tuner, hdmi, av)
                            if mac2cur=='t':
                                self.btnTVInputTuner_Clicked(0)
                            elif mac2cur[0]=='h':
                                self.btnTVInputHDMI_Clicked(0,int(mac2cur[1]))
                            elif mac2cur[0]=='a':
                                self.btnTVInputAV_Clicked(0,int(mac2cur[1]))
##                            elif mac2curr=='h1':
##                                self.btnTVInputHDMI1_Clicked(0)
##                            elif mac2curr=='h2':
##                                self.btnTVInputHDMI2_Clicked(0)
##                            elif mac2curr=='h3':
##                                self.btnTVInputHDMI3_Clicked(0)
##                            elif mac2curr=='h4':
##                                self.btnTVInputHDMI4_Clicked(0)
##                            elif mac2curr=='a1':
##                                self.btnTVInputAV1_Clicked(0)
                        elif mac2comm=='p': # power off (or maybe suspend? who knows? TODO: See if TV devices return true for supports-suspend from device-info)
                            self.btnPowerOff_Clicked(0)
                        elif mac2comm=='z': # sleep
                            self.btnSleep_Clicked(0)

                if 'A' in mac2ex: # Make sure the current channel is up to date, because "A" never refreshes
                    self.btnRefreshCurrentChannel_Clicked(0)
                        
                        
                
    def sendLiteral(self,char):
        print('Sending literal \''+str(char)+'\'...')
        self.beBusy(True)
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Lit_'+char,data=''.encode())
        try: # if this takes too long it could cause a 503 error and crash the program
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
            #pass # ignore 503 errors, this too shall pass
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
        self.beBusy(False)

    def enableOrDisableTVItems(self,enableOrDisable): # True for Enable and Show, False for Disable and Hide
        tvItems=[self.lblVolume,self.btnTVVolUp,self.btnTVVolDown,self.lblChannel,self.btnTVChanUp,self.btnTVChanDown,self.lblInput,self.inputs,self.btnRefreshTVInputs,self.btnSwitchTVInput,self.lblTV,self.btnPowerOff,self.btnSleep]
        if enableOrDisable:
            for item in tvItems:
                #print('Enabling '+str(item)+'...')
                item.Enable()
                #print('Showing '+str(item)+'...')
                item.Show()
        else:
            for item in tvItems:
                #print('Disabling '+str(item)+'...')
                item.Disable()
                #print('Hiding '+str(item)+'...')
                item.Hide()

        return True

    def btnDeviceRefresh_Clicked(self,e):
        print('Refresh devices...')
        self.beBusy(True)

        devnames=[]

        # These controls should be disabled if no Rokus have been found on the network. Not hidden though, just disabled.
        dependentControls=[self.btnRefreshCurrentChannel,self.btnRefreshInstalledChannels,self.lbChannelSelector,self.btnSearch,self.btnLaunchChannel,self.btnRemoteBack,self.btnRemoteHome,self.btnRemoteUp,self.btnRemoteDown,self.btnRemoteLeft,self.btnRemoteRight,self.btnRemoteOK,self.btnRemoteReplay,self.btnRemoteVoice,self.btnRemoteInfo,self.btnRemoteReverse,self.btnRemotePlayPause,self.btnRemoteForward,self.btnMacro0,self.btnMacro1,self.btnMacro2,self.btnMacro3]

        alldevs=self.findRokus()
        print('alldevs: '+str(alldevs))
        if not alldevs==[]:
            for c in range(0,len(alldevs)):
                devnames.append(alldevs[c][1])
            print('devnames: '+str(devnames))
            self.cbDevices.Enable()
            self.cbDevices.Clear()
            self.lbChannelSelector.Clear()
            for control in dependentControls:
                control.Enable()
                control.Show()
            self.cbDevices.Set(devnames)
            self.cbDevices.SetSelection(0)
            if len(roku_devices)>0:
                self.btnDeviceApply_Clicked(0)
        else:
            self.disableOnError('Error: No devices found. Check your Internet connection and that devices are set up and accessible.')
        self.beBusy(False)

    def btnDeviceApply_Clicked(self,e):
        print('Apply device...')
        print('Selection: '+str(self.cbDevices.GetSelection()))
        #print('List of rokus at apply: '+str(roku_devices))
        print('Searching for info on '+self.getIPAddress()+'...')

        self.btnRefreshCurrentChannel_Clicked(0)
        self.btnRefreshInstalledChannels_Clicked(0)
        findRemoteSupport=self.checkForFindRemote()
        if findRemoteSupport[0]:
            self.lblFindRemote.Enable()
            self.lblFindRemote.Show()
            self.btnFindRemote.Show()
            if not findRemoteSupport[1]:
                self.btnFindRemote.Disable()
                self.btnFindRemoteTip=wx.ToolTip('Though your device supports FindRemote, your remote does not. Consider upgrading to the Enhanced voice remote to use this feature.')
                self.btnFindRemote.SetToolTip(self.btnFindRemoteTip)
            else:
                self.lblFindRemote.Show()
                self.btnFindRemote.Show()
                self.btnFindRemote.Enable()
                self.btnFindRemoteTip=wx.ToolTip('Ring your remote if having trouble locating it.')
                self.btnFindRemote.SetToolTip(self.btnFindRemoteTip)
                #self.btnFindRemote.SetToolTip(None)
        else:
            self.lblFindRemote.Hide()
            self.btnFindRemote.Hide()
            self.btnFindRemote.Disable()

        if not self.checkForVoiceSearch():
            self.btnRemoteVoice.Disable()
            self.btnRemoteVoice.Hide()
        else:
            self.btnRemoteVoice.Enable()
            self.btnRemoteVoice.Show()

        if self.checkForSearchEnabled():
            self.btnSearch.Enable()
            self.btnSearch.Show()
        else:
            self.btnSearch.Disable()
            self.btnSearch.Hide()

        if self.checkForTV():
            self.refreshTVInputs_Clicked(0)

        tvItems=[self.lblVolume,self.btnTVVolUp,self.btnTVVolDown,self.lblChannel,self.btnTVChanUp,self.btnTVChanDown,self.lblInput,self.inputs,self.btnRefreshTVInputs,self.btnSwitchTVInput,self.lblTV,self.btnPowerOff]
        if self.checkForTV():
            print('This is a TV. Enabling and showing TV controls.')
            self.enableOrDisableTVItems(True)
            #self.btnDChannelInfo.Show()
            #self.btnDChannelInfo.Enable()
            #self.delay(4)
        else:
            print('This is NOT a TV. Disabling and hiding TV controls.')
            self.enableOrDisableTVItems(False)
            #self.btnDChannelInfo.Disable()
            #self.btnDChannelInfo.Hide()

       

        

##        tvItems=[self.lblVolume,self.btnTVVolUp,self.btnTVVolDown,self.lblInput,self.lblTV,self.btnPowerOff]
##        hdmiPorts=[self.btnTVInputHDMI1,self.btnTVInputHDMI2,self.btnTVInputHDMI3,self.btnTVInputHDMI4]
##        channelItems=[self.lblChannel,self.btnTVChanUp,self.btnTVChanDown,self.btnTVInputTuner]
##        myCurrentChans=self.getAllChannels(self.getIPAddress())
##        if self.checkForTV():
##            for item in tvItems:
##                item.Enable()
##                item.Show()
##            for port in range(self.getNumHDMI(self.getIPAddress())): # see how many hdmi ports there are
##                hdmiPorts[port].Enable()
##                hdmiPorts[port].Show()
##            if 'tvinput.dtv' in myCurrentChans: # see if there's a digital tv port
##                for item in channelItems:
##                    item.Enable()
##                    item.Show()
##            if 'tvinput.cvbs' in myCurrentChans: # see if we have a composite video port
##                self.self.btnTVInputAV1.Enable()
##                self.self.btnTVInputAV1.Show()
##        else:
##            for item in tvItems:
##                item.Disable()
##                item.Hide()
##            for port in range(self.getNumHDMI(self.getIPAddress())): # see how many hdmi ports there are
##                hdmiPorts[port].Disable()
##                hdmiPorts[port].Hide()
            
    def btnRefreshCurrentChannel_Clicked(self,e):
        print('Refresh current channel.')
        if self.getCurrentChannelType(self.getIPAddress())=='app':
            self.lblCurrentChannel.SetLabelMarkup('<u>Current channel:</u>\n'+self.getCurrentChannel(self.getIPAddress())[0])
        elif self.getCurrentChannelType(self.getIPAddress())=='home':
            self.lblCurrentChannel.SetLabelMarkup('<u>Current location:</u>\n'+self.getCurrentChannel(self.getIPAddress())[0])
        elif self.getCurrentChannelType(self.getIPAddress())=='app' or self.getCurrentChannelType(self.getIPAddress())=='screensaver':
            self.lblCurrentChannel.SetLabelMarkup('<u>Current screensaver:</u>\n'+self.getCurrentChannel(self.getIPAddress())[0])
        elif self.getCurrentChannelType(self.getIPAddress())=='tvinput':
            self.lblCurrentChannel.SetLabelMarkup('<u>Current input:</u>\n'+self.getCurrentChannel(self.getIPAddress())[0])

        self.getChannelIcon(self.getIPAddress(),self.getCurrentChannel(self.getIPAddress())[1])

    def btnRefreshInstalledChannels_Clicked(self,e):
        print('Refresh channels list...')

        self.lbChannelSelector.Clear()
        self.lbChannelSelector.Append(self.getAllChannels(self.getIPAddress()))
        self.lbChannelSelector.SetSelection(0)

    def btnLaunchChannel_Clicked(self,e):
        print('Launching channel...')
        self.beBusy(True)
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/launch/'+cids[self.lbChannelSelector.GetSelection()],data=''.encode())
        try: # if this takes too long it could cause a 503 error and crash the program
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
            #pass # ignore 503 errors, this too shall pass
        #print('\n\n'+pge+'\n\n')
##        if self.lbChannelSelector.GetSelection()==0: # The store isn't really an app, it's part of the home screen
##            while not self.getCurrentChannel(self.getIPAddress())[0]=='Roku': # account for taking a moment launching, note there is no ID, so go by channel name
##                pass
##        else:
##            while not self.getCurrentChannel(self.getIPAddress())[1]==cids[self.lbChannelSelector.GetSelection()]: # account for apps that take a moment launching
##                pass
        else:
            pge=resp.read().decode()
            
        self.btnRefreshCurrentChannel_Clicked(0)

        self.beBusy(False)
        

    def launchChannelByCID(self,cid):
        print('Launching channel at cid '+str(cid)+'...')
        self.beBusy(True)
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/launch/'+str(cid),data=''.encode())
        try: # if this takes too long it could cause a 503 error and crash the program
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
            #pass # ignore 503 errors, this too shall pass
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            while not self.getCurrentChannel(self.getIPAddress())[1]==str(cid): # account for channels that take a moment launching
                pass
            self.btnRefreshCurrentChannel_Clicked(0)

        self.beBusy(False)

    def tryLaunchChannelByCID(self,cid): # The difference between this and the above is this doesn't wait to see if the channel was launched, it just sort of assumes it was.
        print('Trying to launch channel at cid '+str(cid)+'...')
        self.beBusy(True)
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/launch/'+str(cid),data=''.encode())
        try: # if this takes too long it could cause a 503 error and crash the program
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
            #pass # ignore 503 errors, this too shall pass
        #print('\n\n'+pge+'\n\n')
        else:
            pge=resp.read().decode()
        self.btnRefreshCurrentChannel_Clicked(0) # this might not get executed in time, unfortunately - requiring a manual channel update click from the user

        self.beBusy(False)

    def launchChannelTuner(self,cid):
        self.beBusy(True)
        if not cid=='':
            print('Launching channel from the tuner at cid '+str(cid)+'...')
            req=urllib.request.Request('http://'+self.getIPAddress()+':8060/launch/tvinput.dtv?ch='+str(cid),data=''.encode())
        else:
            print('Launching channel tuner UI...')
            req=urllib.request.Request('http://'+self.getIPAddress()+':8060/launch/tvinput.dtv',data=''.encode())
        self.beBusy(True)
        try: # if this takes too long it could cause a 503 error and crash the program
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
            #pass # ignore 503 errors, this too shall pass
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
        self.btnRefreshCurrentChannel_Clicked(0)

        self.beBusy(False)
        

    def btnRemoteBack_Clicked(self,e):
        print('Remote: Back')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Back',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteHome_Clicked(self,e):
        print('Remote: Home')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Home',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            while not self.getCurrentChannel(self.getIPAddress())[0]=='Roku': # account for the home button to take a moment launching, note there is no ID, so go by channel name
                pass
            self.btnRefreshCurrentChannel_Clicked(0)


    def btnRemoteUp_Clicked(self,e):
        print('Remote: Up')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Up',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            if self.getCurrentChannel(self.getIPAddress())[1]=='tvinput.dtv': # Probably means we're on DTV
                self.btnRefreshCurrentChannel_Clicked(0)
                self.btnRefreshCurrentChannel_Clicked(0)
                self.btnRefreshCurrentChannel_Clicked(0)


    def btnRemoteLeft_Clicked(self,e):
        print('Remote: Left')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Left',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteOK_Clicked(self,e):
        print('Remote: OK')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Select',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteRight_Clicked(self,e):
        print('Remote: Right')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Right',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteDown_Clicked(self,e):
        print('Remote: Down')
            
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Down',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            if self.getCurrentChannel(self.getIPAddress())[1]=='tvinput.dtv': # Probably means we're on DTV
                self.btnRefreshCurrentChannel_Clicked(0)
                self.btnRefreshCurrentChannel_Clicked(0)
                self.btnRefreshCurrentChannel_Clicked(0)

    def btnRemoteReplay_Clicked(self,e):
        print('Remote: Replay')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InstantReplay',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteVoice_Clicked(self,e):
        print('Remote: Voice')

##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Search',data=''.encode())        
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')

        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keydown/Search',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

        self.delay(5)

        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keyup/Search',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
        

        #time.sleep(v_delay)


##        v_delay=5
##        self.timer=wx.Timer(self)
##        self.Bind(wx.EVT_TIMER,self.onTimer)
##        self.timer.StartOnce(v_delay*1000)

        self.btnRefreshCurrentChannel_Clicked(0) # this might not get executed in time, unfortunately - requiring a manual channel update click from the user

##    def onTimer(self,e):
##        print('Time is up!')
##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keyup/Search',data=''.encode())        
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')


    def btnRemoteInfo_Clicked(self,e):
        print('Remote: Info')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Info',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteReverse_Clicked(self,e):
        print('Remote: Reverse')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Rev',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemotePlayPause_Clicked(self,e):
        print('Remote: Play/Pause')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Play',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
        
    def btnRemoteForward_Clicked(self,e):
        print('Remote: Forward')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Fwd',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnRemoteEnter_Clicked(self,e): # I'm still not entirely sure what the Enter key does, but put it here for someone to use in a macro
        print('Remote: Enter')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Enter',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnTVVolDown_Clicked(self,e):
        print('Remote: VolumeDown')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/VolumeDown',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnTVVolUp_Clicked(self,e):
        print('Remote: VolumeUp')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/VolumeUp',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnTVVolMute_Clicked(self,e):
        print('Remote: VolumeMute')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/VolumeMute',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnTVChanUp_Clicked(self,e):
        print('Remote: ChannelUp')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/ChannelUp',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            #self.delay(2) # needs time to update info
            self.btnRefreshCurrentChannel_Clicked(0)
            self.btnRefreshCurrentChannel_Clicked(0)
            self.btnRefreshCurrentChannel_Clicked(0)

    def btnTVChanDown_Clicked(self,e):
        print('Remote: ChannelDown')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/ChannelDown',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            #self.delay(2) # needs time to update info
            self.btnRefreshCurrentChannel_Clicked(0)
            self.btnRefreshCurrentChannel_Clicked(0)
            self.btnRefreshCurrentChannel_Clicked(0)

    def btnTVInputTuner_Clicked(self,e):
        print('Remote: InputTuner')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputTuner',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def btnTVInputHDMI_Clicked(self,e,hdminum):
        print('Remote: InputHDMI'+str(hdminum))
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputHDMI'+str(hdminum),data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            self.btnRefreshCurrentChannel_Clicked(0)

##    def btnTVInputHDMI1_Clicked(self,e):
##        print('Remote: InputHDMI1')
##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputHDMI1',data=''.encode())
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')
##        self.btnRefreshCurrentChannel_Clicked(0)
##
##    def btnTVInputHDMI2_Clicked(self,e):
##        print('Remote: InputHDMI2')
##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputHDMI2',data=''.encode())
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')
##        self.btnRefreshCurrentChannel_Clicked(0)
##
##    def btnTVInputHDMI3_Clicked(self,e):
##        print('Remote: InputHDMI3')
##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputHDMI3',data=''.encode())
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')
##        self.btnRefreshCurrentChannel_Clicked(0)
##
##    def btnTVInputHDMI4_Clicked(self,e):
##        print('Remote: InputHDMI4')
##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputHDMI4',data=''.encode())
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')
##        self.btnRefreshCurrentChannel_Clicked(0)


    def btnTVInputAV_Clicked(self,e,avnum):
        print('Remote: InputAV'+str(avnum))
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputAV'+str(avnum),data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')
            self.btnRefreshCurrentChannel_Clicked(0)
        

##    def btnTVInputAV1_Clicked(self,e):
##        print('Remote: InputAV1')
##        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/InputAV1',data=''.encode())
##        resp=urllib.request.urlopen(req)
##        pge=resp.read().decode()
##        #print('\n\n'+pge+'\n\n')
##        self.btnRefreshCurrentChannel_Clicked(0)

    def btnPowerOff_Clicked(self,e):
        print('Remote: Power Toggle')
        if self.getPowerState(self.getIPAddress())==True: # if on
            req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/PowerOff',data=''.encode())
            try:
                resp=urllib.request.urlopen(req)
            except Exception as e:
                self.disableOnError('Error: '+str(e))
            else:
                pge=resp.read().decode()
                #print('\n\n'+pge+'\n\n')
        else: # if off
            req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/PowerOn',data=''.encode())
            try:
                resp=urllib.request.urlopen(req)
            except Exception as e:
                self.disableOnError('Error: '+str(e))
            else:
                pge=resp.read().decode()
                #print('\n\n'+pge+'\n\n')
        self.btnRefreshCurrentChannel_Clicked(0)

    def btnSleep_Clicked(self,e):
        print('Remote: Sleep')
        req=urllib.request.Request('http://'+self.getIPAddress()+':8060/keypress/Sleep',data=''.encode())
        try:
            resp=urllib.request.urlopen(req)
        except Exception as e:
            self.disableOnError('Error: '+str(e))
        else:
            pge=resp.read().decode()
            #print('\n\n'+pge+'\n\n')

    def onExit(self,e):
        print('Exiting...')
        self.Destroy() # this is how we play

    def onAbout(self,e):
        print('About...')
        msg=wx.MessageDialog(self,message='Hot Shawarma v. 0.02.11.21-alpha\nURL: https://github.com/RomanOnARiver/HotShawarma\nArtwork/Icons: https://www.intentionallyleftblankdesigns.com',caption='About',style=wx.OK|wx.OK_DEFAULT|wx.ICON_INFORMATION)
        msg.ShowModal()

    def createWidgets(self):
        print('Creating widgets...')

        self.Bind(wx.EVT_CLOSE, self.onExit)

        self.filemenu=wx.Menu()
        self.menuExit=self.filemenu.Append(wx.ID_EXIT,'E&xit','Terminate this program.')
        self.Bind(wx.EVT_MENU,self.onExit,self.menuExit)

        self.helpmenu=wx.Menu()
        self.menuAbout=self.helpmenu.Append(wx.ID_ABOUT,'A&bout','About this program.')
        self.Bind(wx.EVT_MENU,self.onAbout,self.menuAbout)
        
        self.menuBar=wx.MenuBar()
        self.menuBar.Append(self.filemenu,'&File')
        self.menuBar.Append(self.helpmenu,'&Help')
        self.SetMenuBar(self.menuBar)

        self.lblDevice=wx.StaticText(self,label='Please select your device:',pos=(15,35),style=wx.ALIGN_LEFT) #30,35 #size: 155 20
        #self.devices=['test device','other test device','third test device']
        self.cbDevices=wx.Choice(self,pos=(225,35),size=(155,35),choices=[]) # 205 # 30
        self.cbDevices.SetSelection(0)
        #self.cbDevices=wx.ComboBox(self,pos=(215,35),size=(155,35),choices=[],style=wx.CB_READONLY) # 205 # 30
        self.Bind(wx.EVT_CHOICE,self.btnDeviceApply_Clicked,self.cbDevices)
        #self.Bind(wx.EVT_COMBOBOX,self.btnDeviceApply_Clicked,self.cbDevices)
        self.cbDevicesTip=wx.ToolTip('List of devices on your network')
        self.cbDevices.SetToolTip(self.cbDevicesTip)

        self.btnDeviceRefresh=wx.Button(self,label='⟳',pos=(385,35),size=(35,25)) # 365 # 30
        self.Bind(wx.EVT_BUTTON,self.btnDeviceRefresh_Clicked,self.btnDeviceRefresh)
        self.btnDeviceTip=wx.ToolTip('Reload the list of devices on your network')
        self.btnDeviceRefresh.SetToolTip(self.btnDeviceTip)

        self.lblFindRemote=wx.StaticText(self,label='',pos=(15,70))
        self.lblFindRemote.SetLabelMarkup('<u>Remote:</u>')

        self.btnFindRemote=wx.Button(self,pos=(15,97),size=(60,30),style=wx.BU_LEFT)
        self.bmpFindRemote=wx.Bitmap('buttons/findremote.png',wx.BITMAP_TYPE_ANY)
        self.btnFindRemote.SetBitmap(self.bmpFindRemote)
        self.Bind(wx.EVT_BUTTON,self.btnFindRemote_Clicked,self.btnFindRemote)
        self.btnFindRemote.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))

        self.lblFindRemote.Disable()
        self.lblFindRemote.Hide()
        self.btnFindRemote.Disable()
        self.btnFindRemote.Hide()

        self.lblVolume=wx.StaticText(self,label='',pos=(85,70))
        self.lblVolume.SetLabelMarkup('<u>Volume:</u>')

        self.btnTVVolUp=wx.Button(self,pos=(85,90),size=(55,30)) # 85 90 55 20
        self.bmpTVVolUp=wx.Bitmap('buttons/volup.png',wx.BITMAP_TYPE_ANY)
        self.btnTVVolUp.SetBitmap(self.bmpTVVolUp)
        self.Bind(wx.EVT_BUTTON,self.btnTVVolUp_Clicked,self.btnTVVolUp)
        self.btnTVVolUp.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnTVVolUpTip=wx.ToolTip('Increase your volume')
        self.btnTVVolUp.SetToolTip(self.btnTVVolUpTip)

        self.btnTVVolDown=wx.Button(self,pos=(85,125),size=(55,30)) # 85 115 55 20
        self.bmpTVVolDown=wx.Bitmap('buttons/voldown.png',wx.BITMAP_TYPE_ANY)
        self.btnTVVolDown.SetBitmap(self.bmpTVVolDown)
        self.Bind(wx.EVT_BUTTON,self.btnTVVolDown_Clicked,self.btnTVVolDown)
        self.btnTVVolDown.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnTVVolDownTip=wx.ToolTip('Decrease your volume')
        self.btnTVVolDown.SetToolTip(self.btnTVVolDownTip)

        self.lblChannel=wx.StaticText(self,label='',pos=(145,70))
        self.lblChannel.SetLabelMarkup('<u>Channel:</u>')

        self.btnTVChanUp=wx.Button(self,label='C+',pos=(145,90),size=(55,30)) # 145 90 55 20
        self.Bind(wx.EVT_BUTTON,self.btnTVChanUp_Clicked,self.btnTVChanUp)
        self.btnTVChanUpTip=wx.ToolTip('Channel up')
        self.btnTVChanUp.SetToolTip(self.btnTVChanUpTip)

        self.btnTVChanDown=wx.Button(self,label='C-',pos=(145,125),size=(55,30)) # 145 115 55 20
        self.Bind(wx.EVT_BUTTON,self.btnTVChanDown_Clicked,self.btnTVChanDown)
        self.btnTVChanDownTip=wx.ToolTip('Channel down')
        self.btnTVChanDown.SetToolTip(self.btnTVChanDownTip)

        self.lblInput=wx.StaticText(self,label='',pos=(265,70))
        self.lblInput.SetLabelMarkup('<u>Input:</u>')

##        self.btnTVInputTuner=wx.Button(self,label='Tuner',pos=(205,90),size=(55,20))
##        self.Bind(wx.EVT_BUTTON,self.btnTVInputTuner_Clicked,self.btnTVInputTuner)
##
##        self.btnTVInputHDMI1=wx.Button(self,label='HDMI1',pos=(265,90),size=(55,20))
##        self.Bind(wx.EVT_BUTTON,self.btnTVInputHDMI1_Clicked,self.btnTVInputHDMI1)
##
##        self.btnTVInputHDMI2=wx.Button(self,label='HDMI2',pos=(325,90),size=(55,20))
##        self.Bind(wx.EVT_BUTTON,self.btnTVInputHDMI2_Clicked,self.btnTVInputHDMI2)
##
##        self.btnTVInputHDMI3=wx.Button(self,label='HDMI3',pos=(205,115),size=(55,20))
##        self.Bind(wx.EVT_BUTTON,self.btnTVInputHDMI3_Clicked,self.btnTVInputHDMI3)
##
##        self.btnTVInputHDMI4=wx.Button(self,label='HDMI4',pos=(265,115),size=(55,20))
##        self.Bind(wx.EVT_BUTTON,self.btnTVInputHDMI4_Clicked,self.btnTVInputHDMI4)
##
##        self.btnTVInputAV1=wx.Button(self,label='AV1',pos=(325,115),size=(55,20))
##        self.Bind(wx.EVT_BUTTON,self.btnTVInputAV1_Clicked,self.btnTVInputAV1)

        self.inputs=wx.ListView(self,pos=(205,90),size=(155,65),style=wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN) # 180
        self.inputs.InsertColumn(0,format=wx.LIST_FORMAT_LEFT,heading='Input', width=55)
        self.inputs.InsertColumn(1,format=wx.LIST_FORMAT_LEFT,heading='Name', width=75) # mac and Windows include vsb in the size, making it bigger would add an hsb, which we don't like

        if wx.GetOsVersion()[0]==wx.OS_UNIX_LINUX: # GNU/Linux is the only one out of the three where the scrollbar is correctly ignored in sizes, let's take advantage of the extra space
            self.inputs.SetColumnWidth(1,width=100)

        self.inputsTip=wx.ToolTip('List of TV inputs')
        self.inputs.SetToolTip(self.inputsTip)

        # Sample inputs:
##        self.inputs.Append(('Tuner','Live TV'))
##        self.inputs.Append(('HDMI1','Cable box'))
##        self.inputs.Append(('HDMI2','Xbox'))
##        self.inputs.Append(('HDMI3','Chromecast'))
##        self.inputs.Append(('HDMI4','ARC'))
##        self.inputs.Append(('AV1','N-64aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')) # why is the n64 screaming and why is there an unnecessary hyphen there

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.switchTVInput_Clicked,self.inputs)

##        self.inputs.SetColumnWidth(0,wx.LIST_AUTOSIZE_USEHEADER)
##        self.inputs.SetColumnWidth(1,wx.LIST_AUTOSIZE_USEHEADER)

##        self.inputs.SetColumnWidth(0,width=60)
##        self.inputs.SetColumnWidth(1,width=70)

        self.btnRefreshTVInputs=wx.Button(self,label='⟳',pos=(245,160),size=(55,20)) # 270
        self.Bind(wx.EVT_BUTTON,self.refreshTVInputs_Clicked,self.btnRefreshTVInputs)
        self.btnRefreshTVInputsTip=wx.ToolTip('Reload a list of TV inputs')
        self.btnRefreshTVInputs.SetToolTip(self.btnRefreshTVInputsTip)

        self.btnSwitchTVInput=wx.Button(self,label='✔',pos=(305,160),size=(55,20)) #330 # ⤮
        self.Bind(wx.EVT_BUTTON,self.switchTVInput_Clicked,self.btnSwitchTVInput)
        self.btnSwitchTVInputTip=wx.ToolTip('Switch TV input')
        self.btnSwitchTVInput.SetToolTip(self.btnSwitchTVInputTip)

        self.lblTV=wx.StaticText(self,label='',pos=(365,70))
        self.lblTV.SetLabelMarkup('<u>TV:</u>')

        self.btnPowerOff=wx.Button(self,pos=(365,90),size=(30,30))
        self.bmpPowerOff=wx.Bitmap('buttons/pwr.png',wx.BITMAP_TYPE_ANY)
        self.btnPowerOff.SetBitmap(self.bmpPowerOff)
        self.Bind(wx.EVT_BUTTON,self.btnPowerOff_Clicked,self.btnPowerOff)
        self.btnPowerOff.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnPowerOffTip=wx.ToolTip('TV: Power')
        self.btnPowerOff.SetToolTip(self.btnPowerOffTip)
        

        self.btnSleep=wx.Button(self,pos=(365,125),size=(30,30))
        self.bmpSleep=wx.Bitmap('buttons/sleep.png',wx.BITMAP_TYPE_ANY)
        self.btnSleep.SetBitmap(self.bmpSleep)
        self.Bind(wx.EVT_BUTTON,self.btnSleep_Clicked,self.btnSleep)
        self.btnSleep.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnSleepTip=wx.ToolTip('TV: Sleep')
        self.btnSleep.SetToolTip(self.btnSleepTip)

        # TODO: Add GameMode button if tv supports it. What does it do? What is it?

        # TODO: What other buttons are there relating to TV specific functions that we don't know about?

        self.bmpCurrentChannel=wx.StaticBitmap(self,wx.ID_ANY,pos=(10,160),size=(145,109))

        #self.lblCurrentDChannel=wx.StaticText(self,label='...',pos=(10,160),size=(200,89),style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.lblCurrentDChannel=wx.TextCtrl(self,pos=(10,160),size=(145,109),style=wx.TE_MULTILINE|wx.TE_READONLY)

        self.lblCurrentDChannel.Disable()
        self.lblCurrentDChannel.Hide()

        self.lblChannelID=wx.StaticText(self,label='',pos=(10,275),size=(145,109),style=wx.ALIGN_RIGHT)

        self.lblCurrentChannel=wx.StaticText(self,label='',pos=(155,200),size=(210,40),style=wx.ALIGN_CENTRE_HORIZONTAL)
        #self.lblCurrentChannel.SetLabelMarkup('<u>Current channel:</u>\nLoading...')
        self.lblCurrentChannel.SetLabelMarkup('<u>Current channel:</u>\n...')

        self.btnRefreshCurrentChannel=wx.Button(self,label='⟳',pos=(365,200),size=(35,30)) # 385
        self.Bind(wx.EVT_BUTTON,self.btnRefreshCurrentChannel_Clicked,self.btnRefreshCurrentChannel)
        self.btnRefreshCurrentChannelTip=wx.ToolTip('Update currently running channel/input in this application')
        self.btnRefreshCurrentChannel.SetToolTip(self.btnRefreshCurrentChannelTip)

        self.lblInstalledChannels=wx.StaticText(self,label='',pos=(10,295))
        self.lblInstalledChannels.SetLabelMarkup('<u>Installed channels:</u>')
        
        self.btnRefreshInstalledChannels=wx.Button(self,label='⟳',pos=(180,295),size=(35,20))
        self.Bind(wx.EVT_BUTTON,self.btnRefreshInstalledChannels_Clicked,self.btnRefreshInstalledChannels)
        self.btnRefreshInstalledChannelsTip=wx.ToolTip('Update list of currently installed channels in this application')
        self.btnRefreshInstalledChannels.SetToolTip(self.btnRefreshInstalledChannelsTip)

        self.lbChannelSelector=wx.ListBox(self,pos=(10,320),size=(205,230),style=wx.LB_SINGLE|wx.LB_NEEDED_SB)
        self.Bind(wx.EVT_LISTBOX_DCLICK,self.btnLaunchChannel_Clicked,self.lbChannelSelector)
        self.lbChannelSelectorTip=wx.ToolTip('List of installed channels')
        self.lbChannelSelector.SetToolTip(self.lbChannelSelectorTip)
        

        self.btnSearch=wx.Button(self,label='\U0001f50d',pos=(10,555),size=(145,25)) #if50d = left, if50e = right
        self.Bind(wx.EVT_BUTTON,self.btnSearch_Clicked,self.btnSearch)
        self.btnSearchTip=wx.ToolTip('Search for content to watch')
        self.btnSearch.SetToolTip(self.btnSearchTip)

        self.btnLaunchChannel=wx.Button(self,label='✔',pos=(160,555),size=(55,25)) #595 #510
        self.Bind(wx.EVT_BUTTON,self.btnLaunchChannel_Clicked,self.btnLaunchChannel)
        self.btnLaunchChannelTip=wx.ToolTip('Launch the selected channel')
        self.btnLaunchChannel.SetToolTip(self.btnLaunchChannelTip)


        self.lblRemote=wx.StaticText(self,label='',pos=(315,245)) # 270
        self.lblRemote.SetLabelMarkup('<u>Remote</u>')

        self.btnRemoteBack=wx.Button(self,pos=(275,285),size=(55,30)) # 230
        self.bmpRemoteBack=wx.Bitmap('buttons/back.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteBack.SetBitmap(self.bmpRemoteBack)
        self.btnRemoteBack.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.Bind(wx.EVT_BUTTON,self.btnRemoteBack_Clicked,self.btnRemoteBack)
        self.btnRemoteBackTip=wx.ToolTip('Remote: Back')
        self.btnRemoteBack.SetToolTip(self.btnRemoteBackTip)

        self.btnRemoteHome=wx.Button(self,pos=(345,285),size=(55,30)) # 300
        self.bmpRemoteHome=wx.Bitmap('buttons/home.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteHome.SetBitmap(self.bmpRemoteHome)
        self.btnRemoteHome.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.Bind(wx.EVT_BUTTON,self.btnRemoteHome_Clicked,self.btnRemoteHome)
        self.btnRemoteHomeTip=wx.ToolTip('Remote: Home')
        self.btnRemoteHome.SetToolTip(self.btnRemoteHomeTip)

        self.btnRemoteUp=wx.Button(self,pos=(320,320),size=(35,30))
        self.bmpRemoteUp=wx.Bitmap('buttons/up.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteUp.SetBitmap(self.bmpRemoteUp)
        self.btnRemoteUp.SetBackgroundColour((102,45,145,wx.ALPHA_OPAQUE))
        self.Bind(wx.EVT_BUTTON,self.btnRemoteUp_Clicked,self.btnRemoteUp)
        self.btnRemoteUpTip=wx.ToolTip('Remote: Up')
        self.btnRemoteUp.SetToolTip(self.btnRemoteUpTip)

        self.btnRemoteLeft=wx.Button(self,pos=(275,360),size=(35,30))
        self.bmpRemoteLeft=wx.Bitmap('buttons/left.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteLeft.SetBitmap(self.bmpRemoteLeft)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteLeft_Clicked,self.btnRemoteLeft)
        self.btnRemoteLeft.SetBackgroundColour((102,45,145,wx.ALPHA_OPAQUE))
        self.btnRemoteLeftTip=wx.ToolTip('Remote: Left')
        self.btnRemoteLeft.SetToolTip(self.btnRemoteLeftTip)

        self.btnRemoteOK=wx.Button(self,pos=(320,360),size=(35,30))
        self.bmpRemoteOK=wx.Bitmap('buttons/ok.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteOK.SetBitmap(self.bmpRemoteOK)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteOK_Clicked,self.btnRemoteOK)
        self.btnRemoteOK.SetBackgroundColour((102,45,145,wx.ALPHA_OPAQUE))
        self.btnRemoteOKTip=wx.ToolTip('Remote: OK')
        self.btnRemoteOK.SetToolTip(self.btnRemoteOKTip)

        self.btnRemoteRight=wx.Button(self,pos=(365,360),size=(35,30))
        self.bmpRemoteRight=wx.Bitmap('buttons/right.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteRight.SetBitmap(self.bmpRemoteRight)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteRight_Clicked,self.btnRemoteRight)
        self.btnRemoteRight.SetBackgroundColour((102,45,145,wx.ALPHA_OPAQUE))
        self.btnRemoteRightTip=wx.ToolTip('Remote: Right')
        self.btnRemoteRight.SetToolTip(self.btnRemoteRightTip)

        self.btnRemoteDown=wx.Button(self,pos=(320,400),size=(35,30))
        self.bmpRemoteDown=wx.Bitmap('buttons/down.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteDown.SetBitmap(self.bmpRemoteDown)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteDown_Clicked,self.btnRemoteDown)
        self.btnRemoteDown.SetBackgroundColour((102,45,145,wx.ALPHA_OPAQUE))
        self.btnRemoteDownTip=wx.ToolTip('Remote: Down')
        self.btnRemoteDown.SetToolTip(self.btnRemoteDownTip)

        self.btnRemoteReplay=wx.Button(self,pos=(275,440),size=(40,30))
        self.bmpRemoteReplay=wx.Bitmap('buttons/replay.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteReplay.SetBitmap(self.bmpRemoteReplay)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteReplay_Clicked,self.btnRemoteReplay)
        self.btnRemoteReplay.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnRemoteReplayTip=wx.ToolTip('Remote: Replay')
        self.btnRemoteReplay.SetToolTip(self.btnRemoteReplayTip)
        

        self.btnRemoteVoice=wx.Button(self,pos=(320,440),size=(40,30)) 
        self.bmpRemoteVoice=wx.Bitmap('buttons/voice.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteVoice.SetBitmap(self.bmpRemoteVoice)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteVoice_Clicked,self.btnRemoteVoice)
        self.btnRemoteVoice.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnRemoteVoiceTip=wx.ToolTip('Remote: Voice Search')
        self.btnRemoteVoice.SetToolTip(self.btnRemoteVoiceTip)

        # TODO: Hide voice button if there's no voice button on the remote

        # TODO: Suspend option for devices that have supports-suspend in device-info as true - button instead of/next to mic???

        self.btnRemoteInfo=wx.Button(self,pos=(365,440),size=(40,30))
        self.bmpRemoteInfo=wx.Bitmap('buttons/info.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteInfo.SetBitmap(self.bmpRemoteInfo)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteInfo_Clicked,self.btnRemoteInfo)
        self.btnRemoteInfo.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnRemoteInfoTip=wx.ToolTip('Remote: Info')
        self.btnRemoteInfo.SetToolTip(self.btnRemoteInfoTip)

        self.btnRemoteReverse=wx.Button(self,pos=(275,475),size=(30,30))
        self.bmpRemoteReverse=wx.Bitmap('buttons/reverse.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteReverse.SetBitmap(self.bmpRemoteReverse)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteReverse_Clicked,self.btnRemoteReverse)
        self.btnRemoteReverse.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnRemoteReverseTip=wx.ToolTip('Remote: Reverse')
        self.btnRemoteReverse.SetToolTip(self.btnRemoteReverseTip)         

        self.btnRemotePlayPause=wx.Button(self,pos=(310,475),size=(60,30))
        self.bmpRemotePlayPause=wx.Bitmap('buttons/playpause.png',wx.BITMAP_TYPE_ANY)
        self.btnRemotePlayPause.SetBitmap(self.bmpRemotePlayPause)
        self.Bind(wx.EVT_BUTTON,self.btnRemotePlayPause_Clicked,self.btnRemotePlayPause)
        self.btnRemotePlayPause.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnRemotePlayPauseTip=wx.ToolTip('Remote: Play/Pause')
        self.btnRemotePlayPause.SetToolTip(self.btnRemotePlayPauseTip)    

        self.btnRemoteForward=wx.Button(self,pos=(375,475),size=(30,30))
        self.bmpRemoteForward=wx.Bitmap('buttons/forward.png',wx.BITMAP_TYPE_ANY)
        self.btnRemoteForward.SetBitmap(self.bmpRemoteForward)
        self.Bind(wx.EVT_BUTTON,self.btnRemoteForward_Clicked,self.btnRemoteForward)
        if wx.GetOsVersion()[0]==wx.OS_WINDOWS_NT:
            self.btnRemoteForward.SetFont(wx.Font(70,wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False,'Segoe UI Symbol',wx.FONTENCODING_DEFAULT))
        self.btnRemoteForward.SetBackgroundColour((0,0,0,wx.ALPHA_OPAQUE))
        self.btnRemoteForwardTip=wx.ToolTip('Remote: Forward')
        self.btnRemoteForward.SetToolTip(self.btnRemoteForwardTip)    

        # TODO: A and B buttons ???

        #self.btnSearch=wx.Button(self,label='\U0001f50d',pos=(225,490),size=(180,15))

        self.btnMacro0=wx.Button(self,label='(none set)',pos=(225,510),size=(90,30)) # 210
        self.Bind(wx.EVT_BUTTON,self.btnMacro0_Clicked,self.btnMacro0)
        self.btnMacro0Tip=wx.ToolTip('Macro 0')
        self.btnMacro0.SetToolTip(self.btnMacro0Tip)    

        self.btnMacro1=wx.Button(self,label='(none set)',pos=(325,510),size=(90,30)) # 310
        self.Bind(wx.EVT_BUTTON,self.btnMacro1_Clicked,self.btnMacro1)
        self.btnMacro1Tip=wx.ToolTip('Macro 1')
        self.btnMacro1.SetToolTip(self.btnMacro1Tip)

        self.btnMacro2=wx.Button(self,label='(none set)',pos=(225,550),size=(90,30))
        self.Bind(wx.EVT_BUTTON,self.btnMacro2_Clicked,self.btnMacro2)
        self.btnMacro2Tip=wx.ToolTip('Macro 2')
        self.btnMacro2.SetToolTip(self.btnMacro2Tip)

        self.btnMacro3=wx.Button(self,label='(none set)',pos=(325,550),size=(90,30))
        self.Bind(wx.EVT_BUTTON,self.btnMacro3_Clicked,self.btnMacro3)
        self.btnMacro3Tip=wx.ToolTip('Macro 3')
        self.btnMacro3.SetToolTip(self.btnMacro3Tip)


        try:
            os.makedirs(datadir)
            print('Directory '+datadir+' created.')
        except FileExistsError:
            print('Directory '+datadir+' already exists.')


        saveFileParser.read(datadir+'/macros.ini')

        if len(saveFileParser.sections())==0: # TODO: If section is wrong delete everything and start over
            print('No sections yet. We need to set up the template.')
            saveFileParser['macros']={'macro0name':'','macro0macro':'','macro1name':'','macro1macro':'','macro2name':'','macro2macro':'','macro3name':'','macro3macro':''}
            with open(datadir+'/macros.ini','w') as configfile:
                saveFileParser.write(configfile)
            
        else: # TODO: If entries are invalid set them to '' or consider just deleting everything and start over
            print('We have a section, so we need to load.')
            for c in range(0,4):
                for d in range(0,2):
                    if not str(saveFileParser['macros']['macro'+str(c)+'name']) =='':
                        macros[c][0]=str(saveFileParser['macros']['macro'+str(c)+'name'])
                        
                    if not str(saveFileParser['macros']['macro'+str(c)+'macro']) =='':
                        macros[c][1]=str(saveFileParser['macros']['macro'+str(c)+'macro'])

        print('Final list of macros loaded: '+str(macros))

        if not macros[0][0]=='':
            self.btnMacro0.SetLabel(macros[0][0])
        if not macros[1][0]=='':
            self.btnMacro1.SetLabel(macros[1][0])
        if not macros[2][0]=='':
            self.btnMacro2.SetLabel(macros[2][0])
        if not macros[3][0]=='':
            self.btnMacro3.SetLabel(macros[3][0])


##        tvItems=[self.lblFindRemote,self.btnFindRemote,self.lblVolume,self.btnTVVolUp,self.btnTVVolDown,self.lblChannel,self.btnTVChanUp,self.btnTVChanDown,self.lblInput,self.btnTVInputTuner,self.btnTVInputHDMI1,self.btnTVInputHDMI2,self.btnTVInputHDMI3,self.btnTVInputHDMI4,self.btnTVInputAV1,self.lblTV,self.btnPowerOff]
##        for item in tvItems:
##            item.Disable()
##            item.Hide()


        self.enableOrDisableTVItems(False)

        self.Show(True)

        self.btnDeviceRefresh_Clicked(0)
        if len(roku_devices)>0:
            self.btnDeviceApply_Clicked(0)
            
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(440,650),style=wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN) # 445 690
        self.createWidgets()

app = wx.App(False)
frame = MainWindow(None, 'Hot Shawarma').SetIcon(wx.Icon('S_Matty3.xpm'))
app.MainLoop()
