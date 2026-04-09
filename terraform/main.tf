terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}


resource "aws_security_group" "elk_sg" {
  name        = "elk-all-in-one-sg"
  description = "Security group for ELK stack on single instance"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kibana"
    from_port   = 5601
    to_port     = 5601
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Elasticsearch"
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jenkins"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Flask App"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Logstash Beats"
    from_port   = 5044
    to_port     = 5044
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "elk-sg"
  }
}


resource "aws_instance" "elk_server" {
  ami                    = "ami-0f58b397bc5c1f2e8"
  instance_type          = "t3.small"
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.elk_sg.id]

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name    = "elk-all-in-one"
    Project = "elk-anomaly-detector"
  }
}


output "server_public_ip" {
  value       = aws_instance.elk_server.public_ip
  description = "Public IP of ELK server"
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/elk-key.pem ubuntu@${aws_instance.elk_server.public_ip}"
  description = "SSH command to connect"
}

output "kibana_url" {
  value       = "http://${aws_instance.elk_server.public_ip}:5601"
  description = "Kibana dashboard URL"
}

output "jenkins_url" {
  value       = "http://${aws_instance.elk_server.public_ip}:8080"
  description = "Jenkins URL"
}
