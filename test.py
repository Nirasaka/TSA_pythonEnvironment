import os

from function import bpy_host

if __name__ == "__main__":
    print(os.path.dirname(os.path.realpath(__file__)))

    file_name = "8b0a5e257613fd25d4b4d0d82ea1c7fe73ea9e3a81cb213ea46859d0b86e7fa7"

    bpy_host.main(file_name)