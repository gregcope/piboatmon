# class to install python bits
class rpi::python {

  # install some packages we will need
  package { 'python-rpi.gpio': ensure => installed }
  package { 'python3-rpi.gpio': ensure => installed }

}
