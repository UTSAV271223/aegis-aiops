resource "aws_instance" "aegis_core" {
  ami           = "ami-0c7217cdde317cfec" # Standard Ubuntu image
  instance_type = "t3.micro"              # Updated to a free-tier eligible micro type
  
  subnet_id     = aws_subnet.public_subnet.id 
  vpc_security_group_ids = [aws_security_group.aegis_sg.id]

  tags = {
    Name = "Aegis-Command-Center"
  }
}