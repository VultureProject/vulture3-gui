#!/bin/sh
#
# This migration script install newest Vulture-LIBS package
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

cd /tmp

#Add mapping to required library
/bin/echo "
libgcc_s.so.1       vulture/libgcc_s.so.1
libquadmath.so.0    vulture/libquadmath.so.0
libgfortran.so.3    vulture/libgfortran.so.3
liblapack.so.4      vulture/liblapack.so.4
libblas.so.2        vulture/libblas.so.2
libopenblas.so.0    vulture/libopenblas.so.0
libopenblasp.so.0   vulture/libopenblasp.so.0
" > /etc/libmap.conf

#Remove compilators from vulture
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg remove gcc48 2> /dev/null
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg remove gcc49 2> /dev/null
/usr/bin/env ASSUME_ALWAYS_YES=YES pkg remove nghttp2 2> /dev/null


/bin/echo "[+] Updating Vulture-LIBS..."

/bin/rm -f /tmp/Vulture-LIBS.tar.gz
/bin/rm -f /tmp/Vulture-LIBS-11.tar.gz

version=$(freebsd-version | grep -c 11)

if [ $version -eq 1 ]; then
    /usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/11.0/Vulture-LIBS.tar.gz >>/tmp/installation.log 2>&1
    cd /home/vlt-gui
    /usr/bin/tar xf /tmp/Vulture-LIBS.tar.gz
    /usr/sbin/chown -R vlt-gui:vlt-gui /home/vlt-gui/

    /bin/mkdir -p /usr/local/lib/vulture
    /bin/ln -s /home/vlt-gui/lib-11.0/libgcc_s.so.1 /usr/local/lib/vulture/libgcc_s.so.1
    /bin/ln -s /home/vlt-gui/lib-11.0/libgfortran.so.3 /usr/local/lib/vulture/libgfortran.so.3
    /bin/ln -s /home/vlt-gui/lib-11.0/libquadmath.so.0 /usr/local/lib/vulture/libquadmath.so.0
    /bin/ln -s /home/vlt-gui/lib-11.0/liblapack.so.4 /usr/local/lib/vulture/liblapack.so.4
    /bin/ln -s /home/vlt-gui/lib-11.0/libblas.so.2 /usr/local/lib/vulture/libblas.so.2
    /bin/ln -s /home/vlt-gui/lib-11.0/libopenblas.so.0  /usr/local/lib/vulture/libopenblas.so.0
    /bin/ln -s /home/vlt-gui/lib-11.0/libopenblasp.so.0  /usr/local/lib/vulture/libopenblasp.so.0

    /bin/echo "[*] Update of Vulture-LIBS ended successfully"

else
    /usr/local/bin/wget --no-check-certificate https://dl.vultureproject.org/10.3/Vulture-LIBS.tar.gz >>/tmp/installation.log 2>&1
    cd /home/vlt-gui
    /usr/bin/tar xf /tmp/Vulture-LIBS.tar.gz
    /usr/sbin/chown -R vlt-gui:vlt-gui /home/vlt-gui/

    /bin/mkdir -p /usr/local/lib/vulture
    /bin/ln -s /home/vlt-gui/lib-10.3/libgcc_s.so.1 /usr/local/lib/vulture/libgcc_s.so.1
    /bin/ln -s /home/vlt-gui/lib-10.3/libgfortran.so.3 /usr/local/lib/vulture/libgfortran.so.3
    /bin/ln -s /home/vlt-gui/lib-10.3/libquadmath.so.0 /usr/local/lib/vulture/libquadmath.so.0
    /bin/ln -s /home/vlt-gui/lib-10.3/liblapack.so.4 /usr/local/lib/vulture/liblapack.so.4
    /bin/ln -s /home/vlt-gui/lib-10.3/libblas.so.2 /usr/local/lib/vulture/libblas.so.2
    /bin/ln -s /home/vlt-gui/lib-10.3/libopenblas.so.0  /usr/local/lib/vulture/libopenblas.so.0
    /bin/ln -s /home/vlt-gui/lib-10.3/libopenblasp.so.0  /usr/local/lib/vulture/libopenblasp.so.0

    /bin/echo "[*] Update of Vulture-LIBS ended successfully"
fi


