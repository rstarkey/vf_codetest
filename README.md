Write a "vf_start" tool to start the services of a Veriflow system
specified in the procs.cfg file given below.  The tool takes the
configuration file as an input parameter.  Its usage is:

% vf_start [-h] [-s] [-c <config-file>]

where:
  -h   prints the help menu
  -s   sort the output by service name
  -c   specifies the config file

The tool spawns the processes for the services, in their required
count and startup order, and then exits.  It prints out the list of
process IDs (PIDs) for the services using this format, one service
per line:

<name>:<comma-separated-list-of-PIDs>

By default (i.e. without the "-s" option) the output is sorted by the
startup order of the services.  If "-s" is given, the output is sorted
by the service name.

Below is an example configuration file and description of its fields.

~~~
#===================== procs.cfg =====================
# The list of application services to run.
#
# Each service is configured with these parameters:
# * name:   the name of the service (mandatory)
# * cmd:    the command line to run (mandatory)
# * count:  the number of instances to start (optional, default 1)
# * order:  the startup order -- lower numbers are started before higher
#           number; same numbers can start in any order among themselves
#           (optional, default 0)
# * stdin:  the filename to use as the "stdin" of each process (optional,
#           default /dev/null)
# * stdout: the filename to use as the "stdout" of each process (optional,
#           default /dev/null)
# * stderr: the filename to use as the "stderr" of each process (optional,
#           default /dev/null)
#
# The syntax is one service per line:
# <name>:<count>:<order>:<stdin>:<stdout>:<stderr>:<cmd>

parser:1:3::/tmp/vf_parser.out:/tmp/vf_parser.err:/bin/echo -n hello world
modeler::5:/etc/passwd:/tmp/vf_mod.out::/bin/wc -l
brain:3:::/tmp/vf_nn.out::/bin/bash -c "echo `date` : $$"
db::100:::/tmp/vf_db.err:/bin/cat /tmp/missing_file
cache:1:2::/tmp/vf_cache.out:/tmp/vf_cache.err:/bin/cat /tmp/missing_file
#===================== procs.cfg =====================
~~~