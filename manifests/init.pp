class rpi {

  include rpi::python
  include rpi::gps
  include rpi::ntp
  include rpi::3g
  include rpi::mopi
  include rpi::fasterboot
  include rpi::removepackages
  include rpi::boatmon
}

# to run but do nothing
# sudo puppet apply init.pp --modulepath=/home/pi
# and to run doing stuff
# sudo puppet apply init.pp --modulepath=/home/pi --noop
include rpi
