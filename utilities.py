import os, random, string

def generate_password(length=32):
    # https://stackoverflow.com/questions/7479442/high-quality-simple-random-password-generator#7480271
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024))

    return ''.join(random.choice(chars) for i in range(length))
