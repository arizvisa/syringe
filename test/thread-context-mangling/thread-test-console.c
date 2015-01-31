#include <stdio.h>
#include <windows.h>

void
fatal(char* string)
{
    int res;
    char buffer[128];

#if 0
    OutputDebugString(string);
    OutputDebugString("\n");
#endif

    res = GetLastError();

    /* i think stack-based overflows give a program character. */
    sprintf(buffer, "%s\nGetLastError: %x\n", string, res);
    OutputDebugString(buffer);
    exit(0);
}

DWORD WINAPI
workerthread(void* param)
{
    for(;;) {
        Sleep(1000);
    }
    return 0;
}

int
createWorkerThread()
{
    int res;
    HANDLE hThread;
    DWORD threadId;

    res = (int)CreateThread(NULL, 0, workerthread, NULL, CREATE_SUSPENDED, &threadId);
    if (res == 0)
        fatal("unable to create worker thread");
    hThread = (HANDLE)res;

    ResumeThread(hThread);

    CloseHandle(hThread);
    return threadId;
}

int
main(int argc, char** argv)
{
    printf("started process %d\n", GetCurrentProcessId());
    printf("started thread %x\n", createWorkerThread());
    for(;;) {
        Sleep(5000);
    }
    return 0;
}
