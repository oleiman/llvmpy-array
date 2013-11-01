#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

int main (int argc, char **argv) {
   int *a = malloc(10 * sizeof(int));
   int *b = malloc(12 * sizeof(int));
   for (int i = 0; i < 12; i++) {
      if (i < 10) a[i] = 1;
      b[i] = 2;
   }
   
   int fd1 = creat("foo.arr", S_IRWXU);
   int fd2 = creat("bar.arr", S_IRWXU);

   ssize_t w1 = write(fd1, a, 10 * sizeof(int));
   ssize_t w2 = write(fd2, b, 12 * sizeof(int));
   if (w1 != 10 * sizeof(int)){
      fprintf(stderr, "array 1 only wrote %d bytes!\n", (int) w1);
   } else if (w2 != 12 * sizeof(int)) {
      fprintf(stderr, "array 2 only wrote %d bytes!\n", (int) w2);
      return 1;
   } else {
      printf("arrays written successfully!\n%d\nlet's try it:\n", a[8]);
      int fdt = open("foo.arr", O_RDONLY);
      int *buf = calloc(10, sizeof(int));
      (void) read(fdt, (void*) buf, 10 * sizeof(int));
      for (int i = 0; i < 10; i++){
      	 printf("%d", buf[i]);
      	 printf("%c", (i < 9 ? ' ' : '\n'));
      }
   }

   close(fd1);
   close(fd2);
   return 0;
}      
   
