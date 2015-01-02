# class to install 3G dongle bits

class piboatmon::3g {

# install packages
  package { 'usb-modeswitch': }
  package { 'ppp': }
  package { 'wvdial': }
  package { 'gammu': }
  package { 'python-gammu': }
  package { 'minicom': }

# config gammu
# only if installed
# to test
# echo "fooo" | gammu sendsms TEXT +441234567890
# should see
# If you want break, press Ctrl+C...
# Sending SMS 1/1....waiting for network answer..OK, message reference=4
  file { '/home/pi/.gammurc':
    ensure => 'present',
    owner => pi,
    group => pi,
    content => "[gammu]\n\nport = /dev/ttyUSB0\nmodel = \nconnection = at19200\nsynchronizetime = yes\nlogfile = \nlogformat = nothing\nuse_locking = \ngammuloc = \n",
    require => Package [ 'gammu' ],
  }

# config usb switch for Huaewei
#  file { '/etc/usb_modeswitch.conf':
#    ensure => 'present',
#    content => "EnableLogging=1\nDefaultVendor= 0×12d1\nDefaultProduct= 0×1446\nTargetVendor= 0×12d1\nTargetProduct= 0×1436\nMessageEndpoint= 0×01\nMessageContent= \"55534243000000000000000000000011060000000000000000000000000000\"",
#    require => Package [ 'usb-modeswitch' ],
#  }

# config wvdial
# only if installed
  file { '/etc/wvdial.conf':
    ensure => 'present',
    content => "[Dialer giffgaff]\nInit3 = AT+CGDCONT=1,\"IP\",\"giffgaff.com\"\nUsername = giffgaff\nPassword = password\n\n[Dialer Defaults]\nModem = /dev/ttyUSB0\nInit1 = ATZ\nInit2 = ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0\nCarrier Check = no\nStupid Mode = 1\nModem Type = Analog Modem\nPhone = *99#\nISDN = 0\nBaud = 460800\n",
    require => Package [ 'wvdial' ],
  }

# config pppd
# only if installed
  exec { 'configPppOptions':
    logoutput => true,
    command => '/bin/echo -e "defaultroute\nreplacedefaultroute" >> /etc/ppp/options',
    unless => '/bin/egrep "defaultroute|replacedefaultroute" /etc/ppp/options',
    require => Package [ 'ppp' ],
  }
}

# Think I need to run;
# usb_modeswitch -c /etc/usb_modeswitch.conf
# http://debbox.dk/sending-sms-from-huawei-e1752/
#
# minial pi installed
# http://www.cnx-software.com/2012/07/31/84-mb-minimal-raspbian-armhf-image-for-raspberry-pi/
# 
# lots of links about 3G pi router
# http://techmind.org/rpi/ 
#
# or
# http://ubuntuforums.org/showthread.php?t=1996734&p=12000198#post12000198

# gammu?
# http://www.mattiasnorell.com/send-sms-from-a-raspberry-pi/
# http://wammu.eu/phones/huawei/4062/

# http://myraspberryandme.wordpress.com/2013/09/13/short-message-texting-sms-with-huawei-e220/

# gnokki? looks simple ...
# http://debbox.dk/sending-sms-from-huawei-e1752/
#

