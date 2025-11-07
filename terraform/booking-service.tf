# NAYA: CloudWatch Log Group (ECS Error ke liye)
resource "aws_cloudwatch_log_group" "booking_service_lg" {
  name = "/ecs/${var.project_name}/booking-service"
  tags = { Name = "${var.project_name}-booking-lg" }
}

resource "aws_ecs_task_definition" "booking_service_task" {
  family                   = "booking-service-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn # ecs-cluster.tf se
  task_role_arn            = aws_iam_role.ecs_task_role.arn           # ecs-cluster.tf se

  container_definitions = jsonencode([
    {
      name      = "booking-service"
      image     = "${aws_ecr_repository.booking_repo.repository_url}:latest" # ecr.tf se
      essential = true
      portMappings = [{ containerPort = 5000, hostPort = 5000 }]
      environment = [
        { name = "BOOKINGS_TABLE_NAME", value = aws_dynamodb_table.bookings_db.name }, # <-- FIX
        { name = "SEAT_TABLE_NAME", value = aws_dynamodb_table.seat_inventory_table.name }
      ]
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.booking_service_lg.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "booking_service" {
  name            = "booking-service"
  cluster         = aws_ecs_cluster.cluster.id # CORRECTED
  task_definition = aws_ecs_task_definition.booking_service_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups = [aws_security_group.ecs_sg.id] # security.tf se
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.booking_tg.arn
    container_name   = "booking-service"
    container_port   = 5000
  }
  depends_on = [aws_lb_listener.http]
}