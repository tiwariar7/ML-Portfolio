import os
import subprocess

# Repository and project paths
repo_path = r"C:\Users\arman\Documents\ML-Portfolio"
project_path = r"C:\Users\arman\Downloads\Arman ML\ML PROJECT"

# Helper function to run git commands
def git_command(command, cwd=repo_path):
    if not os.path.isdir(cwd):
        raise NotADirectoryError(f"The directory {cwd} is invalid or does not exist.")
    print(f"Running command: {command} in directory: {cwd}")
    subprocess.run(command, shell=True, cwd=cwd, check=True)

# Verify paths
if not os.path.isdir(repo_path):
    raise NotADirectoryError(f"Repository path {repo_path} does not exist.")
if not os.path.isdir(project_path):
    raise NotADirectoryError(f"Project path {project_path} does not exist.")

# Initialize Git repository (if not already initialized)
git_command("git init")

# Walk through the project folder and add files incrementally
for root, dirs, files in os.walk(project_path):
    for file in files:
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, project_path)
        dest_path = os.path.join(repo_path, rel_path)

        # Skip files larger than 100 MB
        if os.path.getsize(file_path) < 100 * 1024 * 1024:
            # Check if the file already exists in the destination
            if not os.path.exists(dest_path):
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(file_path, dest_path)
                git_command(f"git add {rel_path}")  # Ensure files are added

# Stage all files that are untracked (if any)
git_command("git add .")

# Commit the changes
git_command('git commit -m "Added all project files"')

# Push to GitHub
git_command("git branch -M main")
git_command("git remote add origin https://github.com/tiwariar7/ML-Portfolio.git")
git_command("git push -u origin main")
