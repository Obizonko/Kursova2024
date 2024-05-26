with open('models.py', 'rb') as f:
    for line in f:
        if b'\x00' in line:
            print("Нульовий байт знайдено у рядку:", line)
