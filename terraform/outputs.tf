output "load_balancer_dns" {
  description = "Backend ALB DNS name"
  value       = aws_lb.alb.dns_name
}

output "frontend_bucket_name" {
  description = "Name of the S3 bucket for the frontend"
  value       = aws_s3_bucket.frontend_bucket.bucket
}

