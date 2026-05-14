import torch
import warnings
from botorch.exceptions import BadInitialCandidatesWarning, InputDataWarning
import os
import sys
import logging
from hydra.core.hydra_config import HydraConfig
import pandas as pd
import numpy as np
import time
from time import sleep
import random
from filelock import FileLock  

tkwargs = {"dtype": torch.double, "device": torch.device("cuda" if torch.cuda.is_available() else "cpu")}

def fetch_next_job(samples_file_path):
    """Fetch the next available job with 'pending' status, ensuring only one task can access the file at a time."""
    lock_path = samples_file_path + ".lock"
    with FileLock(lock_path):  
        df = pd.read_csv(samples_file_path)
        for idx, row in df.iterrows():
            if row['status'] == 'pending':
                df.loc[idx, 'status'] = 'in_progress'
                df.to_csv(samples_file_path, index=False)
                return idx, row  
    return None, None  

def update_job_status(samples_file_path, job_index, input_columns, current_x, output_columns, numeric_output, status='completed'):
    """Update the job status and result in the shared CSV file, ensuring safe access with file locking."""
    lock_path = samples_file_path + ".lock"
    with FileLock(lock_path):

        df = pd.read_csv(samples_file_path)
        
        df.loc[job_index, 'status'] = status

        if isinstance(current_x, torch.Tensor):
            df.loc[job_index, input_columns] = current_x.cpu().numpy()
        else:
            df.loc[job_index, input_columns] = current_x.to_numpy()
        
        if 'Stress' in output_columns:
            strain = np.linspace(0, 0.5, 201)

            if isinstance(numeric_output, pd.DataFrame):
                stress_values = numeric_output.to_numpy().reshape(-1)
            elif isinstance(numeric_output, torch.Tensor):
                stress_values = numeric_output.cpu().numpy().reshape(-1)
            else:
                raise TypeError("Expected numeric_output to be a DataFrame or tensor")

            print(len(stress_values), len(strain))

            assert len(stress_values) == len(strain), "Mismatch between strain and stress values length."
            stress_update = {f"{strain[i]:.3f}": s_value for i, s_value in enumerate(stress_values)}
            df.loc[job_index, list(stress_update.keys())] = list(stress_update.values())

        df.to_csv(samples_file_path, index=False)

