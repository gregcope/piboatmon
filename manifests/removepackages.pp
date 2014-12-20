# class to make a piboatmon boot faster
class piboatmon::removepackages {

  # remove a load of guff
  # http://www.raspberrypi.org/forums/viewtopic.php?f=29&t=25777
  package { 'libgtk-3-common': ensure => 'purged' }
  package { 'xkb-data': ensure => 'purged' }
  package { 'lxde-icon-theme': ensure => 'purged' }
  package { 'raspberrypi-artwork': ensure => 'purged' }
  package { 'penguinspuzzle': ensure => 'purged' }
  # https://projects.drogon.net/raspberry-pi/initial-setup2/
  package { 'xinetd': ensure => 'purged' }
  package { 'portmap': ensure => 'purged' }
  package { 'fuse-utils': ensure => 'purged' }
  package { 'libfuse2': ensure => 'purged' }
  package { 'libntfs10': ensure => 'purged' }
  package { 'gdm': ensure => 'purged' }
  # mine from  dpkg --get-selections | more
  package { 'rsync': ensure => 'purged' }
  package { 'alsa-base': ensure => 'purged' }
  package { 'alsa-utils': ensure => 'purged' }
  package { 'cups-bsd': ensure => 'purged' }
  package { 'cups-client': ensure => 'purged' }
  package { 'cups-common': ensure => 'purged' }
  package { 'libflac8': ensure => 'purged' }
  # http://blog.pedrocarrico.net/post/90383758203/strip-down-raspbian-to-a-bare-minimum
  package { 'samba-common': ensure => 'purged' }
  package { 'desktop-base': ensure => 'purged' }
  package { 'lightdm': ensure => 'purged' }
  package { 'lxappearance': ensure => 'purged' }
  package { 'lxde-common': ensure => 'purged' }
  package { 'lxinput': ensure => 'purged' }
  package { 'lxpanel': ensure => 'purged' }
  package { 'lxpolkit': ensure => 'purged' }
  package { 'lxrandr': ensure => 'purged' }
  package { 'lxsession-edit': ensure => 'purged' }
  package { 'lxshortcut': ensure => 'purged' }
  package { 'lxtask': ensure => 'purged' }
  package { 'lxterminal': ensure => 'purged' }
  package { 'wolfram-engine': ensure => 'purged' }
  package { 'obconf': ensure => 'purged' }
  package { 'openbox': ensure => 'purged' }
  package { 'xarchiver': ensure => 'purged' }
  package { 'xinit': ensure => 'purged' }
  package { 'xserver-xorg': ensure => 'purged' }
  package { 'xserver-xorg-video-fbdev': ensure => 'purged' }
  package { 'x11-utils': ensure => 'purged' }
  package { 'x11-common': ensure => 'purged' }
  package { 'x11-session utils': ensure => 'purged' }
  package { 'triggerhappy': ensure => 'purged' }
}
