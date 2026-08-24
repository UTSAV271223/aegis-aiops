resource "aws_s3_bucket" "terraform_state" {
  # MUST BE UNIQUE: Change the numbers at the end if AWS says it's taken
  bucket = "aegis-aiops-state-bucket-utsav123" 
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "aegis-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
}