def get_init_data(config, mode):
    logger = logging.getLogger(__name__)

    path_to_spinodal_resources = config.path_to_spinodal_resources
    hydra_cfg = HydraConfig.get()
    hydra_output_directory = hydra_cfg['runtime']['output_dir']    
    path_to_GIBBON = config.path_to_GIBBON
    path_to_MOO = config.path_to_MOO_folder

    input_columns = config.input_columns    
    output_columns = config.output_columns

    num_samples = config.num_samples
    seed = config.seed
    batch_size = config.batch_size
    apply_transform = config.apply_transform
    apply_densification_filter = config.apply_densification_filter
    sge_jobid = config.sge_jobid
    taskid = config.hpc.taskid
    sys.path.insert(0, os.path.abspath(path_to_MOO))
    sys.path.insert(0, os.path.abspath(path_to_MOO+'/src'))

    from spinodoid_script import Spinodoid_function
    from utility import utility_functions

    samples_file_path = os.path.join(hydra_output_directory, "initial_data.csv")
    marker_file_path = os.path.join(hydra_output_directory, "master_done.marker")

    train_x = torch.zeros((len(input_columns), 1))
    train_y = torch.zeros((len(output_columns), 1))

    problem = Spinodoid_function(
        train_x=train_x, 
        train_y=train_y, 
        path_to_spinodal_resources=path_to_spinodal_resources,
        hydra_output_directory=hydra_output_directory,
        path_to_GIBBON=path_to_GIBBON,
        output_columns=output_columns,
        batch_size=batch_size,
        apply_transform=apply_transform,
        tkwargs=tkwargs,
        apply_densification_filter=apply_densification_filter
    )

    if taskid == 1 or mode == 'local':

        if not os.path.exists(samples_file_path):
            logger.info("Generating initial data.")
            
            samples = utility_functions.sample_sobol_sequence(problem, num_samples, batch_size, seed)
            samples_reshaped = samples.squeeze(1)
            
            samples_df = pd.DataFrame(samples_reshaped, columns=input_columns)
            
            if 'Stress' in output_columns:
                strain = np.linspace(0, 0.5, 201)
                stress_columns = [f"{s:.3f}" for s in strain]

                stress_df = pd.DataFrame(np.nan, index=samples_df.index, columns=stress_columns)

                samples_df = pd.concat([samples_df, stress_df], axis=1)

            output_only_columns = [col for col in output_columns if col != 'Stress']
            for col in output_only_columns:
                samples_df[col] = np.nan

            samples_df['status'] = 'pending'
            
            samples_df.to_csv(samples_file_path, index=False)
            logger.info("Initial data CSV created with all columns.")

        if taskid == 1:
            
            with open(marker_file_path, 'w') as marker_file:
                marker_file.write("Master job completed.")

            if mode == 'local':
                run_evaluation_sequential(samples_file_path, mode, problem, input_columns, output_columns, logger)

                logger.info("Initial data generation completed.")

            else:

                run_evaluation_cluster(samples_file_path, mode, problem, input_columns, output_columns, logger, taskid)

        else:
            logger.info("Initial data already exists. Skipping generation.")

    else:

        delay = random.uniform(5, 20)  
        time.sleep(delay)

        while not os.path.exists(marker_file_path):
            logger.info(f"Worker task {taskid} waiting for master job to complete...")
            time.sleep(10)  

        logger.info(f"Worker task {taskid} proceeding to evaluate inputs.")

        run_evaluation_cluster(samples_file_path, mode, problem, input_columns, output_columns, logger, taskid)

def run_evaluation_cluster(samples_file_path, mode, problem, input_columns, output_columns, logger, taskid):

    """Evaluate jobs in a cluster environment."""
    while True:
        job_index, job_data = fetch_next_job(samples_file_path)
        if job_index is None:
            logger.info("No pending jobs left, exiting.")
            break

        new_x_array = job_data[input_columns].to_numpy()
        new_x_array = new_x_array.astype(np.float64)
        new_x = torch.tensor(new_x_array).to(**tkwargs).unsqueeze(0)
        logger.info(f" Worker task {taskid} Processing job {job_index}: {new_x_array}")
        try:

            current_x, new_obj = problem.evaluate(new_x, mode=mode, batch_id=0, iteration_number=job_index)

            logger.info(f" Worker task {taskid} completed job {job_index}")

            update_job_status(samples_file_path, job_index, input_columns, current_x, output_columns, new_obj, status='completed')

        except Exception as e:
            logger.error(f"Error processing job {job_index}: {e}")

            update_job_status(samples_file_path, job_index, input_columns, current_x, output_columns, new_obj, status='error')

def run_evaluation_sequential(samples_file_path, mode, problem, input_columns, output_columns, logger):
    """Run jobs sequentially for local execution."""
    df = pd.read_csv(samples_file_path)

    for i in range(len(df)):
        if df.loc[i, 'status'] == 'pending':
            new_x_array = df.loc[i, input_columns].to_numpy()
            new_x_array = new_x_array.astype(np.float64)
            new_x = torch.tensor(new_x_array).to(**tkwargs).unsqueeze(0)

            logger.info(f"Processing job {i}: {new_x_array}")
            try:

                current_x, new_obj = problem.evaluate(new_x, mode=mode, batch_id=0, iteration_number=i)
                
                logger.info(f"Completed job {i}")

                update_job_status(samples_file_path, i, input_columns, current_x, output_columns, new_obj, status='completed')

            except Exception as e:
                logger.error(f"Error processing job {i}: {e}")

                update_job_status(samples_file_path, i, input_columns, current_x, output_columns, new_obj, status='error')