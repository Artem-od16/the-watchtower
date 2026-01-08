provider "aws" {
  region = "eu-west-3"
}

resource "aws_key_pair" "watchtower_key" {
  key_name   = "watchtower-admin-key"
  public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIR6bD4+Ir5vidiKK9hciCNnqYaINqsJctaor3An2VkT artem@Art"
}

resource "aws_security_group" "watchtower_sg" {
  name        = "watchtower-security-group-v2"
  description = "Allow HTTP, SSH and Monitoring traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH from anywhere"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Grafana UI"
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Prometheus Metrics"
  }

  ingress {
    from_port   = 9443
    to_port     = 9443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Portainer UI"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_instance" "watchtower_server" {
  ami           = "ami-078abd88811000d7e" # Current Ubuntu 22.04 AMI
  instance_type = "t3.micro"               # Instance size
  key_name      = aws_key_pair.watchtower_key.key_name

  vpc_security_group_ids = [aws_security_group.watchtower_sg.id]

  tags = {
    Name = "The-Watchtower-Server"
  }
}

output "instance_public_ip" {
  value = aws_instance.watchtower_server.public_ip
}