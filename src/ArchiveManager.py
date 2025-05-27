import os
import shutil
import subprocess
import logging


class ArchiveManager:
    """
    Class to handle the creation of compressed archives for files.
    Primarily used for creating maximum compressed RAR archives.
    """

    def __init__(self, globalvar):
        """
        Initialize the ArchiveManager with the global variables.

        Args:
            globalvar: Global variables instance containing logging and path information
        """
        self.glv = globalvar
        # Make sure we can access the entry_id property from Globalvar
        # It will be set after the database insert operation

    def create_rar_archive(self, source_file_path, vndb_id, custom_name=None):
        """
        Create a maximum compressed RAR archive of the specified file.

        Args:
            source_file_path (str): Path to the file to be archived
            vndb_id (str): The VNDB ID for directory structure
            custom_name (str, optional): Custom name for the archive. Defaults to None.

        Returns:
            str: Path to the created archive file
        """

        # Format the filename using the entry ID
        entry_id = self.glv.entry_id
        if entry_id is None or entry_id == 0:
            # If no entry ID is available, use the source filename
            if custom_name:
                base_filename = custom_name
            else:
                base_filename = os.path.basename(source_file_path)
                base_filename = os.path.splitext(base_filename)[0]  # Remove extension
        else:
            # Format as E1{ID} with ID padded to 4 digits
            base_filename = f"E1{int(entry_id):04d}"

        # Define the directories and file paths
        archive_dir = os.path.expanduser('~')  # Use home directory for archives
        archive_path = f'{archive_dir}/{base_filename}.rar'

        # Create archives directory if it doesn't exist
        # if not os.path.exists(archive_dir):
        #     os.makedirs(archive_dir)
        #     self.glv.log(f'Created archives directory: {archive_dir}')

        # Create a maximum compressed RAR archive using command line
        # -m5: Maximum compression level
        # -ep: Exclude paths from names
        cmd = ['rar', 'a', '-m3', '-ep', archive_path, source_file_path]

        try:
            # Run the RAR command
            self.glv.log(f'Attempting to create RAR archive: {archive_path}')
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.glv.log(f'Successfully created maximum compressed RAR archive: {archive_path}')
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                self.glv.log(f'Error creating RAR archive: {error_msg}')

                # Fallback to using copy if RAR fails
                self._fallback_copy(source_file_path, archive_dir, base_filename)

        except Exception as e:
            self.glv.log(f'Exception creating RAR archive: {str(e)}')
            # Fallback to using copy if RAR command fails completely
            self._fallback_copy(source_file_path, archive_dir, base_filename, True)

        return archive_path

    def _fallback_copy(self, source_file_path, archive_dir, base_filename, preserve_filename=False):
        """
        Fallback method to copy the original file when RAR creation fails.

        Args:
            source_file_path (str): Path to the original file
            archive_dir (str): Directory to store the copy
            base_filename (str): Base name for the copied file
            preserve_filename (bool): Whether to preserve the formatted filename
        """
        file_extension = os.path.splitext(source_file_path)[1]
        if preserve_filename:
            fallback_path = f'{archive_dir}/{base_filename}{file_extension}'
        else:
            fallback_path = f'{archive_dir}/{base_filename}_original{file_extension}'

        try:
            shutil.copy2(source_file_path, fallback_path)
            self.glv.log(f'Fallback: Copied original file to {fallback_path}')
        except Exception as e:
            self.glv.log(f'Failed to copy original file: {str(e)}')