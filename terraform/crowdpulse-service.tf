# --------------------
# CrowdPulse Task Definition
# --------------------
resource "aws_ecs_task_definition" "crowdpulse_task" {
  family                   = "crowdpulse-task"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn # ecs-cluster.tf se
  task_role_arn            = aws_iam_role.ecs_task_role.arn           # Use task_role for potential API needs

  container_definitions = jsonencode([{
    name  = "crowdpulse"
    image = var.crowdpulse_image
    portMappings = [{
      containerPort = 5010
      hostPort      = 5010
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/travelease" # Ensure this log group exists or is defined
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "crowdpulse"
      }
    }
    environment = [
      {
        name  = "YOUTUBE_API_KEY"
        value = var.youtube_api_key
      }
    ]
  }])
}

# --------------------
# CrowdPulse ECS Service
# --------------------
resource "aws_ecs_service" "crowdpulse_service" {
  name            = "crowdpulse-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.crowdpulse_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.crowdpulse_tg.arn
    container_name   = "crowdpulse"
    container_port   = 5010
  }

  depends_on = [aws_lb_listener.http]
}
