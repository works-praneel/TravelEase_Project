# NAYA: CloudWatch Log Group
resource "aws_cloudwatch_log_group" "payment_service_lg" {
  name = "/ecs/${var.project_name}/payment-service"
  tags = { Name = "${var.project_name}-payment-lg" }
}

resource "aws_ecs_task_definition" "payment_service_task" {
  family                   = "payment-service-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "payment-service"
      image     = "${aws_ecr_repository.payment_repo.repository_url}:latest" # ecr.tf se
      essential = true
      
      # FIX 1: Ensure the containerPort is 5003
      portMappings = [{ containerPort = 5003, hostPort = 5003 }]
      
      environment = [
        # FIX 2: Explicitly pass the PORT environment variable to the Flask app
        { name = "PORT", value = "5003" }
      ]
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.payment_service_lg.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "payment_service" {
  name            = "payment-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.payment_service_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  # 🟢 FIX ADDED: Set grace period to 300 seconds (5 minutes) to ensure stabilization.
  health_check_grace_period_seconds = 300 

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.ecs_sg.id] # security.tf se
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.payment_tg.arn
    container_name   = "payment-service"
    # FIX 3: Ensure the load balancer container port is 5003
    container_port   = 5003
  }
  depends_on = [aws_lb_listener.http]
}