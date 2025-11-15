# -------------------------
# CrowdPulse Service
# -------------------------

resource "aws_cloudwatch_log_group" "crowdpulse_service_lg" {
  name = "/ecs/${var.project_name}/crowdpulse-service"
  tags = { Name = "${var.project_name}-crowdpulse-lg" }
}

resource "aws_ecs_task_definition" "crowdpulse_service_task" {
  family                   = "crowdpulse-service-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "crowdpulse-service"
      image     = "${aws_ecr_repository.crowdpulse_repo.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 5010
          hostPort      = 5010
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "FLASK_ENV"
          value = "production"
        },
        {
          name  = "PORT"
          value = "5010"
        },
        {
          name  = "YOUTUBE_API_KEY",
          value = var.youtube_api_key # From variables.tf
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.crowdpulse_service_lg.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:5010/api/crowdpulse/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

resource "aws_ecs_service" "crowdpulse_service" {
  name            = "crowdpulse-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.crowdpulse_service_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  health_check_grace_period_seconds = 300

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.crowdpulse_tg.arn
    container_name   = "crowdpulse-service"
    container_port   = 5010
  }

  depends_on = [aws_lb_listener.http]
}

