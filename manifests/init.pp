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

file { '/etc/usb-modeswitch.conf':
  ensure => 'present',
  content => "DefaultVendor= 0×12d1\nDefaultProduct= 0×1446\nTargetVendor= 0×12d1\nTargetProduct= 0×1001\nMessageEndpoint= 0×01\nMessageContent= \"55534243000000000000000000000011060000000000000000000000000000\"",
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

