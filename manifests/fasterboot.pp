# class to make a rpi boot faster
class rpi::fasterboot {

  # remove a load of guff
  # http://www.raspberrypi.org/forums/viewtopic.php?f=29&t=25777
  package { 'libfreetype6': ensure => 'absent' }
  package { 'libx11-6': ensure => 'absent' }
  package { 'libgtk-3-common': ensure => 'absent' }
  package { 'xkb-data': ensure => 'absent' }
  package { 'lxde-icon-theme': ensure => 'absent' }
  package { 'raspberrypi-artwork': ensure => 'absent' }
  package { 'penguinspuzzle': ensure => 'absent' }
  # https://projects.drogon.net/raspberry-pi/initial-setup2/
  package { 'xinetd': ensure => 'absent' }
  package { 'portmap': ensure => 'absent' }
  package { 'fuse-utils': ensure => 'absent' }
  package { 'libfuse2': ensure => 'absent' }
  package { 'libntfs10': ensure => 'absent' }
  package { 'gdm': ensure => 'absent' }
  # mine from  dpkg --get-selections | more
  package { 'rsync': ensure => 'absent' }
  package { 'alsa-base': ensure => 'absent' }
  package { 'alsa-utils': ensure => 'absent' }
  package { 'cups-bsd': ensure => 'absent' }
  package { 'cups-client': ensure => 'absent' }
  package { 'cups-common': ensure => 'absent' }
  # http://blog.pedrocarrico.net/post/90383758203/strip-down-raspbian-to-a-bare-minimum
  package { 'samba-common': ensure => 'absent' }
  package { 'desktop-base': ensure => 'absent' }
  package { 'lightdm': ensure => 'absent' }
  package { 'lxappearance': ensure => 'absent' }
  package { 'lxde-common': ensure => 'absent' }
  package { 'lxde-icon-theme': ensure => 'absent' }
  package { 'lxinput': ensure => 'absent' }
  package { 'lxpanel': ensure => 'absent' }
  package { 'lxpolkit': ensure => 'absent' }
  package { 'lxrandr': ensure => 'absent' }
  package { 'lxsession-edit': ensure => 'absent' }
  package { 'lxshortcut': ensure => 'absent' }
  package { 'lxtask': ensure => 'absent' }
  package { 'lxterminal': ensure => 'absent' }
  package { 'wolfram-engine': ensure => 'absent' }
  package { 'obconf': ensure => 'absent' }
  package { 'openbox': ensure => 'absent' }
  package { 'raspberrypi-artwork': ensure => 'absent' }
  package { 'xarchiver': ensure => 'absent' }
  package { 'xinit': ensure => 'absent' }
  package { 'xserver-xorg': ensure => 'absent' }
  package { 'xserver-xorg-video-fbdev': ensure => 'absent' }
  package { 'x11-utils': ensure => 'absent' }
  package { 'x11-common': ensure => 'absent' }
  package { 'x11-session utils': ensure => 'absent' }

  # disable swap at boot
  # http://www.element14.com/community/thread/21377/l/how-do-i-permanently-disable-the-swap-service
#  exec { 'stopdphys-swapfile':
#    logoutput => true,
#    command => '/usr/sbin/update-rc.d -f dphys-swapfile remove',
#    onlyif => '/bin/ls -la /etc/rc2.d/S02dphys-swapfile',
#  }

  #squashfs?

  # mount / with options to reduce writes
  # http://raspberrypi.stackexchange.com/questions/335/is-there-anything-i-can-do-to-improve-boot-speed
#  mount { '/':
#    ensure => present,
#    atboot => yes,
#    fstype => ext4,
#    dump => 0,
#    pass => 1,
#    options => 'defaults,noatime,nodiratime,errors=remount-ro,data=writeback'
#  }

  # remove used getty's
  # https://extremeshok.com/1081/raspberry-pi-raspbian-tuning-optimising-optimizing-for-reduced-memory-usage/
#  exec { 'removeGettys':
#    logoutput => true,
#    command => '/bin/sed -i "/[2-6]:23:respawn:\/sbin\/getty 38400 tty[2-6]/s%^%#%g" /etc/inittab',
#    unless => '/bin/grep "#[2-6]:23:respawn:\/sbin\/getty 38400 tty[2-6]" /etc/inittab'
#  }
}
