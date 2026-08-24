output "ec2_public_ip" {
  description = "Public IP address of the Aegis Core EC2 instance"
  value       = aws_instance.aegis_core.public_ip
}