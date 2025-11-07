variable "project_name" {
  default = "travelease"
}

variable "aws_region" {
  default = "eu-north-1"
}

variable "aws_account_id" {
  default = "904233121598"
}

variable "booking_image" {
  type    = string
  default = "904233121598.dkr.ecr.eu-north-1.amazonaws.com/booking-service:latest"
}

variable "flight_image" {
  type    = string
  default = "904233121598.dkr.ecr.eu-north-1.amazonaws.com/flight-service:latest"
}

variable "payment_image" {
  type    = string
  default = "904233121598.dkr.ecr.eu-north-1.amazonaws.com/payment-service:latest"
}

# CrowdPulse ECR Image
variable "crowdpulse_image" {
  description = "ECR image URL for the CrowdPulse service"
  type        = string
}

# YouTube API Key for real-time sentiment analysis
variable "youtube_api_key" {
  description = "YouTube API key used by CrowdPulse"
  type        = string
  sensitive   = true
}

