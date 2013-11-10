#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

/* extern int sum(void*, void*, void*); */
extern int sumA_1(void*, void*, void*);
extern int sumA_2(void*, void*, void*);

/* int sum(void* a, void *b, void * c)  */
/* { */
/*    return sumA_1 */
/* } */

int sumA_0(void* q, void* r, void* s)
{
   int size = 28;
   char *a = "foo.arr";
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

int sumA_1(void* q, void* b, void* c)
{
   int size = 8;
   char *a = "bar.arr";
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

