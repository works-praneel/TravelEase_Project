# -- coding: utf-8 --
import json
import os
import re
import subprocess
import sys

def run_command(cmd, capture_output=False):
    """Run a shell command."""
    print(f"\n[CMD] {cmd}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = []
    for line in process.stdout:
        print(line, end='')
        if capture_output:
            output.append(line)
    process.wait()
    if process.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(process.returncode)
    return ''.join(output) if capture_output else None


def get_terraform_outputs(repo_dir):
    """Get ALB DNS and S3 bucket name from Terraform output JSON."""
    tf_dir = os.path.join(repo_dir, "terraform")
    os.chdir(tf_dir)
    print("[INFO] Reading Terraform outputs...")

    run_command("terraform output -json > tf_outputs.json")
    with open("tf_outputs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    alb_dns = data["load_balancer_dns"]["value"]
    s3_bucket = data["frontend_bucket_name"]["value"]
    print(f"[INFO] ALB DNS Detected: {alb_dns}")
    print(f"[INFO] Frontend S3 Bucket: {s3_bucket}")
    return alb_dns, s3_bucket


def update_urls_in_index(index_path, new_url):
    """Update ALB_URL and API_ENDPOINT constants inside index.html."""
    if not os.path.exists(index_path):
        print(f"[WARN] index.html not found: {index_path}")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    content = re.sub(r'(const\s+ALB_URL\s*=\s*")[^"]+(")', fr'\1{new_url}\2', content)
    content = re.sub(r'(const\s+API_ENDPOINT\s*=\s*")[^"]+(")', fr'\1{new_url}\2', content)

    if content != original:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Updated ALB_URL and API_ENDPOINT → {new_url}")
    else:
        print("[INFO] No changes detected in index.html")


def deploy_to_s3(bucket):
    """Upload index and assets to S3."""
    print(f"\n[DEPLOY] Uploading frontend to s3://{bucket}/")
    run_command(f'aws s3 cp index.html s3://{bucket}/index.html --content-type text/html --acl public-read')
    run_command(f'aws s3 cp CrowdPulse\\frontend\\crowdpulse_widget.html s3://{bucket}/crowdpulse_widget.html --content-type text/html --acl public-read')
    run_command(f'aws s3 cp images\\travelease_logo.png s3://{bucket}/images/travelease_logo.png --content-type image/png --acl public-read')
    print("[SUCCESS] Deployment completed successfully.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_frontend_and_deploy.py <repo_dir>")
        sys.exit(1)

    repo_dir = sys.argv[1]
    os.chdir(repo_dir)

    alb_dns, bucket = get_terraform_outputs(repo_dir)
    alb_url = f"http://{alb_dns}"

    update_urls_in_index("index.html", alb_url)
    deploy_to_s3(bucket)


if __name__ == "__main__":
    main()
