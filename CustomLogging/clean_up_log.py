import os
import subprocess


def clean_up(path):
    # If the system was shut down and python did not have time to complete data compression and log file storage, it
    # will do it before starting a new recording
    if os.path.exists(path + '/audio_record.log'):
        data_path = path + '/Recordings'
        for folders in os.walk(data_path):
            # Look for the folder with the log file missing (it should be the last one in the list
            if not os.path.exists(folders[0] + '/audio_record.log') and folders[0] != data_path:
                # Compress .wav file(s)
                subprocess.run(['zip', '-j', '-r', '-m', '-9', folders[0] + '/data.zip', folders[0]])
                # Move the log file to the folder where data are saved
                subprocess.run(['mv', 'audio_record.log', folders[0]])
