#include <stdio.h>

#include <windows.h>

typedef int (*somefuncptr)(int);

int
main(int argc, char** argv)
{
    HANDLE hPlugin; int res;
    somefuncptr func;

    hPlugin = LoadLibrary(argv[1]);
    if (hPlugin == NULL) {
        printf("well...shit...\n");
        return 0;
    }

    func = GetProcAddress(hPlugin, argv[2]);
    if (func == NULL) {
        printf("well...fuck...\n");
        return 0;
    }

    res = func( atoi(argv[3]) );
    for(;;){}   // i'm a dick
    return res;
}

