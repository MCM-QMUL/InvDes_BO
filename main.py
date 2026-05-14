import hydra
import sys
import os
import time
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.abspath('C:\\Temp\\\InvDes_GAN'))

from create_init_data import get_init_data  

@hydra.main(config_path='', config_name="config_init_data")
def main(config):

    get_init_data(config, mode='local')

if __name__ == "__main__":
    main()
