import sys, time, builtins

def type_print(*args, speed=0.01, end="\n", sep=" ", **kwargs):
    text = sep.join(str(a) for a in args)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write(end)
    sys.stdout.flush()

# Override the built-in print
builtins.print = type_print
