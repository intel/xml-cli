#include <unistd.h>
#include <sys/types.h>
#include <errno.h>
#include <fcntl.h>

int mem_read(const unsigned long, void const *, const size_t);
int mem_write(const unsigned long, const void const *, const size_t);

static int mem_fh = -1;

static int mem_open() {
  int res;

  // Our file handler to /dev/mem is already opened
  if (mem_fh != -1) {
    return errno = EBADF;
  }

  // Constantly try to open the /dev/mem file, taking into account any system interrupts we get
  do {
    res = open("/dev/mem", O_RDWR | O_SYNC);
  } while (res == -1 && errno == EINTR);

  // If we had an issue opening the file, and no system interrupt occurred, then return the errno
  if (res == -1) {
    return errno;
  }

  // Set our file handler to /dev/mem and return 0
  mem_fh = res;
  return 0;
}

int mem_read(const unsigned long addr, void const *dest, const size_t bytes) {

  // Cast off our const arguments
  unsigned char *d = (unsigned char *) dest;
  off_t off = (off_t) addr;
  size_t n = bytes;
  ssize_t	b_read;

  while (n) {

    // Read n bytes from /dev/mem starting at offset equal to our address and store it in dest
    b_read = pread(mem_fh, d, n, off);

    // If we read all n bytes in a single read, then return 0
    if (b_read == (ssize_t) n) {
      return 0;
    }

    else if (b_read >= (ssize_t) 0) {
      // We need to set up for the next read
      d += b_read;  		// We now need to start r to base_dest + b
      off += b_read;  	// We now need to read from base_addr + b
      n -= b_read;		// We now need to only read n-b more bytes
    }

    // If we have a bad file descriptor, try to re-open the file
    else if(errno == EBADF) {
      if(mem_open()) {
        return errno;
      }
    }

    // If we get something < -1 then we have some IO error
    else if(b_read != (ssize_t)-1) {
      return errno = EIO;
    }
  }

  return 0;
}

int mem_write(const unsigned long addr, const void *source, const size_t bytes) {

  // Cast off our const arguments
  unsigned char *s = (unsigned char *) source;
  off_t off = (off_t) addr;
  size_t n = bytes;
  ssize_t	b_written;

  while(n) {
    // Write n bytes from source to /dev/mem using our address as offset
    b_written = pwrite(mem_fh, s, n, off);

    // If we wrote all n bytes in a single write, then return 0
    if (b_written == (ssize_t) n) {
      return 0;
    }

    else if (b_written >= (ssize_t) 0) {
      // We need to set up for the next write
      s += b_written; 	// We now need to start reading to base_source + b
      off += b_written;  	// We now need to write to base_addr + b
      n -= b_written;		// We now need to only write n-b more bytes
    }

    // If we have a bad file descriptor, try to re-open the file
    else if (errno == EBADF) {
      if (mem_open()) {
        return errno;
      }
    }

    // If we get something < -1 then we have some IO error
    else if (b_written != (ssize_t)-1) {
      return errno = EIO;
    }
  }

  return 0;
}
