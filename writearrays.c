#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define ARRAY1 "foo.arr"
#define A1_SIZE 28
#define ARRAY2 "bar.arr"
#define A2_SIZE 12

int main (int argc, char **argv) {
   /* int *a = malloc(10 * sizeof(int)); */
   /* int *b = malloc(A2_SIZE * sizeof(int)); */
   /* int a[3][3] = {{1,1,1},{1,1,1},{1,1,1}}; */
   /* int b[2][2] = {{2,2},{2,2}}; */
   int a[A1_SIZE] = {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1};
   int b[A2_SIZE]  = {2,2,2,2,2,2,2,2,2,2,2,2};
   fprintf(stderr, "%d\n", S_IRWXU);

   /* for (int i = 0; i < 6; i++) { */
   /*    for (int j = 0; j < 6; j++) { */
   /* 	 if (i < 5 && j < 5) a[i][j] = 1; */
   /* 	 b[i][j] = 2; */
   /*    } */
   /* } */
   
   int fd1 = creat(ARRAY1, S_IRWXU);
   int fd2 = creat(ARRAY2, S_IRWXU);

   /* int fd1 = open(ARRAY1, O_WRONLY | O_CREAT); */
   /* int fd2 = open(ARRAY2, O_WRONLY | O_CREAT); */

   ssize_t w1 = write(fd1, a, A1_SIZE * sizeof(int));
   ssize_t w2 = write(fd2, b, A2_SIZE * sizeof(int));
   if (w1 != A1_SIZE * sizeof(int)){
      fprintf(stderr, "array 1 only wrote %d bytes!\n", (int) w1);
   } else if (w2 != A2_SIZE * sizeof(int)) {
      fprintf(stderr, "array 2 only wrote %d bytes!\n", (int) w2);
      return 1;
   } else {
      printf("arrays written successfully to './%s' and './%s'\n", ARRAY1, ARRAY2);
      /* int fdt = open(ARRAY1, O_RDONLY); */
      /* int ***buf = calloc(3, sizeof(int**)); */
      /* /\* int ***buf = calloc(27, sizeof(int)); *\/ */
      /* buf[0] = calloc(3, sizeof(int*)); */
      /* buf[1] = calloc(3, sizeof(int*)); */
      /* buf[2] = calloc(3, sizeof(int*)); */

      /* buf[0][0] = calloc(3, sizeof(int)); */
      /* buf[0][1] = calloc(3, sizeof(int)); */
      /* buf[0][2] = calloc(3, sizeof(int)); */

      /* buf[1][0] = calloc(3, sizeof(int)); */
      /* buf[1][1] = calloc(3, sizeof(int)); */
      /* buf[1][2] = calloc(3, sizeof(int)); */

      /* buf[2][0] = calloc(3, sizeof(int)); */
      /* buf[2][1] = calloc(3, sizeof(int)); */
      /* buf[2][2] = calloc(3, sizeof(int)); */

      /* /\* (void) read(fdt, (void*) buf, 27 * sizeof(int)); *\/ */

      /* (void) read(fdt, (void*) buf[0][0], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[0][1], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[0][2], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[1][0], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[1][1], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[1][2], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[2][0], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[2][1], 3 * sizeof(int)); */
      /* (void) read(fdt, (void*) buf[2][2], 3 * sizeof(int)); */


      /* printf("%d\n", buf[0][0][0]); */
   }

   close(fd1);
   close(fd2);
   return 0;
}      
   
