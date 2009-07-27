#include <stdio.h>

extern void loader();
extern void pause();

int
_djbhash32(char* string, int hash)
{
    unsigned char n = *string;

    if (*string == 0)
        return hash;

    return _djbhash32(string+1, hash*33 + n);
}

int
djbhash32(char* string)
{
    return _djbhash32(string, strlen(string));
}

int
_othash32(char* string, int hash)
{
    unsigned char n = *string;

    if (n == 0)
        return hash;

    hash += n;
    hash += (hash << 10);
    hash ^= (hash >> 6);
    return _othash32(string+1, hash);
}

int
othash32(char* string)
{
    int res;
    res = _othash32(string, 0);
    res += (res << 3);
    res ^= (res >> 11);
    res += (res << 15);
    return res;
}

char*
randBuffer(int length)
{
    char* p;
    int i;

    p = malloc(length+1);
    if (p == NULL)
        return NULL;

    for (i = 0; i < length; i++)
        p[i] = rand()&0xff;
    p[i] = 0;
    return p;
}

int
main(int argc, char** argv)
{
    char* string;
    int i;

    loader();
/*
    string = "ntdll.dll";
    printf("%s = %08x\n", string, djbhash32(string));

    string = "NtQueueThreadApc";
    printf("%s = %08x\n", string, djbhash32(string));
*/

/*
    for(;;) {
        string = randBuffer( rand()&0xf );
        printf("%08x - %s\n", othash32(string), string);
        free(string);
    }
*/

    return 0;
}
