import os

from function import bpy_host
import main

if __name__ == "__main__":
    print(os.path.dirname(os.path.realpath(__file__)))

    file_name = "09f310509064de763da2daeb7232270ba1b186a48bae9577e9e23185c1eed338"

    # bpy_host.main(file_name)

    main.generateFish(file_name)