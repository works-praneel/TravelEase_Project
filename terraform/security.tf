# --- ECS Security Group Definition ---
resource "aws_security_group" "ecs_sg" {
  name        = "${var.project_name}-ecs-sg"
  description = "Security group for ECS services"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-ecs-sg"
  }
}

# --- ALB Security Group Definition ---
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
  
  # Outbound from ALB to ECS (Allow all outbound traffic)
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 1. Allow inbound HTTP traffic from the internet to the ALB
resource "aws_security_group_rule" "ingress_alb_http" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  security_group_id = aws_security_group.alb_sg.id
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTP from anywhere (for ALB)"
}

# --- ECS Ingress Rules: Allowing ALB to talk to ECS TASKS (ecs_sg rules) ---

# 2. Allow ALB to talk to the Booking Service (Port 5000)
resource "aws_security_group_rule" "ingress_booking_service" {
  type                     = "ingress"
  from_port                = 5000
  to_port                  = 5000
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ecs_sg.id
  source_security_group_id = aws_security_group.alb_sg.id 
  description              = "Allow ALB to talk to Booking service"
}

# 3. Allow ALB to talk to the Flight Service (Port 5002)
resource "aws_security_group_rule" "ingress_flight_service" {
  type                     = "ingress"
  from_port                = 5002
  to_port                  = 5002
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ecs_sg.id
  source_security_group_id = aws_security_group.alb_sg.id 
  description              = "Allow ALB to talk to Flight service"
}

# 4. Allow ALB to talk to the Payment Service (Port 5003)
resource "aws_security_group_rule" "ingress_payment_service" {
  type                     = "ingress"
  from_port                = 5003
  to_port                  = 5003
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ecs_sg.id
  source_security_group_id = aws_security_group.alb_sg.id 
  description              = "Allow ALB to talk to Payment service"
}

# 5. NAYA: Allow ALB to talk to the CrowdPulse Service (Port 5010)
resource "aws_security_group_rule" "ingress_crowdpulse_service" {
  type                     = "ingress"
  from_port                = 5010
  to_port                  = 5010
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ecs_sg.id
  source_security_group_id = aws_security_group.alb_sg.id 
  description              = "Allow ALB to talk to CrowdPulse service"
}

# 6. Allow all outbound traffic from ECS tasks (for pulling images, AWS APIs, etc.)
resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.ecs_sg.id
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}