terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.25"
    }
  }
}

provider "aws" {
  region = var.region
}
