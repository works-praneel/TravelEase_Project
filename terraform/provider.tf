# provider.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"
  # credentials: prefer env vars or shared credentials file.
  # If you previously used an alias named "primary" (state references .primary),
  # add alias = "primary".
  alias = "primary"
}


