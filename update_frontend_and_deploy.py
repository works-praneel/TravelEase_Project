# -- coding: utf-8 --
import re
import sys
import os
import subprocess
import json

def run_command(cmd, cwd=None):
    """Run a shell command and print output in real time."""
    print(f"\n[CMD] Running: {cmd}")
    process = subprocess.Popen(cmd, cwd=cwd, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(process.returncode)
    return process.returncode


def get_terraform_outputs(repo_dir):
    """Extract ALB DNS and frontend bucket name from Terraform outputs."""
    tf_dir = os.path.join(repo_dir, "terraform")
    print("[INFO] Reading Terraform outputs...")

    run_command("terraform output -json > tf_outputs.json", cwd=tf_dir)

    outputs_path = os.path.join(tf_dir, "tf_outputs.json")
    if not os.path.exists(outputs_path):
        print("[ERROR] Terraform outputs file not found.")
        sys.exit(1)

    with open(outputs_path, "r") as f:
        data = json.load(f)

    alb_dns = data.get("load_balancer_dns", {}).get("value", "")
    s3_bucket = data.get("frontend_bucket_name", {}).get("value", "")

    if not alb_dns or not s3_bucket:
        print("[ERROR] Missing required Terraform outputs.")
        sys.exit(1)

    print(f"[INFO] ALB DNS Detected: {alb_dns}")
    print(f"[INFO] Frontend S3 Bucket: {s3_bucket}")

    os.chdir(repo_dir)
    return alb_dns, s3_bucket


def update_urls_in_index(file_path, new_url):
    """Replace CONST ALB_URL and CONST API_ENDPOINT constants in index.html."""
    if not os.path.exists(file_path):
        print(f"[WARN] Skipping missing file: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Match uppercase constants from index.html
    content = re.sub(r'(const\s+ALB_URL\s*=\s*")[^"]+(")', fr'\1{new_url}\2', content)
    content = re.sub(r'(const\s+API_ENDPOINT\s*=\s*")[^"]+(")', fr'\1{new_url}\2', content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Updated ALB URLs in: {file_path}")
    else:
        print(f"[INFO] No ALB URL changes needed in: {file_path}")


def deploy_to_s3(bucket_name):
    """Upload frontend files to S3 (compatible with ACLs disabled)."""
    print(f"\n[DEPLOY] Uploading frontend to s3://{bucket_name}/")

    files_to_upload = {
        "index.html": "text/html",
        "CrowdPulse\\frontend\\crowdpulse_widget.html": "text/html",
        "images\\travelease_logo.png": "image/png"
    }

    for local_path, content_type in files_to_upload.items():
        if not os.path.exists(local_path):
            print(f"[WARN] File not found: {local_path}")
            continue

        s3_key = local_path.replace("\\", "/")  # normalize path for S3
        cmd = (
            f'aws s3 cp "{local_path}" "s3://{bucket_name}/{s3_key}" '
            f'--content-type {content_type}'
        )
        run_command(cmd)

    print("[SUCCESS] Frontend assets deployed successfully.")


def populate_databases(repo_dir):
    """Run DB population scripts automatically."""
    print("\n[DB] Populating Smart Trips and Flights databases...")

    scripts = [
        "populate_smart_trips_db.py",
        os.path.join("Flight_Service", "populate_flights_db.py")
    ]

    for script in scripts:
        script_path = os.path.join(repo_dir, script)
        if not os.path.exists(script_path):
            print(f"[WARN] Database script not found: {script}")
            continue

        cmd = f'"C:\\Users\\bruhn\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" "{script_path}"'
        run_command(cmd)

    print("[SUCCESS] Database population complete.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_frontend_and_deploy.py <repo_dir>")
        sys.exit(1)

    repo_dir = sys.argv[1]
    alb_dns, bucket = get_terraform_outputs(repo_dir)
    alb_url = f"http://{alb_dns}"

    print(f"[UPDATE] Updating index.html with ALB endpoint: {alb_url}")
    update_urls_in_index(os.path.join(repo_dir, "index.html"), alb_url)

    print(f"[UPLOAD] Uploading updated files to S3 bucket: {bucket}")
    deploy_to_s3(bucket)

    populate_databases(repo_dir)


if __name__ == "__main__":
    main()
