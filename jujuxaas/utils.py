import subprocess

def run_command(args, stdin='', exit_codes=[0], **kwargs):
  print 'Running command: ' + ' '.join(args)

  proc = subprocess.Popen(args,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          **kwargs)

  out, err = proc.communicate(input=stdin)
  retcode = proc.returncode
  if not retcode in exit_codes:
    print "Calling return error: " + ' '.join(args)
    print "Output: " + out
    print "Error: " + err
    raise subprocess.CalledProcessError(retcode, args)
  return out, err

# Updates a key-value file to set the key to the value
def update_keyvalue(path, entries):
  with open(path) as f:
    existing = f.read()
  lines = existing.split('\n')
  for i in range(len(lines)):
    raw_line = lines[i]
    line = raw_line.trim()
    for k, v in entries.iteritems():
      if line.startswith(k + "="):
        updated = k + "=" + v
        if line != updated:
          changed = True
          lines[i] = updated
  if updated:
    with open(path, 'w') as f:
        f.write(lines.join('\n'))
  return updated

# Writes a file, checking if the contents have changed
def write_file(path, contents):
  with open(path) as f:
    existing = f.read()
  if existing == contents:
    return False
  with open(path, 'w') as f:
    f.write(contents)
  return True


# Installs the specified packages
def apt_get_install(pkgs):
  cmd = [
        'apt-get',
        '-y',
        'install'
        ]
  for pkg in pkgs:
    cmd.append(pkg)
  run_command(cmd)
