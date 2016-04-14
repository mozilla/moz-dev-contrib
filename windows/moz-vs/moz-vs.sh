#
# moz-vs-common.sh
#

moz_vs() {
    MOZ_TARGET_ENV="$1"
    temp=`mktemp`
    case "$MOZ_TARGET_ENV" in
	2015|2015-64|vs2015-64)
	    /usr/share/moz-vs/moz-vs-get-values.py amd64 2015 > $temp
	    . $temp
	    rm -f $temp
	    ;;
	2015-32|vs2015-32)
	    /usr/share/moz-vs/moz-vs-get-values.py x86 2015 > $temp
	    . $temp
	    rm -f $temp
	    ;;
	*)
	    echo Usage: moz_vs env
	    echo   Valid environment names:
	    echo     2015 2015-64 vs2015-64   Visual Studio 2015, 64-bit 
	    echo     2015-32 vs2015-32        Visual Studio 2015, 32-bit 
	;;
    esac
}

