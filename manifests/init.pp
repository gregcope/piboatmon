class piboatmon {

  include piboatmon::python
  include piboatmon::gps
#  include piboatmon::ntp
  include piboatmon::3g
  include piboatmon::mopi
  include piboatmon::fasterboot
  include piboatmon::removepackages
  include piboatmon::logrotate
  include piboatmon::puppet
  include piboatmon::piboatmon
  include piboatmon::readonlyboot
  include piboatmon::overclock
}

# to run but do nothing
# sudo puppet apply init.pp --modulepath=/tmp
# and to run doing stuff
# sudo puppet apply init.pp --modulepath=/home/pi --noop
include piboatmon
