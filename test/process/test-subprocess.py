import os,signal,threading,Queue,subprocess,time
class spawn(object):
    """Spawns a program along with a few monitoring threads.

    Provides stdout and stderr in the form of Queue.Queue objects to allow for asynchronous reading.
    """

    program = None              # subprocess.Popen object
    stdout,stderr = None,None   # queues containing stdout and stderr
    id = property(fget=lambda s: s.program.pid)
    running = property(fget=lambda s: s.program.poll() is None)

    def __init__(self, command, **kwds):
        # process
        env = kwds.get('env', os.environ)
        cwd = kwds.get('cwd', os.getcwd())
        joined = kwds.get('joined', True)
        newlines = kwds.get('newlines', True)
        self.program = program = self.__newprocess(command, cwd, env, newlines, joined=joined)

        ## monitor threads (which aren't important if python didn't suck with both threads and gc)
        threads = []
        t,stdout = spawn.monitorPipe('thread-%x-stdout'% program.pid, program.stdout)
        threads.append(t)
        if not joined:
            t,stderr = spawn.monitorPipe('thread-%x-stderr'% program.pid, program.stderr)
            threads.append(t)
        else:
            stderr = None
        self.__threads = threads

        # queues containing stdout and stderr
        self.stdout,self.stderr = stdout,stderr

        # set things off
        for t in threads:
            t.start()

    def __newprocess(self, program, cwd, environment, newlines, joined):
        stderr = subprocess.STDOUT if joined else subprocess.PIPE
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            return subprocess.Popen(program, universal_newlines=newlines, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, close_fds=False, startupinfo=si, cwd=cwd, env=environment)
        return subprocess.Popen(program, universal_newlines=newlines, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, close_fds=True, cwd=cwd, env=environment)

    @staticmethod
    def monitorPipe(id, pipe, blocksize=1):
        """Create a monitoring thread that stuffs data from a pipe into a queue.

        Returns a (threading.Thread, Queue.Queue)
        (Queues are the only python object that allow you to timeout if data isn't currently available)
        """

        def shuffle(queue, pipe):
            while not pipe.closed:
                data = pipe.read(blocksize)
                queue.put(data)
            return

        q = Queue.Queue()   # XXX: this should be a multiprocessing.Pipe, but i've had many a problems with that module
        if id is None:
            monitorThread = threading.Thread(target=shuffle, args=(q,pipe))
        else:
            monitorThread = threading.Thread(target=shuffle, name=id, args=(q,pipe))
        monitorThread.daemon = True
        return monitorThread,q

    def write(self, data):
        """Write data directly to program's stdin"""
        if self.running:
            return self.program.stdin.write(data)

        pid,result = self.program.pid,self.program.poll()
        raise IOError('Unable to write to terminated process %d. Process terminated with a returncode of %d'% (pid,result))

    def signal(self, signal):
        """Send a signal to the program"""
        if self.running:
            return self.program.send_signal(signal)

        pid,result = self.program.pid,self.program.poll()
        raise IOError('Unable to signal terminated process %d. Process terminated with a returncode of %d'% (pid,result))

    def wait(self, timeout=0.0):
        """Wait for a process to terminate"""
        program = self.program

        if timeout:
            t = time.time()
            while t + timeout > time.time():        # spin until we timeout
                if program.poll() is not None:
                    return program.returncode
                continue
            return None

        return program.wait()

    def stop(self):
        """Sends a SIGKILL signal and then waits for program to complete"""
        if not self.running:
            self.stop_monitoring()
            return self.program.poll()

        p = self.program
        p.kill()
        result = p.wait()
        self.stop_monitoring()
        self.program = None
        return result

    def stop_monitoring(self):
        """Cleanup monitoring threads"""

        # close pipes that have been left open since python fails to do this on program death
        p,stdout,stderr = self.program,self.stdout,self.stderr

        p.stdin.close()
        for q,p in ((stdout,p.stdout), (stderr,p.stderr)):
            if q is None:
                continue
            q.mutex.acquire()
            while not p.closed:
                try: p.close()
                except IOError:
                    continue
            q.mutex.release()
        [ x.join() for x in self.__threads]

if __name__ == '__main__':
    import sys,time
    program = spawn('python.exe -i', joined=True)

    # this is not the way the "protocol" works
    # ...but i don't really want to implement expect

    while program.running:
        time.sleep(0.2)
        for q in (program.stdout,program.stderr):
            if q is None:
                continue
            data = ''
            while not q.empty():
                data += q.get()
            if data:
                print data,
        else:
            program.write(raw_input() + "\n")
        continue
