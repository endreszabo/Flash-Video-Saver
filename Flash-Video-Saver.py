#!/usr/bin/python2
import os
from stat import S_IWUSR, S_IRUSR 
from shutil import copyfile
from time import strftime, localtime, sleep, time

hosting_processes=['plugin-container']   #flash plugin container process name
dest_dir=os.environ['HOME']+'/Downloads' #target dir where file will be saved
min_size=500000                          #minimum file size limit
file_age=30                              #files this many seconds untouched will be saved (implicit facepalm)

saved_items={}

def find_container():
	return filter(is_container, os.listdir('/proc'))

def is_container(pid):
	try:
		exe=os.path.realpath("/proc/%s/exe" % pid)
		return any(exe.endswith(process) for process in hosting_processes)
	except:
		return False

def find_fds(pid):
	writing=[]
	written=[]
	basedir="/proc/%s/fd" % pid
	for i in os.listdir(basedir):
		rp=os.path.realpath(basedir+'/'+i)
		if 'tmp/FlashX' in rp:
			print "found %s" % i
			stat=os.stat(basedir+'/'+i)
			mode=stat.st_mode
			# epic fail:
			#
			# due to the non-deterministic behaviour of the flash plugin,
			# i have to workaround detection of downloaded stuff like below:
			#
			#print S_IWUSR, mode
			#if S_IWUSR & mode:
			#	if S_IRUSR & mode:
			#		written.append(basedir+'/'+i)
			#	else:
			#		writing.append(basedir+'/'+i)
			print time()
			print stat.st_mtime
			print "diff:", time()-stat.st_mtime
			if time()-stat.st_mtime > file_age:
				written.append(basedir+'/'+i)
			else:
				writing.append(basedir+'/'+i)
	
	print(written,writing)
	return(written,writing)

def save_file(fd):
	i=0
	filename=strftime("%Y-%m-%d_%H.%M.%S", localtime())
	destfile="%s/%s.flv" % (dest_dir, filename)
	while os.path.exists(destfile):
		i+=1
		destfile="%s/%s-%d.flv" % (dest_dir, filename, i)
	try:
		print "Copying %s to %s" % (fd, destfile)
		copyfile(fd, destfile)
	except:
		return False
	return os.stat(fd)

while True:
	pids=find_container()
	for pid in pids:
		found_fds=find_fds(pid)
		for fd in found_fds[0]:
			lstat=os.lstat(fd)
			rstat=os.stat(fd)
			print "fd in saved:", fd in saved_items
			if (fd not in saved_items) or (fd in saved_items and saved_items[fd] != rstat):
				if fd in saved_items:
					print saved_items[fd]
					print rstat
				if rstat.st_size>min_size:
					stat=save_file(fd)
					if stat:
						saved_items[fd]=stat
			if fd in saved_items and saved_items[fd] == rstat:
				pass
		if found_fds[1]:
			print "Not saving uncomplete fds: %s" % repr(found_fds[1])
	sleep(5)
