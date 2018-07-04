# Example watch control file for uscan
# Rename this file to "watch" and then you can run the "uscan" command
# to check for upstream updates and more.
# See uscan(1) for format

# Compulsory line, this is a version 3 file
version=3

# Uncomment to examine a Webpage
# <Webpage URL> <string match>
#http://www.example.com/downloads.php puppet-module-openio-gridinit-(.*)\.tar\.gz

# Uncomment to examine a Webserver directory
#http://www.example.com/pub/puppet-module-openio-gridinit-(.*)\.tar\.gz

# Uncommment to examine a FTP server
#ftp://ftp.example.com/pub/puppet-module-openio-gridinit-(.*)\.tar\.gz debian uupdate

# Uncomment to find new files on sourceforge, for devscripts >= 2.9
# http://sf.net/puppet-module-openio-gridinit/puppet-module-openio-gridinit-(.*)\.tar\.gz

# Uncomment to find new files on GooglePages
# http://example.googlepages.com/foo.html puppet-module-openio-gridinit-(.*)\.tar\.gz
