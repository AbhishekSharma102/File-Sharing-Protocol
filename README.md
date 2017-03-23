This is a simple python app, to keep two directories synced using sockets.

Commands:
index longlist - gives information about files(name, size, type, timestamp).
index shortlist <starttimestamp> <endtimestamp> - gives information about files between certain specified timestamp.
index regex <regex> - lists files matching the regex.

hash verify <filename> - returns md5 hash of input file.
hash checkall - returns hash of all files.

download TCP <filename> - Downloads the given file using TCP protocol and shows its size, timestamp and MD5 hash.
download UDP <filename> - Downloads the given file using UDP protocol and verifies its hash with the newly downloaded file.

The directories are also periodically synced, including sub directories. File permissions are also preserved during these operations.