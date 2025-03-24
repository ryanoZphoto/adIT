import os
import sys
import subprocess
import tempfile
import shutil
import atexit

def main():
    # Set root directory to where the executable is located
    exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    os.environ['AD_SERVICE_ROOT'] = exe_dir
    
    # Create working directory next to executable if it doesn't exist
    work_dir = os.path.join(exe_dir, 'ad_service_data')
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    
    # Extract bundled files to the working directory if needed
    for dir_name in ['config', 'companies', 'ad_service', 'charts', 'logs', '.streamlit']:
        if not os.path.exists(os.path.join(work_dir, dir_name)):
            src_dir = os.path.join(exe_dir, dir_name)
            if os.path.exists(src_dir):
                shutil.copytree(src_dir, os.path.join(work_dir, dir_name))
    
    # Set current directory to working directory
    os.chdir(work_dir)
    
    # Launch the main application
    from ad_service.start_service import main as start_service_main
    start_service_main()

if __name__ == '__main__':
    main()
