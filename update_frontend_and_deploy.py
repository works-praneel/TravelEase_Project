# -- coding: utf-8 --
import re
import sys
import os
import subprocess

def update_urls_in_file(file_path, new_url):
    """Replace ALB_URL and API_ENDPOINT constants with the new URL."""
    if not os.path.exists(file_path):
        print(f"[WARN] Skipping missing file: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    content = re.sub(r'(const\s+ALB_URL\s*=\s*")[^"]+(")', fr'\1{new_url}\2', content)
    content = re.sub(r'(const\s+API_ENDPOINT\s*=\s*")[^"]+(")', fr'\1{new_url}\2', content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Updated URLs in: {file_path}")
    else:
        print(f"[INFO] No URL changes needed in: {file_path}")

def run_command(cmd):
    """Run a shell command and print output in real time."""
    print(f"\n[CMD] Running: {cmd}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(process.returncode)

def deploy_to_s3(bucket_name):
    """Deploy updated frontend files to the given S3 bucket."""
    print(f"\n[DEPLOY] Uploading updated frontend files to s3://{bucket_name}/")

    # Deploy index.html
    run_command(f'aws s3 cp index.html s3://{bucket_name}/index.html --content-type text/html --acl public-read')

    # Deploy crowdpulse_widget.html
    run_command(f'aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://{bucket_name}/crowdpulse_widget.html --content-type text/html --acl public-read')

    # Deploy logo image
    run_command(f'aws s3 cp images\\travelease_logo.png s3://{bucket_name}/images/travelease_logo.png --content-type image/png --acl public-read')

    print("[SUCCESS] All frontend assets deployed successfully!")

def main():
    if len(sys.argv) != 4:
        print("Usage: python update_frontend_and_deploy.py <new_ALB_URL> <S3_BUCKET_NAME> <repo_dir>")
        sys.exit(1)

    new_url = sys.argv[1]
    bucket_name = sys.argv[2]
    repo_dir = sys.argv[3]

    os.chdir(repo_dir)

    print(f"[UPDATE] Replacing URLs with new ALB endpoint: {new_url}")
    update_urls_in_file("index.html", new_url)
    update_urls_in_file("CrowdPulse\\frontend\\crowdpulse_widget.html", new_url)

    print(f"[UPLOAD] Deploying updated files to S3 bucket: {bucket_name}")
    deploy_to_s3(bucket_name)

if __name__ == "_main_":
    main()