Name:                   certmonger
Version:                0.79.11
Release:                2
Summary:                Certificate status monitor and PKI enrollment client
License:                GPLv3+
URL:                    http://pagure.io/certmonger/
Source0:                https://pagure.io/certmonger/archive/certmonger-%{version}/certmonger-certmonger-%{version}.tar.gz

Patch0001:              Don-t-free-soptions-while-it-is-still-needed.patch

BuildRequires:          autoconf automake gettext-devel gcc openldap-devel krb5-devel
BuildRequires:          libidn2-devel dbus-devel nspr-devel nss-devel openssl-devel
BuildRequires:          libuuid-devel libtalloc-devel libtevent-devel libcurl-devel
BuildRequires:          libxml2-devel xmlrpc-c-devel systemd-units diffutils expect
BuildRequires:          nss-tools openssl /usr/bin/dbus-launch /usr/bin/dos2unix
BuildRequires:          /usr/bin/unix2dos /usr/bin/which python3-dbus popt-devel
Requires:               dbus
Requires(post):         %{_bindir}/dbus-send systemd-units
Requires(preun):        systemd-units dbus sed
Requires(postun):       systemd-units
Conflicts:              libtevent < 0.9.13

%description
Certmonger is a service which is primarily concerned with getting your
system enrolled with a certificate authority (CA) and keeping it enrolled.

%package help
Summary:             Documentation for help using certmonger
provides:            certmonger = %{version}-%{release}

%description help
This package provides docs for user of certmonger.

%prep
%autosetup -n certmonger-certmonger-%{version} -p1 -S git

%build
autoreconf -i -f
%configure \
    --enable-systemd --enable-tmpfiles --with-homedir=/var/run/certmonger \
    --with-tmpdir=/var/run/certmonger --enable-pie --enable-now
%make_build XMLRPC_LIBS="-lxmlrpc_client -lxmlrpc_util -lxmlrpc"

%install
%make_install
install -d $RPM_BUILD_ROOT/%{_localstatedir}/lib/certmonger/{cas,requests}
install -m755 -d $RPM_BUILD_ROOT/var/run/certmonger
%{find_lang} %{name}

%check
make check

%post
if test $1 -eq 1 ; then
    %{_bindir}/dbus-send --system --type=method_call --dest=org.freedesktop.DBus / org.freedesktop.DBus.ReloadConfig 2>&1 || :
fi
if test $1 -eq 1 ; then
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%triggerin -- certmonger < 0.58
if test $1 -gt 1 ; then
    objpath=`dbus-send --system --reply-timeout=10000 --dest=org.openeulerhosted.certmonger \
    --print-reply=o /org/openeulerhosted/certmonger org.openeulerhosted.certmonger.find_ca_by_nickname \
                  string:dogtag-ipa-renew-agent 2> /dev/null | sed -r 's,^ +,,g' || true`
    if test -n "$objpath" ; then
        dbus-send --system --dest=org.openeulerhosted.certmonger --print-reply /org/openeulerhosted/certmonger \
                                  org.openeulerhosted.certmonger.remove_known_ca objpath:"$objpath" >/dev/null 2> /dev/null
    fi
    for cafile in %{_localstatedir}/lib/certmonger/cas/* ; do
        if grep -q '^id=dogtag-ipa-renew-agent$' "$cafile" ; then
            rm -f "$cafile"
        fi
    done
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart certmonger.service >/dev/null 2>&1 || :
fi

%preun
if test $1 -eq 0 ; then
    /bin/systemctl --no-reload disable certmonger.service > /dev/null 2>&1 || :
    /bin/systemctl stop certmonger.service > /dev/null 2>&1 || :
fi

%triggerun -- certmonger < 0.43
/sbin/chkconfig --del certmonger >/dev/null 2>&1 || :
/bin/systemctl try-restart certmonger.service >/dev/null 2>&1 || :

%files -f %{name}.lang
%doc README.md LICENSE STATUS doc/*.txt
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/*
%{_datadir}/dbus-1/services/*
%dir %{_sysconfdir}/certmonger
%config(noreplace) %{_sysconfdir}/certmonger/certmonger.conf
%dir /var/run/certmonger
%{_bindir}/*
%{_sbindir}/certmonger
%{_libexecdir}/%{name}
%{_localstatedir}/lib/certmonger
%attr(0644,root,root) %config(noreplace) %{_tmpfilesdir}/certmonger.conf
%{_unitdir}/*
%{_datadir}/dbus-1/system-services/*

%files help
%doc LICENSE doc/*.txt
%{_mandir}/man*/*

%changelog
* Tue Oct 27 2020 leiju <leiju4@huawei.com> - 0.79.11-2
- Modify BuildRequires from python2-dbus to python3-dbus

* Thu Aug 06 2020 lingsheng <lingsheng@huawei.com> - 0.79.11-1
- Update to 0.79.11

* Thu May 14 2020 Jeffery.Gao <gaojianxing@huawei.com> - 0.79.8-3
- Package init
