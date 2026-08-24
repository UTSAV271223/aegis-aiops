terraform {
 
  backend "s3" {
    # Use the exact bucket name from step 1
    bucket         = "aegis-aiops-state-bucket-utsav123"
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "aegis-state-locks"
    encrypt        = true
  } 
  
}
# 1. Custom Isolated VPC
resource "aws_vpc" "aegis_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 2. Internet Gateway
resource "aws_internet_gateway" "aegis_igw" {
  vpc_id = aws_vpc.aegis_vpc.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 3. Public Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.aegis_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# 4. Route Table for External Traffic
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.aegis_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.aegis_igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# 5. Associate Route Table to Subnet
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}