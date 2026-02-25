# ============================================================================
# SNS Alert Topic
# ============================================================================
# All alarms in this module send to this single topic. Add subscriptions
# (email, PagerDuty, Slack via Lambda) post-apply — subscriptions require
# out-of-band confirmation so they're not managed by Terraform here.
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alerts"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Optional email subscription — only created when alert_email is provided.
resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================================================
# ECS Alarms
# ============================================================================

# High CPU — sustained load approaching container limits
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-ecs-cpu-high"
  alarm_description   = "ECS service CPU utilization is above ${var.ecs_cpu_threshold}% for 5 consecutive minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = var.ecs_cpu_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# High memory — container approaching OOM kill territory
resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  alarm_name          = "${var.project_name}-${var.environment}-ecs-memory-high"
  alarm_description   = "ECS service memory utilization is above ${var.ecs_memory_threshold}% for 5 consecutive minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = var.ecs_memory_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# No running tasks — catches crashed services, failed secret injection,
# or misconfigured task definitions silently killing containers at launch
resource "aws_cloudwatch_metric_alarm" "ecs_no_running_tasks" {
  alarm_name          = "${var.project_name}-${var.environment}-ecs-no-running-tasks"
  alarm_description   = "ECS service has zero running tasks — possible crash loop or failed secret injection"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  treat_missing_data  = "breaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================================
# ALB Alarms
# ============================================================================

# HTTP 5xx errors — application errors reaching the load balancer
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx-high"
  alarm_description   = "ALB is returning more than ${var.alb_5xx_threshold} HTTP 5xx errors per minute"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = var.alb_5xx_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# High latency — target response time degradation
resource "aws_cloudwatch_metric_alarm" "alb_high_latency" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-latency-high"
  alarm_description   = "ALB target response time is above ${var.alb_latency_threshold}s for 3 consecutive minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period             = 60
  extended_statistic = "p99"
  threshold          = var.alb_latency_threshold
  treat_missing_data = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Unhealthy host count — targets failing health checks
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-unhealthy-hosts"
  alarm_description   = "ALB has unhealthy targets — health checks failing"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================================
# RDS Alarms
# ============================================================================

# High CPU — database under heavy query load
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-cpu-high"
  alarm_description   = "RDS CPU utilization is above ${var.rds_cpu_threshold}% for 5 consecutive minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = var.rds_cpu_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.db_instance_identifier
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# High connection count — db.t3.micro has a max of ~85 connections
resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-connections-high"
  alarm_description   = "RDS connection count exceeded ${var.rds_connections_threshold} — approaching db.t3.micro limit"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = var.rds_connections_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.db_instance_identifier
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Low free storage — early warning before disk full causes write failures
resource "aws_cloudwatch_metric_alarm" "rds_low_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-low-storage"
  alarm_description   = "RDS free storage space is below 2 GiB — consider increasing allocated storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.rds_storage_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.db_instance_identifier
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================================
# CloudWatch Dashboard
# ============================================================================
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      # ── Row 1: ECS ─────────────────────────────────────────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "ECS CPU Utilization"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["AWS/ECS", "CPUUtilization",
              "ClusterName", var.ecs_cluster_name,
              "ServiceName", var.ecs_service_name,
              { label = "CPU %" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.ecs_cpu_threshold, label = "Alarm threshold", color = "#ff6961" }]
          }
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "ECS Memory Utilization"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["AWS/ECS", "MemoryUtilization",
              "ClusterName", var.ecs_cluster_name,
              "ServiceName", var.ecs_service_name,
              { label = "Memory %" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.ecs_memory_threshold, label = "Alarm threshold", color = "#ff6961" }]
          }
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "ECS Running Task Count"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["ECS/ContainerInsights", "RunningTaskCount",
              "ClusterName", var.ecs_cluster_name,
              "ServiceName", var.ecs_service_name,
              { label = "Running Tasks" }
            ]
          ]
          annotations = {
            horizontal = [{ value = 1, label = "Min healthy", color = "#ff6961" }]
          }
        }
      },
      # ── Row 2: ALB ─────────────────────────────────────────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 8
        height = 6
        properties = {
          title  = "ALB Request Count"
          view   = "timeSeries"
          stat   = "Sum"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "RequestCount",
              "LoadBalancer", var.alb_arn_suffix,
              { label = "Requests/min" }
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 6
        width  = 8
        height = 6
        properties = {
          title  = "ALB HTTP 5xx Errors"
          view   = "timeSeries"
          stat   = "Sum"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count",
              "LoadBalancer", var.alb_arn_suffix,
              "TargetGroup", var.target_group_arn_suffix,
              { label = "5xx count", color = "#ff6961" }
            ],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count",
              "LoadBalancer", var.alb_arn_suffix,
              "TargetGroup", var.target_group_arn_suffix,
              { label = "4xx count", color = "#ffb347" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.alb_5xx_threshold, label = "5xx alarm", color = "#ff6961" }]
          }
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 6
        width  = 8
        height = 6
        properties = {
          title  = "ALB Target Response Time (p99)"
          view   = "timeSeries"
          stat   = "p99"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime",
              "LoadBalancer", var.alb_arn_suffix,
              { label = "p99 latency (s)" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.alb_latency_threshold, label = "Latency alarm", color = "#ff6961" }]
          }
        }
      },
      # ── Row 3: RDS ─────────────────────────────────────────────────────────
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 8
        height = 6
        properties = {
          title  = "RDS CPU Utilization"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["AWS/RDS", "CPUUtilization",
              "DBInstanceIdentifier", var.db_instance_identifier,
              { label = "CPU %" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.rds_cpu_threshold, label = "Alarm threshold", color = "#ff6961" }]
          }
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 12
        width  = 8
        height = 6
        properties = {
          title  = "RDS Database Connections"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["AWS/RDS", "DatabaseConnections",
              "DBInstanceIdentifier", var.db_instance_identifier,
              { label = "Connections" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.rds_connections_threshold, label = "Alarm threshold", color = "#ff6961" }]
          }
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 12
        width  = 8
        height = 6
        properties = {
          title  = "RDS Free Storage Space"
          view   = "timeSeries"
          stat   = "Average"
          period = 300
          metrics = [
            ["AWS/RDS", "FreeStorageSpace",
              "DBInstanceIdentifier", var.db_instance_identifier,
              { label = "Free storage (bytes)" }
            ]
          ]
          annotations = {
            horizontal = [{ value = var.rds_storage_threshold, label = "Low storage alarm", color = "#ff6961" }]
          }
        }
      },
      # ── Row 4: Alarm status overview ───────────────────────────────────────
      {
        type   = "alarm"
        x      = 0
        y      = 18
        width  = 24
        height = 6
        properties = {
          title = "Alarm Status Overview"
          alarms = [
            aws_cloudwatch_metric_alarm.ecs_cpu_high.arn,
            aws_cloudwatch_metric_alarm.ecs_memory_high.arn,
            aws_cloudwatch_metric_alarm.ecs_no_running_tasks.arn,
            aws_cloudwatch_metric_alarm.alb_5xx_errors.arn,
            aws_cloudwatch_metric_alarm.alb_high_latency.arn,
            aws_cloudwatch_metric_alarm.alb_unhealthy_hosts.arn,
            aws_cloudwatch_metric_alarm.rds_cpu_high.arn,
            aws_cloudwatch_metric_alarm.rds_connections_high.arn,
            aws_cloudwatch_metric_alarm.rds_low_storage.arn,
          ]
        }
      }
    ]
  })
}
