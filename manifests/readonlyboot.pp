# make root readonly
# from:
# http://blog.gegg.us/2014/03/a-raspbian-read-only-root-fs-howto/

class piboatmon::readonlyboot {

  service { 'bootlogs':
    ensure => stopped,
    enable => false,
  }

  service { 'sudo':
    ensure => stopped,
    enable => false,
  }

  service { 'console-setup':
    ensure => stopped,
    enable => false,
  }

  service { 'fake-hwclock':
    ensure => stopped,
    enable => false,
  }

  exec { 'removedoStartCheckRootSh':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s/do_start$/#do_start/" /etc/init.d/checkroot.sh',
    unless => '/bin/grep "#do_start$" /etc/init.d/checkroot.sh',
  }

  exec { 'removedoStartCheckFsSh':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s/do_start$/#do_start/" /etc/init.d/checkfs.sh',
    unless => '/bin/grep "#do_start$" /etc/init.d/checkfs.sh',
  }

  exec { 'removecleanAllCheckRootBootCleanSh':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s/clean_all/#clean_all/" /etc/init.d/checkroot-bootclean.sh',
    unless => '/bin/grep "#clean_all" /etc/init.d/checkroot-bootclean.sh',
  }

  exec { 'removeCleanCheckRootBootCleanSh':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s?rm -f /tmp/.clean /lib/init/rw/.clean /run/.clean /run/lock/.clean?#rm -f /tmp/.clean /lib/init/rw/.clean /run/.clean /run/lock/.clean?" /etc/init.d/checkroot-bootclean.sh',
    unless => '/bin/grep "#rm -f /tmp/.clean /lib/init/rw/.clean /run/.clean /run/lock/.clean" /etc/init.d/checkroot-bootclean.sh',
  }

#  mount { '/':
#    ensure => present,
#    device => '/dev/mmcblk0p2',
#    atboot => yes,
#    fstype => ext4,
#    dump => 0,
#    pass => 1,
#    options => 'defaults,ro'
#  }

  mount { '/boot':
    ensure => present,
    device => '/dev/mmcblk0p1',
    atboot => yes,
    fstype => vfat,
    dump => 0,
    pass => 2,
    options => 'defaults,ro'
  }

  file { '/var/lib/dhcp':
    ensure => 'link',
    target => '/tmp/dhcp',
  }

#  exec { 'addRoToBootCmdline':
#    logoutput => true,
#    command => '/usr/bin/perl -p -i -e "s/elevator=deadline/elevator=deadline ro/" /boot/cmdline.txt',
#    unless => '/bin/grep "elevator=deadline ro" /boot/cmdline.txt',
#  }

}
