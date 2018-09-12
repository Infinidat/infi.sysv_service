Introduction
============

This package allows controlling Linux services.

There are three common init systems in use by Linux distributions, each
offering its own way to manage system services.
* "System V" (pronounced "system five") is the older init system.
Its service configuration files ("init scripts") are in `/etc/init.d` and
services are controlled with the `service` command.
* Upstart is a newer init system. Its service configuration files are in
`/etc/init` and services are controlled by commands such as `start <service>`,
`stop <service>`, etc. Normally, distributions that use Upstart as the init
system also support managing services using the System V service configuration
and commands.
* systemd offers an even newer init system. Its service configuration files
are in several locations such as `/usr/lib/systemd/system` and services are
controlled by the `systemctl` command.

This package supports controlling services with either System V commands or
systemd commands.

Supported operating systems:

* Ubuntu
* RedHat based distributions such as RHEL, CentOS, and Oracle Linux
* SUSE based distributions such as SLES or SLED

Usage
=====
Depending on the operating system distribution and version, instantiate
the correct class:

* Ubuntu version<15.04 - `UbuntuInitService`
* SUSE version<12 - `SuseInitService`
* RedHat version<7 - `RedHatInitService`
* Ubuntu version>=15.04 - `SystemdService`
* SUSE version>=12 - `SystemdService`
* RedHat version>=7 - `SystemdService`

Pass the service name and the name of the process the service is expected
to use, for example:

    sysv_service = UbuntuInitService('multipath-tools', 'multipathd')

The classes provide the following methods:

* `is_running`
* `start`
* `force_start`
* `stop`
* `is_auto_start`
* `set_auto_start`

Checking out the code
=====================

To run this code from the repository for development purposes, run the following:

    easy_install -U infi.projector
    projector devenv build
