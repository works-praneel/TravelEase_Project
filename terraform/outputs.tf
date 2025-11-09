# -----------------------------
# Output: Application Load Balancer DNS
# -----------------------------
output "load_balancer_dns" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.alb.dns_name
}

# -----------------------------
# Output: Frontend S3 Bucket Name
# -----------------------------
output "frontend_bucket_name" {
  description = "Name of the S3 bucket hosting the frontend"
  value       = aws_s3_bucket.frontend_bucket.bucket
}

# -----------------------------
# Output: Frontend Website URL
# -----------------------------
output "frontend_website_url" {
  description = "Public website endpoint for the frontend"
  value       = aws_s3_bucket.frontend_bucket.website_endpoint
}
