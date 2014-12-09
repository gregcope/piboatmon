# class to make a piboatmon boot faster
class piboatmon::fasterboot {

  # disable swap at boot
  # http://www.element14.com/community/thread/21377/l/how-do-i-permanently-disable-the-swap-service
  exec { 'stopdphys-swapfile':
    logoutput => true,
    command => '/usr/sbin/update-rc.d -f dphys-swapfile remove',
    onlyif => '/bin/ls -la /etc/rc2.d/S02dphys-swapfile',
  }

  #squashfs?

  # mount / with options to reduce writes
  # http://raspberrypi.stackexchange.com/questions/335/is-there-anything-i-can-do-to-improve-boot-speed
  mount { '/':
    ensure => present,
    atboot => yes,
    fstype => ext4,
    dump => 0,
    pass => 1,
    options => 'defaults,noatime,nodiratime'
  }

  # remove used getty's
  # https://extremeshok.com/1081/raspberry-pi-raspbian-tuning-optimising-optimizing-for-reduced-memory-usage/
  exec { 'removeGettys':
    logoutput => true,
    command => '/bin/sed -i "/[2-6]:23:respawn:\/sbin\/getty 38400 tty[2-6]/s%^%#%g" /etc/inittab',
    unless => '/bin/grep "#[2-6]:23:respawn:\/sbin\/getty 38400 tty[2-6]" /etc/inittab'
  }
}
