# terraform/security.tf - CORRECTED
# Note: Assuming aws_vpc.main.id and aws_security_group.alb_sg.id are defined elsewhere.

resource "aws_security_group" "ecs_sg" {
  name        = "${var.project_name}-ecs-sg"
  description = "Security group for ECS services"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-ecs-sg"
  }
}

# 1. Allow inbound HTTP traffic from the internet to the ALB (This rule seems misplaced and may belong to ALB_SG)
# For now, let's trust this is where your ALB is getting its port 80/443 rule from.
resource "aws_security_group_rule" "ingress_alb_http" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  security_group_id = aws_security_group.alb_sg.id # Assuming this is meant for ALB_SG to allow internet traffic.
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTP from anywhere (for ALB)"
}

# --- ALB Security Group Definition (Required to reference below) ---
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
  
  # Outbound from ALB to ECS is defined here:
  # This egress is important for the ALB to send requests out to the ECS services.
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- ECS Ingress Rules: Allowing ALB to talk to ECS TASKS ---

# 2. Allow ALB to talk to the Booking Service (Port 5000)
resource "aws_security_group_rule" "ingress_booking_service" {
  type                     = "ingress"
  from_port                = 5000
  to_port                  = 5000
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ecs_sg.id
  # 🟢 FIX: Source must be the ALB's Security Group ID
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
  # 🟢 FIX: Source must be the ALB's Security Group ID
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
  # 🟢 FIX: Source must be the ALB's Security Group ID
  source_security_group_id = aws_security_group.alb_sg.id 
  description              = "Allow ALB to talk to Payment service"
}

# 5. Allow all outbound traffic (for pulling images, AWS APIs, etc.)
resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.ecs_sg.id
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}