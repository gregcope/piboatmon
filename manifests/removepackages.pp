# class to make a rpi boot faster
class rpi::removepackages {

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
  package { 'libflac8': ensure => 'absent' }
  # http://blog.pedrocarrico.net/post/90383758203/strip-down-raspbian-to-a-bare-minimum
  package { 'samba-common': ensure => 'absent' }
  package { 'desktop-base': ensure => 'absent' }
  package { 'lightdm': ensure => 'absent' }
  package { 'lxappearance': ensure => 'absent' }
  package { 'lxde-common': ensure => 'absent' }
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
  package { 'xarchiver': ensure => 'absent' }
  package { 'xinit': ensure => 'absent' }
  package { 'xserver-xorg': ensure => 'absent' }
  package { 'xserver-xorg-video-fbdev': ensure => 'absent' }
  package { 'x11-utils': ensure => 'absent' }
  package { 'x11-common': ensure => 'absent' }
  package { 'x11-session utils': ensure => 'absent' }
}
