
# avahi-browse -d local -atlpc
import subprocess as sp

def get_hosts(domain='.local'):
    hosts = set()
    p = sp.Popen(['avahi-browse', '-alrpt'], stdout=sp.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode()
    for line in stdout.splitlines():
        elements = line.split(';')
        hosts = hosts | set([x for x in elements if x.endswith(domain)])
    return sorted(hosts)


if __name__ == '__main__':
    hosts = get_hosts()
    for host in hosts:
        print(host)
