#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

extern int sum(char*, char*, int, int);
int sumA(char*, int);

int sum(char *a1, char *a2, int size1, int size2) 
{
   return sumA(a1, size1) + sumA(a2, size2);
}

int sumA(char *a, int size) 
{
   int res = 0;
   int fd = open(a, O_RDONLY);
   int *buf = calloc(size, sizeof(int));
   ssize_t bytes_read = read(fd, buf, size * sizeof(int));
   if (bytes_read < size * sizeof(int)) {
      fprintf(stderr, "incorrect size given for %s [%d]\n", a, size);
   }
   for (int i = 0; i < size; i++) {
      res += buf[i];
   }
   return res;
}
