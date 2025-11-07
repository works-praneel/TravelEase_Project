resource "aws_ecs_task_definition" "flight_task" {
  family                   = "flight-task"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
 execution_role_arn = "arn:aws:iam::904233121598:role/ecsTaskExecutionRole"


  container_definitions = jsonencode([{
    name  = "flight"
    image = var.flight_image
    portMappings = [{
      containerPort = 5002
      hostPort      = 5002
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/travelease"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "flight"
      }
    }
  }])
}

resource "aws_ecs_service" "flight_service" {
  name            = "flight-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.flight_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.flight_tg.arn
    container_name   = "flight"
    container_port   = 5002
  }

  depends_on = [aws_lb_listener.http]
}

