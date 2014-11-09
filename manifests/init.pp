#
#
# Think I need to run;
# usb_modeswitch -c /etc/usb_modeswitch.conf
# http://debbox.dk/sending-sms-from-huawei-e1752/
#
#

#
# huawei e1752cu
# 
# install usb-modeswitch
# which basically sets some udev rules
package { 'usb-modeswitch': }

file { '/etc/usb_modeswitch.d/e1752cu.conf':
  ensure => 'present',
  content => "DefaultVendor= 0×12d1\nDefaultProduct= 0×1446\nTargetVendor= 0×12d1\nTargetProdct= 0×1001\nMessageEndpoint= 0×01\nMessageContent= \"55534243000000000000000000000011060000000000000000000000000000\""
}

# install gnokii so that we can send sms'es
package { 'gnokii': }

# configure gnokii
file { ' /etc/gnokiirc':
   ensure => 'present',
   content => "[global]\nmodel = AT\nport = /dev/gsmmodem\nconnection = serial\n",
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

