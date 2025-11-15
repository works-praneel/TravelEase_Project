variable "aws_region" {
  description = "The AWS region to deploy infrastructure"
  default     = "eu-north-1"
}

variable "project_name" {
  description = "The name of the project"
  default     = "travelease-project"
}

variable "primary_region" {
  description = "The primary AWS region for the provider"
  default     = "eu-north-1"
}

variable "aws_profile" {
  description = "The AWS CLI profile to use"
  default     = "default"
}

# --- New Variables Added ---

variable "email_user" {
  description = "The Gmail address for sending emails (e.g., you@gmail.com)"
  type        = string
  default     = "dynoc845@gmail.com" # <-- IMPORTANT: Change this to your email
}

variable "email_pass" {
  description = "The 16-character Google App Password"
  type        = string
  sensitive   = true # This hides the value in Terraform's output
}

variable "youtube_api_key" {
  description = "The YouTube Data API v3 key"
  type        = string
  sensitive   = true
}