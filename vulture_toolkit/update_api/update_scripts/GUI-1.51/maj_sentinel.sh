#!/bin/sh
#
# This migration script update /usr/local/etc/rc.d/sentinel
#
#

script_filename="/usr/local/etc/rc.d/sentinel"

/bin/echo -n "[+] Updating file $script_filename ..."

/bin/echo "#!/bin/sh
#
# \$FreeBSD: head/databases/redis/files/redis.in 385499 2015-05-06 01:24:13Z osa \$
#

# PROVIDE: redis-sentinel
# REQUIRE: redis
# BEFORE:  securelevel
# KEYWORD: shutdown

# Add the following line to /etc/rc.conf to enable sentinel:
#
#sentinel_enable=\"YES\"
#

. /etc/rc.subr

name=\"sentinel\"
rcvar=\"\${name}_enable\"

start_cmd=\"sentinel_start\"
stop_cmd=\"sentinel_stop\"
pidfile=\"/var/run/redis/\$name.pid\"

load_rc_config \$name

sentinel_start()
{
    if checkyesno \${rcvar}; then
    {
        if [ ! -f /var/bootstrap/.first_start ]; then
        {
            sleep 1
            /usr/local/bin/redis-sentinel /usr/local/etc/sentinel.conf
            sleep 2
            /usr/local/bin/redis-cli -p 26379 SENTINEL FAILOVER mymaster
        }
        fi
    }
    fi
}

sentinel_stop()
{
    if checkyesno \${rcvar}; then
    {
        if [ -f \$pidfile ]; then
        {
            # Kill processus
            /bin/kill \$(/bin/cat \$pidfile)
            # Empty pid file
            /bin/cat /dev/null > \$pidfile
        }
        fi
    }
    fi
}

run_rc_command \"\$1\"
" > "$script_filename"

/bin/echo "OK"
