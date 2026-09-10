import os
import subprocess
import time


class Cancelled(Exception): pass


def own_process_tree(proc):
    """Windows job containing only this new child and its descendants.

    Closing it cleans up renderer browsers/encoders, never unrelated apps or Warp.
    """
    if os.name != 'nt':return lambda:None
    import ctypes
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_=[('process_time',ctypes.c_int64),('job_time',ctypes.c_int64),('flags',w.DWORD),
                  ('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',w.DWORD),
                  ('affinity',ctypes.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
    class IO(ctypes.Structure):
        _fields_=[(n,ctypes.c_uint64) for n in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
    class Extended(ctypes.Structure):
        _fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),
                  ('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];kernel.CreateJobObjectW.restype=w.HANDLE
    kernel.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
    kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
    kernel.CloseHandle.argtypes=[w.HANDLE]
    job=kernel.CreateJobObjectW(None,None)
    limits=Extended();limits.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not job or not kernel.SetInformationJobObject(job,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(job,w.HANDLE(int(proc._handle))):
        if job:kernel.CloseHandle(job)
        proc.terminate();proc.wait(timeout=10)
        raise RuntimeError('Could not contain the renderer process tree for cancellation.')
    return lambda:kernel.CloseHandle(job)


def popen(args, **kwargs):
    # Only launches owned child processes; never touches Warp or other windows.
    return subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0, **kwargs)


def run(args, *, cwd=None, timeout=120, cancel=None, env=None, input=None):
    proc = popen(args, cwd=cwd, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    start=time.monotonic()
    try:
        while True:
            if cancel and cancel.is_set(): raise Cancelled('Cancelled')
            if time.monotonic()-start > timeout: raise TimeoutError('This step timed out. Retry with a shorter clip.')
            try:
                out, err = proc.communicate(input=input, timeout=.5)
                break
            except subprocess.TimeoutExpired: input=None
        if proc.returncode: raise RuntimeError(err.decode('utf-8',errors='replace')[-1800:] or 'Process failed.')
        return out
    finally:
        if proc.poll() is None:
            proc.terminate() # This exact child only.
            try: proc.communicate(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.communicate()


def run_logged(args, input_path, prefix, *, timeout=900, cancel=None, env=None):
    """Persist diagnostics as they arrive; invoke the native owned executable directly."""
    with input_path.open('rb') as inp, prefix.with_suffix('.stdout.log').open('wb') as out, prefix.with_suffix('.stderr.log').open('wb') as err:
        proc=popen(args,cwd=input_path.parent,stdin=inp,stdout=out,stderr=err,env=env)
        started=time.monotonic()
        try:
            while proc.poll() is None:
                if cancel and cancel.is_set():raise Cancelled()
                if time.monotonic()-started>timeout:raise TimeoutError('ChatGPT analysis timed out. Retry with a shorter clip.')
                try:proc.wait(timeout=.5)
                except subprocess.TimeoutExpired:pass
            if proc.returncode:
                err.flush()
                raise RuntimeError(prefix.with_suffix('.stderr.log').read_text(encoding='utf-8',errors='replace')[-1800:])
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
