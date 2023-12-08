import subprocess
import os
import signal


def execute(command):
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True, preexec_fn=os.setsid)

    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
        if 'close' in stdout_line or 'finished' in stdout_line:
            os.killpg(os.getpgid(popen.pid), signal.SIGTERM)

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


cmd = ['python3', '-u', 'ME_main.py loop']
while 1:
    for path in execute(cmd):
        print(path, end="")
