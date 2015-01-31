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

LRESULT CALLBACK
defaultwindowproc(HWND hWnd, UINT nMsg, WPARAM wParam, LPARAM lParam)
{
    int res;
    HDC hDC; PAINTSTRUCT ps;
    char ilovestack[254];

    switch (nMsg) {
#if 0
        case WM_CREATE:
            break;
#endif
    
        case WM_LBUTTONDOWN:
            res = createWorkerThread();
            sprintf(ilovestack, "created thread %x", res);
            SetWindowText(hWnd, ilovestack);
            break;

        case WM_PAINT:
            hDC = BeginPaint(hWnd, &ps);
            EndPaint(hWnd, &ps);
            break;

        case WM_DESTROY:
            PostQuitMessage(0);
            break;

        default:
            return DefWindowProc(hWnd, nMsg, wParam, lParam);
    }
    return 0;
}

int WINAPI
WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR cmdline, int nCmdShow)
{
    int res;
    WNDCLASSEX wndclass; MSG msg; int className; HWND hWnd;
    memset(&wndclass, 0, sizeof(wndclass));

    wndclass.cbSize = sizeof(wndclass);
    wndclass.style = CS_HREDRAW|CS_VREDRAW;
    wndclass.lpfnWndProc = defaultwindowproc;
    wndclass.cbClsExtra = wndclass.cbWndExtra = 0;
    wndclass.hInstance = hInst;
    wndclass.hIcon = wndclass.hIconSm = 0;
    wndclass.hCursor = 0;
    wndclass.hbrBackground = GetStockObject(BLACK_BRUSH);
    wndclass.lpszMenuName = 0;
    wndclass.lpszClassName = "HiThere";

    res = RegisterClassEx(&wndclass);
    if (res == 0)
        fatal("unable to register window class");
    className = res;

    sprintf((char*)&wndclass, "hello, i am %d", GetCurrentProcessId());
    res = (int)CreateWindowEx(0, (char*)className, 
        (char*)&wndclass, WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        CW_USEDEFAULT, CW_USEDEFAULT,
        NULL, NULL, hInst, NULL);

    if (res == 0)
        fatal("unable to create window");
    hWnd = (HWND)res;

    ShowWindow(hWnd, nCmdShow);
    UpdateWindow(hWnd);

    while (res=GetMessage(&msg, NULL, 0, 0)) {
        res = TranslateMessage(&msg);
        res = DispatchMessage(&msg);
    }
    return 0;
}

