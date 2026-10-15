import os

from function import bpy_host

if __name__ == "__main__":
    print(os.path.dirname(os.path.realpath(__file__)))

    file_name = "69b1dc99f17f3040723b6f8f023ce33081064bd763e3b5f84d048b4c12f3c828"

    bpy_host.main(file_name)