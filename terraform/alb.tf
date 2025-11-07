resource "aws_lb" "alb" {
  name               = "${var.project_name}-ALB"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ecs_sg.id]
  subnets            = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
}

# --------------------
# Target Groups
# --------------------

resource "aws_lb_target_group" "booking_tg" {
  name        = "booking-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/ping" # Sahi health check
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "flight_tg" {
  name        = "flight-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/ping" # FIX 1: Health check /ping par set
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "payment_tg" {
  name        = "payment-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/ping" # FIX 2: Health check /ping par set
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
  }
}

resource "aws_lb_target_group" "crowdpulse_tg" {
  name        = "crowdpulse-tg"
  port        = 5010
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
  }
}

# --------------------
# Listener + Default Action
# --------------------

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
}

# --------------------
# Path-based Routing Rules
# --------------------

resource "aws_lb_listener_rule" "booking_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.booking_tg.arn
  }

  condition {
    path_pattern {
      values = ["/book*", "/ping"]
    }
  }
}

resource "aws_lb_listener_rule" "flight_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.flight_tg.arn
  }

  condition {
    path_pattern {
      # FIX 3: /api/flights* ko add kiya gaya hai
      values = ["/flight*", "/search*", "/api/flights*"]
    }
  }
}

resource "aws_lb_listener_rule" "payment_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 30

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.payment_tg.arn
  }

  condition {
    path_pattern {
      # FIX 4: /api/payment* ko add kiya gaya hai
      values = ["/pay*", "/payment*", "/api/payment*"]
    }
  }
}

resource "aws_lb_listener_rule" "crowdpulse_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 40

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.crowdpulse_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api/crowdpulse*", "/crowdpulse*", "/pulse*"]
    }
  }
}
