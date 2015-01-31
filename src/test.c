//#include <windows.h>
#include <Python.h>

char* python_main = "print 'hello world'\n"
"x = file('./test.txt','wb')\n"
"x.write('holy fuck')\n"
"x.close()\n";

int
main(int argc, char** argv)
{
    (void)Py_Initialize();
    (int)PyRun_SimpleString(python_main);
    (void)Py_Finalize();
    return 0;
}

int
test(void)
{
    return 0;
}
