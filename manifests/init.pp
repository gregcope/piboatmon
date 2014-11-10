#
#
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
# huawei e1752cu
# 
# install usb-modeswitch
# which basically sets some udev rules
package { 'usb-modeswitch': }

file { '/etc/usb_modeswitch.conf':
  ensure => 'present',
  content => "DefaultVendor= 0×12d1\nDefaultProduct= 0×1446\nTargetVendor= 0×12d1\nTargetProdct= 0×1001\nMessageEndpoint= 0×01\nMessageContent= \"55534243000000000000000000000011060000000000000000000000000000\"",
  require => Package [ 'usb-modeswitch' ],
}

# install gnokii so that we can send sms'es
package { 'gnokii': }

# configure gnokii
file { '/etc/gnokiirc':
   ensure => 'present',
   content => "[global]\nmodel = AT\nport = /dev/gsmmodem\nconnection = serial\n",
   require => Package [ 'gnokii' ],
}

# or
# http://ubuntuforums.org/showthread.php?t=1996734&p=12000198#post12000198

# gammu?
# http://www.mattiasnorell.com/send-sms-from-a-raspberry-pi/
# http://wammu.eu/phones/huawei/4062/

# http://myraspberryandme.wordpress.com/2013/09/13/short-message-texting-sms-with-huawei-e220/

# gnokki? looks simple ...
# http://debbox.dk/sending-sms-from-huawei-e1752/
#






# http://www.stroobant.be/huawei-e1752-mobiel-internet-op-linux-ubuntudebian

# Chose one of;
# DetachStorageOnly=1
# HuaweiMode=1

# DefaultVendor=  0x12d1
# DefaultProduct= 0x1001
 

# TargetClass=    0xff

# choose one of these:
# DetachStorageOnly=1
# HuaweiMode=1


#TargetProductList="1001,1406,140b,140c,1412,141b,14ac"
# add 1436?
# https://help.ubuntu.com/community/3GInternet

# http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=561&sid=b1fc4ab2946571296dc2042a4630ef21

# /usr/sbin/usb_modeswitch -I -W -c /etc/usb_modeswitch.d/12d1:1446
